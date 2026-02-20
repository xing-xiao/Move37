"""Content summarization package."""

from __future__ import annotations

import logging

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

if load_dotenv is not None:
    load_dotenv()

LOGGER = logging.getLogger(__name__)

from .config import ConfigurationError, load_config
from .content_fetcher import extract_youtube_video_id, is_youtube_url
from .summarizer import summarize_all, summarize_single_url

__all__ = [
    "ConfigurationError",
    "extract_youtube_video_id",
    "is_youtube_url",
    "load_config",
    "summarize_all",
    "summarize_single_url",
]
