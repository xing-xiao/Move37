"""Exception types for write_docx module."""

from __future__ import annotations


class ConfigurationError(ValueError):
    """Raised when required write_docx configuration is missing or invalid."""


class FeishuAPIError(RuntimeError):
    """Raised when Feishu API returns an error response."""


class NetworkError(RuntimeError):
    """Raised when HTTP/network operations fail."""


class ContentExtractionError(RuntimeError):
    """Raised when extracting article content fails."""


class LLMError(RuntimeError):
    """Raised when LLM translation/generation fails."""


class DocumentOperationError(RuntimeError):
    """Raised when creating or writing documents fails."""
