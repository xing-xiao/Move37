"""Data ingest coordinator."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from move37.utils.date_utils import get_date_range, get_yesterday_range
from move37.utils.opml.opml_parser import parse_opml
from move37.utils.rss.rss_collector import collect_rss
from move37.utils.youtube.youtube_collector import collect_youtube

LOGGER = logging.getLogger(__name__)
DEFAULT_OPML_PATH = Path(__file__).resolve().parents[1] / "sources" / "rss.opml"


def _normalize_source_type(source_type: str) -> str:
    key = source_type.strip().lower().replace("_", " ")
    if key in {"blogs", "blog", "rss"}:
        return "Blogs"
    if key in {
        "youtube channels",
        "youtube channel",
        "youtube",
        "youtubechannels",
        "yt",
    }:
        return "YouTube Channels"
    return source_type


def format_results(results: List[Dict], target_date: str) -> Dict:
    """Format output payload and drop empty source items."""
    filtered = [item for item in results if item.get("items")]
    return {
        "collection_date": datetime.now(timezone.utc).date().isoformat(),
        "target_date": target_date,
        "results": filtered,
    }


def collect_all(
    target_date: str | None = None,
    opml_path: str | Path | None = None,
    max_sources: int | None = None,
) -> Dict:
    """Collect data for blogs and YouTube channels from OPML sources."""
    if target_date:
        start_time, end_time = get_date_range(target_date)
        normalized_target_date = target_date
    else:
        start_time, end_time = get_yesterday_range()
        normalized_target_date = start_time.date().isoformat()

    sources = parse_opml(opml_path or DEFAULT_OPML_PATH)
    collected_results: List[Dict] = []

    if max_sources is not None:
        if max_sources <= 0:
            raise ValueError("`max_sources` must be a positive integer.")
        sources = sources[:max_sources]
        LOGGER.info("启用 max_sources=%d，本次仅处理前 %d 个 source。", max_sources, len(sources))
    total_sources = len(sources)

    for index, source in enumerate(sources, start=1):
        source_type = _normalize_source_type(source.get("sourceType", "Unknown"))
        source_title = source.get("xmlTitle", "Unknown")
        source_url = source.get("xmlUrl", "")
        source_started = datetime.now(timezone.utc)

        LOGGER.info(
            "开始采集 source %d/%d: title=%s, type=%s, url=%s",
            index,
            total_sources,
            source_title,
            source_type,
            source_url,
        )

        result = {
            "source_type": source_type,
            "source_title": source_title,
            "success": True,
            "items": [],
        }

        try:
            if source_type == "Blogs":
                result["items"] = collect_rss(
                    feed_url=source_url,
                    start_time=start_time,
                    end_time=end_time,
                    source_title=source_title,
                )
            elif source_type == "YouTube Channels":
                result["items"] = collect_youtube(
                    channel_url=source_url,
                    start_time=start_time,
                    end_time=end_time,
                    source_title=source_title,
                )
            else:
                result["success"] = False
                result["error"] = f"Unsupported source type: {source_type}"
                LOGGER.info("跳过不支持的sourceType: %s (%s)", source_type, source_title)
        except Exception as exc:  # noqa: BLE001
            result["success"] = False
            result["error"] = str(exc)
            LOGGER.error("采集失败: %s (%s): %s", source_title, source_url, exc)
        finally:
            duration_seconds = (datetime.now(timezone.utc) - source_started).total_seconds()
            LOGGER.info(
                "结束采集 source %d/%d: title=%s, success=%s, items=%d, duration=%.2fs",
                index,
                total_sources,
                source_title,
                result.get("success", False),
                len(result.get("items", [])),
                duration_seconds,
            )

        collected_results.append(result)

    return format_results(collected_results, target_date=normalized_target_date)
