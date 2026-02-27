"""All-in-one workflow entrypoint."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

if __package__ in {None, ""}:
    SRC_ROOT = Path(__file__).resolve().parents[1]
    if str(SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(SRC_ROOT))

from move37.ingest.collection import collect_all
from move37.notify.notifier import notify_feishu
from move37.summarize.summarizer import summarize_all
from move37.write_docx.writer import write_to_feishu_docx

LOGGER = logging.getLogger(__name__)


def _validate_pipeline_result(name: str, data: Dict[str, Any]) -> None:
    required = {"collection_date", "target_date", "results"}
    if not isinstance(data, dict):
        raise ValueError(f"{name} must be a dictionary.")
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{name} missing required fields: {', '.join(missing)}")
    if not isinstance(data.get("results"), list):
        raise ValueError(f"{name}.results must be a list.")


def _run_once(target_date: str | None = None, max_sources: int | None = None) -> Dict[str, Any]:
    started_at = time.time()
    steps: List[Dict[str, Any]] = []
    errors: List[str] = []

    collection_result = None
    summary_result = None

    # Step 1: collection
    step_started = time.time()
    try:
        collection_result = collect_all(target_date=target_date, max_sources=max_sources)
        _validate_pipeline_result("collection_result", collection_result)
        steps.append(
            {
                "step": "collection",
                "success": True,
                "duration_seconds": round(time.time() - step_started, 2),
            }
        )
    except Exception as exc:  # noqa: BLE001
        error = f"collection failed: {type(exc).__name__}: {exc}"
        errors.append(error)
        steps.append(
            {
                "step": "collection",
                "success": False,
                "duration_seconds": round(time.time() - step_started, 2),
                "error": error,
            }
        )
        return {
            "success": False,
            "steps": steps,
            "errors": errors,
            "duration_seconds": round(time.time() - started_at, 2),
        }

    # Step 2: summarize
    step_started = time.time()
    try:
        summary_result = summarize_all(collection_result)
        _validate_pipeline_result("summary_result", summary_result)
        steps.append(
            {
                "step": "summarize",
                "success": True,
                "duration_seconds": round(time.time() - step_started, 2),
            }
        )
    except Exception as exc:  # noqa: BLE001
        error = f"summarize failed: {type(exc).__name__}: {exc}"
        errors.append(error)
        steps.append(
            {
                "step": "summarize",
                "success": False,
                "duration_seconds": round(time.time() - step_started, 2),
                "error": error,
            }
        )
        return {
            "success": False,
            "steps": steps,
            "errors": errors,
            "duration_seconds": round(time.time() - started_at, 2),
        }

    # Step 3: notify (fail-open)
    step_started = time.time()
    notify_result = notify_feishu(summary_result)
    notify_success = bool(notify_result.get("success"))
    if not notify_success:
        errors.append(f"notify failed: {notify_result.get('message')}")
    steps.append(
        {
            "step": "notify",
            "success": notify_success,
            "duration_seconds": round(time.time() - step_started, 2),
            "message": str(notify_result.get("message") or ""),
        }
    )

    # Step 4: write docx (always run after summarize)
    step_started = time.time()
    try:
        write_result = write_to_feishu_docx(summary_result)
        steps.append(
            {
                "step": "write_docx",
                "success": bool(write_result.get("success", True)),
                "duration_seconds": round(time.time() - step_started, 2),
                "document_id": write_result.get("document_id"),
            }
        )
    except Exception as exc:  # noqa: BLE001
        error = f"write_docx failed: {type(exc).__name__}: {exc}"
        errors.append(error)
        steps.append(
            {
                "step": "write_docx",
                "success": False,
                "duration_seconds": round(time.time() - step_started, 2),
                "error": error,
            }
        )

    return {
        "success": not any(step.get("success") is False for step in steps[:2]) and len(errors) == 0,
        "steps": steps,
        "errors": errors,
        "duration_seconds": round(time.time() - started_at, 2),
    }


def _seconds_until_next(schedule_time: str) -> int:
    hour, minute = schedule_time.split(":")
    now = datetime.now()
    next_run = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return max(1, int((next_run - now).total_seconds()))


def _run_scheduled(
    schedule_time: str,
    target_date: str | None = None,
    max_sources: int | None = None,
) -> int:
    LOGGER.info("Scheduled mode started, run time=%s", schedule_time)
    try:
        while True:
            wait_seconds = _seconds_until_next(schedule_time)
            LOGGER.info("Next run in %s seconds", wait_seconds)
            time.sleep(wait_seconds)
            report = _run_once(target_date=target_date, max_sources=max_sources)
            LOGGER.info("Scheduled run finished: %s", json.dumps(report, ensure_ascii=False))
    except KeyboardInterrupt:
        LOGGER.info("Scheduled mode stopped by user.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Move37 all-in-one workflow entrypoint.")
    parser.add_argument("--direct", action="store_true", help="Run workflow once immediately.")
    parser.add_argument(
        "--schedule-time",
        type=str,
        default="05:00",
        help="Daily schedule time in HH:MM for scheduled mode (default: 05:00).",
    )
    parser.add_argument(
        "--target-date",
        type=str,
        default=None,
        help="Optional target date in YYYY-MM-DD.",
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=None,
        help="Optional max number of OPML sources to process (for debugging).",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    if args.direct:
        report = _run_once(target_date=args.target_date, max_sources=args.max_sources)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("success") else 1

    return _run_scheduled(
        schedule_time=args.schedule_time,
        target_date=args.target_date,
        max_sources=args.max_sources,
    )


if __name__ == "__main__":
    raise SystemExit(main())
