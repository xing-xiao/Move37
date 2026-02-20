"""Exception types for notify module."""

from __future__ import annotations


class ConfigurationError(ValueError):
    """Raised when required notify configuration is missing or invalid."""


class DataParseError(ValueError):
    """Raised when summary_result has invalid structure."""


class NetworkError(RuntimeError):
    """Raised when an HTTP/network operation fails."""


class FeishuAPIError(RuntimeError):
    """Raised when Feishu API returns an error response."""
