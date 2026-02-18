"""Collect YouTube videos by channel and date range."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import urlparse

import requests

from move37.utils.rss.rss_collector import DEFAULT_HEADERS
from move37.utils.rss.rss_collector import collect_rss

LOGGER = logging.getLogger(__name__)
CHANNEL_ID_RE = re.compile(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"')


def _channel_url_to_feed_url(channel_url: str, timeout: int = 15) -> str:
    if "feeds/videos.xml" in channel_url:
        return channel_url

    parsed = urlparse(channel_url)
    if "youtube.com" not in parsed.netloc:
        return channel_url

    channel_match = re.search(r"/channel/([a-zA-Z0-9_-]+)", parsed.path)
    if channel_match:
        channel_id = channel_match.group(1)
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    # For handle/user style URLs, fetch page and extract channelId.
    response = requests.get(channel_url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    match = CHANNEL_ID_RE.search(response.text)
    if not match:
        raise RuntimeError(f"Cannot resolve YouTube channel id from URL: {channel_url}")
    channel_id = match.group(1)
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def collect_youtube(
    channel_url: str,
    start_time: datetime,
    end_time: datetime,
    source_title: str = "Unknown",
    retries: int = 3,
    timeout: int = 15,
):
    feed_url = _channel_url_to_feed_url(channel_url, timeout=timeout)
    items = collect_rss(
        feed_url=feed_url,
        start_time=start_time,
        end_time=end_time,
        source_title=source_title,
        retries=retries,
        timeout=timeout,
    )
    LOGGER.info("对%s(%s)parse完毕，共获取%d个有效视频。", source_title, channel_url, len(items))
    return items
