"""Configuration loader for write-feishu-docx."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import ConfigurationError

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "base_url": "https://open.feishu.cn",
    "timeout": 30.0,
    "max_retries": 3,
}


def _read_dotenv_values(env_path: Path) -> Dict[str, str]:
    if not env_path.exists():
        LOGGER.warning(".env file not found at %s", env_path)
        return {}

    try:
        from dotenv import dotenv_values
    except ImportError as exc:  # pragma: no cover
        raise ConfigurationError(
            "python-dotenv is required. Install with `pip install python-dotenv`."
        ) from exc

    values = dotenv_values(env_path)
    return {
        str(key): str(value).strip()
        for key, value in values.items()
        if key and value is not None and str(value).strip() != ""
    }


def _pick_value(values: Dict[str, str], *keys: str) -> Optional[str]:
    for key in keys:
        value = values.get(key)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def _to_float(value: Any, default: float, field_name: str) -> float:
    if value is None or value == "":
        return default
    try:
        resolved = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid `{field_name}` value: {value!r}. Expected float."
        ) from exc

    if resolved <= 0:
        raise ConfigurationError(f"`{field_name}` must be greater than 0.")
    return resolved


def _to_int(value: Any, default: int, field_name: str) -> int:
    if value is None or value == "":
        return default
    try:
        resolved = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid `{field_name}` value: {value!r}. Expected integer."
        ) from exc

    if resolved <= 0:
        raise ConfigurationError(f"`{field_name}` must be greater than 0.")
    return resolved


def load_write_docx_config(
    config: Optional[Dict[str, Any]] = None,
    env_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load write_docx config with priority: argument > .env > defaults."""

    overrides = dict(config or {})
    resolved_env_path = Path(env_path) if env_path else Path(".env")
    env_values = _read_dotenv_values(resolved_env_path)

    app_id = str(
        overrides.get("app_id")
        or overrides.get("FEISHU_APP_ID")
        or _pick_value(env_values, "FEISHU_APP_ID")
        or ""
    ).strip()
    app_secret = str(
        overrides.get("app_secret")
        or overrides.get("FEISHU_APP_SECRET")
        or _pick_value(env_values, "FEISHU_APP_SECRET")
        or ""
    ).strip()
    wiki_space_id = str(
        overrides.get("wiki_space_id")
        or overrides.get("space_id")
        or overrides.get("FEISHU_WIKI_SPACE_ID")
        or _pick_value(env_values, "FEISHU_WIKI_SPACE_ID")
        or ""
    ).strip()
    wiki_parent_node_token = str(
        overrides.get("wiki_parent_node_token")
        or overrides.get("parent_node_token")
        or overrides.get("FEISHU_WIKI_PARENT_NODE_TOKEN")
        or _pick_value(env_values, "FEISHU_WIKI_PARENT_NODE_TOKEN")
        or ""
    ).strip()

    missing_fields = []
    if not app_id:
        missing_fields.append("FEISHU_APP_ID")
    if not app_secret:
        missing_fields.append("FEISHU_APP_SECRET")
    if not wiki_space_id:
        missing_fields.append("FEISHU_WIKI_SPACE_ID")
    if not wiki_parent_node_token:
        missing_fields.append("FEISHU_WIKI_PARENT_NODE_TOKEN")
    if missing_fields:
        raise ConfigurationError(
            f"Missing required write_docx configuration: {', '.join(missing_fields)}. "
            "Please set values in `.env` or pass `config`."
        )

    timeout_raw = (
        overrides.get("timeout")
        or overrides.get("FEISHU_TIMEOUT")
        or _pick_value(env_values, "FEISHU_TIMEOUT")
    )
    timeout = _to_float(timeout_raw, float(DEFAULT_CONFIG["timeout"]), "timeout")

    retries_raw = (
        overrides.get("max_retries")
        or overrides.get("FEISHU_MAX_RETRIES")
        or _pick_value(env_values, "FEISHU_MAX_RETRIES")
    )
    max_retries = _to_int(retries_raw, int(DEFAULT_CONFIG["max_retries"]), "max_retries")

    base_url = str(
        overrides.get("base_url")
        or overrides.get("FEISHU_BASE_URL")
        or _pick_value(env_values, "FEISHU_BASE_URL")
        or DEFAULT_CONFIG["base_url"]
    ).strip()
    if not base_url:
        base_url = str(DEFAULT_CONFIG["base_url"])
    base_url = base_url.rstrip("/")

    llm_config = overrides.get("llm_config")

    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "wiki_space_id": wiki_space_id,
        "wiki_parent_node_token": wiki_parent_node_token,
        "timeout": timeout,
        "max_retries": max_retries,
        "base_url": base_url,
        "llm_config": llm_config,
    }
