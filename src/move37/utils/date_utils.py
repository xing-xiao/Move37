"""Date helper functions for ingest flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date(date_str: str) -> datetime:
    """Parse YYYY-MM-DD into a UTC datetime at 00:00:00."""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Invalid date '{date_str}', expected YYYY-MM-DD.") from exc
    return parsed.replace(tzinfo=timezone.utc)


def get_date_range(date_str: str) -> Tuple[datetime, datetime]:
    """Return [start, end) UTC range for the specified day."""
    start = parse_date(date_str)
    end = start + timedelta(days=1)
    return start, end


def get_yesterday_range(reference_time: datetime | None = None) -> Tuple[datetime, datetime]:
    """Return [start, end) UTC range for yesterday."""
    now_utc = _ensure_utc(reference_time) if reference_time else datetime.now(timezone.utc)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    return yesterday_start, today_start

