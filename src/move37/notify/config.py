"""Configuration loader for Feishu notification."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .errors import ConfigurationError

LOGGER = logging.getLogger(__name__)

DEFAULT_FEISHU_CONFIG: Dict[str, Any] = {
    "chat_receive_id_type": "chat_id",
    "timeout": 30.0,
    "base_url": "https://open.feishu.cn",
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


def load_feishu_config(
    config: Optional[Dict[str, Any]] = None,
    env_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load Feishu config with priority: argument > .env > defaults."""

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
    chat_receive_id = str(
        overrides.get("chat_receive_id")
        or overrides.get("FEISHU_CHAT_RECEIVE_ID")
        or _pick_value(env_values, "FEISHU_CHAT_RECEIVE_ID")
        or ""
    ).strip()

    missing_fields = []
    if not app_id:
        missing_fields.append("FEISHU_APP_ID")
    if not app_secret:
        missing_fields.append("FEISHU_APP_SECRET")
    if not chat_receive_id:
        missing_fields.append("FEISHU_CHAT_RECEIVE_ID")
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ConfigurationError(
            f"Missing required Feishu configuration: {missing}. "
            "Please set values in `.env` or pass `config`."
        )

    chat_receive_id_type = str(
        overrides.get("chat_receive_id_type")
        or overrides.get("FEISHU_CHAT_RECEIVE_ID_TYPE")
        or _pick_value(env_values, "FEISHU_CHAT_RECEIVE_ID_TYPE")
        or DEFAULT_FEISHU_CONFIG["chat_receive_id_type"]
    ).strip()
    if not chat_receive_id_type:
        chat_receive_id_type = str(DEFAULT_FEISHU_CONFIG["chat_receive_id_type"])

    timeout_raw = overrides.get("timeout")
    if timeout_raw is None or timeout_raw == "":
        timeout_raw = overrides.get("FEISHU_TIMEOUT")
    if timeout_raw is None or timeout_raw == "":
        timeout_raw = _pick_value(env_values, "FEISHU_TIMEOUT")
    timeout = _to_float(timeout_raw, float(DEFAULT_FEISHU_CONFIG["timeout"]), "timeout")

    base_url = str(
        overrides.get("base_url")
        or overrides.get("FEISHU_BASE_URL")
        or _pick_value(env_values, "FEISHU_BASE_URL")
        or DEFAULT_FEISHU_CONFIG["base_url"]
    ).strip()
    if not base_url:
        base_url = str(DEFAULT_FEISHU_CONFIG["base_url"])
    base_url = base_url.rstrip("/")

    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "chat_receive_id": chat_receive_id,
        "chat_receive_id_type": chat_receive_id_type,
        "timeout": timeout,
        "base_url": base_url,
    }
