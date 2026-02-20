"""Feishu wiki document writing package."""

from __future__ import annotations

import logging

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

if load_dotenv is not None:
    load_dotenv()

LOGGER = logging.getLogger(__name__)

from .config import load_write_docx_config
from .errors import (
    ConfigurationError,
    ContentExtractionError,
    DocumentOperationError,
    FeishuAPIError,
    LLMError,
    NetworkError,
)
from .writer import write_to_feishu_docx

__all__ = [
    "ConfigurationError",
    "ContentExtractionError",
    "DocumentOperationError",
    "FeishuAPIError",
    "LLMError",
    "NetworkError",
    "load_write_docx_config",
    "write_to_feishu_docx",
]
