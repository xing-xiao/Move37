"""Statistics calculator for summarize results."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict

from .errors import DataParseError

LOGGER = logging.getLogger(__name__)
_TIME_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


def _parse_processing_seconds(value: Any) -> float:
    if value is None:
        return 0.0

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, float(value))

    if not isinstance(value, str):
        return 0.0

    text = value.strip().lower()
    if not text:
        return 0.0

    if text.endswith("s"):
        text = text[:-1].strip()
    try:
        return max(0.0, float(text))
    except ValueError:
        matched = _TIME_PATTERN.search(text)
        if matched:
            try:
                return max(0.0, float(matched.group(1)))
            except ValueError:
                return 0.0
    return 0.0


def _parse_tokens(value: Any) -> int:
    if value is None:
        return 0

    if isinstance(value, bool):
        return 0

    try:
        parsed = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def calculate_statistics(summary_result: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate total items, status counts, elapsed time and token usage."""
    if not isinstance(summary_result, dict):
        raise DataParseError("`summary_result` must be a dictionary.")

    results = summary_result.get("results")
    if results is None:
        results = []
    if not isinstance(results, list):
        raise DataParseError("`summary_result.results` must be a list.")

    total_count = 0
    success_count = 0
    failure_count = 0
    total_seconds = 0.0
    total_tokens = 0

    for source in results:
        if not isinstance(source, dict):
            LOGGER.warning("Skip invalid source entry in statistics: %r", source)
            continue

        items = source.get("items", [])
        if not isinstance(items, list):
            LOGGER.warning(
                "Skip source with invalid items in statistics: source_title=%s",
                source.get("source_title"),
            )
            continue

        for item in items:
            if not isinstance(item, dict):
                LOGGER.warning("Skip invalid item entry in statistics: %r", item)
                continue

            total_count += 1
            if bool(item.get("success")):
                success_count += 1
            else:
                failure_count += 1

            total_seconds += _parse_processing_seconds(item.get("processing_time"))
            total_tokens += _parse_tokens(item.get("tokens_consumed"))

    whole_seconds = int(total_seconds)
    total_time_minutes = whole_seconds // 60
    total_time_seconds = whole_seconds % 60

    return {
        "total_count": total_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "total_time_minutes": total_time_minutes,
        "total_time_seconds": total_time_seconds,
        "total_tokens": total_tokens,
        "total_time_raw_seconds": round(total_seconds, 2),
    }
