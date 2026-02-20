"""Lightweight URL helpers for summarize routing."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import parse_qs, urlparse


def is_youtube_url(url: str) -> bool:
    """Return whether the URL belongs to YouTube."""
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract YouTube video id from common URL patterns."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host == "youtu.be":
        video_id = parsed.path.strip("/")
        return video_id or None

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            query = parse_qs(parsed.query or "")
            video_ids = query.get("v", [])
            return video_ids[0] if video_ids else None

        match = re.match(r"^/(?:embed|shorts|live)/([^/?#]+)", parsed.path or "")
        if match:
            return match.group(1)

    return None
