"""Feishu notification package."""

from __future__ import annotations

import logging

from move37.utils.feishu import FeishuClient

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

if load_dotenv is not None:
    load_dotenv()

LOGGER = logging.getLogger(__name__)

from .config import load_feishu_config
from .errors import ConfigurationError, DataParseError, FeishuAPIError, NetworkError
from .notifier import notify_feishu

__all__ = [
    "ConfigurationError",
    "DataParseError",
    "FeishuAPIError",
    "NetworkError",
    "FeishuClient",
    "load_feishu_config",
    "notify_feishu",
]
