"""RSS/Atom feed collector."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List

import feedparser
import requests
from dateutil import parser as date_parser

LOGGER = logging.getLogger(__name__)
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_entry_datetime(entry: feedparser.FeedParserDict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed_struct = entry.get(key)
        if parsed_struct:
            return datetime(
                year=parsed_struct.tm_year,
                month=parsed_struct.tm_mon,
                day=parsed_struct.tm_mday,
                hour=parsed_struct.tm_hour,
                minute=parsed_struct.tm_min,
                second=parsed_struct.tm_sec,
                tzinfo=timezone.utc,
            )

    for key in ("published", "updated"):
        raw_time = entry.get(key)
        if not raw_time:
            continue
        try:
            return _to_utc(date_parser.parse(raw_time))
        except (ValueError, TypeError):
            continue
    return None


def _build_headers(feed_url: str) -> Dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    if "youtube.com" in feed_url:
        headers["Referer"] = "https://www.youtube.com/"
    return headers


def _fetch_feed_content(feed_url: str, retries: int, timeout: int) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(feed_url, headers=_build_headers(feed_url), timeout=timeout)
            if response.status_code in RETRYABLE_HTTP_STATUS:
                raise requests.HTTPError(
                    f"Retryable HTTP status {response.status_code}",
                    response=response,
                )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(8, 0.5 * (2 ** (attempt - 1))))
                continue
            break
    raise RuntimeError(f"Failed to fetch feed: {feed_url}. last_error={last_error}") from last_error


def collect_rss(
    feed_url: str,
    start_time: datetime,
    end_time: datetime,
    source_title: str = "Unknown",
    retries: int = 3,
    timeout: int = 15,
) -> List[Dict[str, str]]:
    """Collect entries within [start_time, end_time)."""
    start_utc = _to_utc(start_time)
    end_utc = _to_utc(end_time)
    parsed = None
    primary_error: Exception | None = None

    try:
        content = _fetch_feed_content(feed_url, retries=retries, timeout=timeout)
        parsed = feedparser.parse(content)
        if parsed.bozo and not parsed.entries:
            raise RuntimeError(f"Feed parse failed: {feed_url} ({parsed.bozo_exception})")
    except Exception as exc:  # noqa: BLE001
        primary_error = exc
        LOGGER.warning("请求抓取失败，尝试超时受控兜底请求: %s", feed_url)
        try:
            fallback_content = _fetch_feed_content(feed_url, retries=1, timeout=timeout)
            parsed = feedparser.parse(fallback_content)
            if parsed.bozo and not parsed.entries:
                raise RuntimeError(f"Feed parse failed: {feed_url} ({parsed.bozo_exception})")
        except Exception as fallback_error:  # noqa: BLE001
            raise RuntimeError(
                f"Failed to fetch feed: {feed_url}. "
                f"primary_error={primary_error}; "
                f"fallback_error={fallback_error}"
            ) from fallback_error

    items: List[Dict[str, str]] = []
    for entry in parsed.entries:
        published_dt = _parse_entry_datetime(entry)
        if not published_dt:
            continue
        if not (start_utc <= published_dt < end_utc):
            continue

        link = entry.get("link")
        if not link:
            continue

        items.append(
            {
                "title": entry.get("title", link),
                "url": link,
                "published": published_dt.isoformat().replace("+00:00", "Z"),
            }
        )

    LOGGER.info("对%s(%s)parse完毕，共获取%d个有效文章。", source_title, feed_url, len(items))
    return items
