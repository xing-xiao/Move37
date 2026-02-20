"""Fetch source content before passing to LLM."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import requests

LOGGER = logging.getLogger(__name__)

YOUTUBE_OEMBED_URL = "https://www.youtube.com/oembed"


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


def fetch_youtube_summary_input(
    url: str,
    title: str = "",
    published: str = "",
    preferred_languages: Optional[List[str]] = None,
    max_input_chars: int = 20000,
    enable_metadata_fallback: bool = True,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Fetch transcript first, then fallback to metadata if enabled."""
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError(f"Invalid YouTube URL, failed to extract video id: {url}")

    langs = preferred_languages or ["zh-Hans", "zh", "en"]
    transcript_error = ""

    try:
        transcript_text, transcript_lang = _fetch_youtube_transcript(video_id, langs)
        content = _build_transcript_content(
            url=url,
            video_id=video_id,
            title=title,
            published=published,
            transcript_text=transcript_text[:max_input_chars],
            transcript_lang=transcript_lang,
        )
        return {
            "basis": "transcript",
            "content": content,
            "video_id": video_id,
            "warning": None,
        }
    except Exception as exc:  # noqa: BLE001
        transcript_error = f"{type(exc).__name__}: {exc}"
        LOGGER.warning("YouTube transcript unavailable for %s: %s", url, transcript_error)

    if not enable_metadata_fallback:
        raise RuntimeError(
            f"Failed to fetch transcript for {url}, metadata fallback is disabled. "
            f"error={transcript_error}"
        )

    metadata = _fetch_youtube_metadata(url=url, timeout=timeout)
    content = _build_metadata_content(
        url=url,
        video_id=video_id,
        title=title,
        published=published,
        metadata=metadata,
    )
    return {
        "basis": "metadata",
        "content": content[:max_input_chars],
        "video_id": video_id,
        "warning": (
            "Transcript unavailable; summary is generated from metadata only. "
            f"transcript_error={transcript_error}"
        ),
    }


def _fetch_youtube_transcript(video_id: str, languages: List[str]) -> tuple[str, str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "youtube-transcript-api is required. Install with "
            "`pip install youtube-transcript-api`."
        ) from exc

    raw_items: List[Any] = []
    transcript_lang = ""

    if hasattr(YouTubeTranscriptApi, "fetch"):
        fetched = None
        try:
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id, languages=languages)
        except Exception:  # noqa: BLE001
            # Compatibility fallback for versions where fetch is a class/static method.
            fetched = YouTubeTranscriptApi.fetch(video_id, languages=languages)

        transcript_lang = str(getattr(fetched, "language_code", "") or "")
        snippets = getattr(fetched, "snippets", None)
        if snippets is not None:
            raw_items = list(snippets)
        elif isinstance(fetched, list):
            raw_items = fetched
        else:
            raw_items = list(fetched)
    elif hasattr(YouTubeTranscriptApi, "get_transcript"):
        raw_items = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    else:
        raise RuntimeError("Unsupported youtube-transcript-api version.")

    texts: List[str] = []
    for item in raw_items:
        if isinstance(item, dict):
            text = str(item.get("text", "")).strip()
        else:
            text = str(getattr(item, "text", "")).strip()
        if text:
            texts.append(text)

    merged = " ".join(texts).strip()
    if not merged:
        raise ValueError("Transcript is empty.")

    return merged, transcript_lang


def _fetch_youtube_metadata(url: str, timeout: int = 30) -> Dict[str, Any]:
    try:
        response = requests.get(
            YOUTUBE_OEMBED_URL,
            params={"url": url, "format": "json"},
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Failed to fetch oEmbed metadata for %s: %s", url, exc)
        return {}


def _build_transcript_content(
    url: str,
    video_id: str,
    title: str,
    published: str,
    transcript_text: str,
    transcript_lang: str,
) -> str:
    lines = [
        "以下是 YouTube 视频信息与字幕内容。请只基于这些内容生成总结：",
        f"URL: {url}",
        f"Video ID: {video_id}",
    ]
    if title:
        lines.append(f"标题: {title}")
    if published:
        lines.append(f"发布时间: {published}")
    if transcript_lang:
        lines.append(f"字幕语言: {transcript_lang}")

    lines.extend(
        [
            "",
            "[字幕内容开始]",
            transcript_text,
            "[字幕内容结束]",
        ]
    )
    return "\n".join(lines).strip()


def _build_metadata_content(
    url: str,
    video_id: str,
    title: str,
    published: str,
    metadata: Dict[str, Any],
) -> str:
    lines = [
        "以下是 YouTube 视频的元数据（无字幕可用）。请基于这些信息生成总结，并在内容中说明信息有限：",
        f"URL: {url}",
        f"Video ID: {video_id}",
    ]
    if title:
        lines.append(f"采集标题: {title}")
    if published:
        lines.append(f"发布时间: {published}")

    oembed_title = str(metadata.get("title", "")).strip()
    author_name = str(metadata.get("author_name", "")).strip()
    provider_name = str(metadata.get("provider_name", "")).strip()

    if oembed_title:
        lines.append(f"oEmbed 标题: {oembed_title}")
    if author_name:
        lines.append(f"作者: {author_name}")
    if provider_name:
        lines.append(f"平台: {provider_name}")

    if not any([oembed_title, author_name, provider_name, title, published]):
        lines.append("可用元数据非常有限。")

    return "\n".join(lines).strip()
