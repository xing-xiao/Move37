"""Configuration loader for content summarization."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

DEFAULT_PROMPT_TEMPLATE = """
You are an AI analyst.
Read and analyze the following URL, then return your result in Chinese.

Requirements:
1. brief: within 100 Chinese characters.
2. summary: within 1000 Chinese characters.
3. Return strict JSON only, with this shape:
{
  "brief": "brief text",
  "summary": "detailed summary text"
}

URL: {url}
""".strip()


DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 2000,
    "timeout": 60,
    "max_retries": 3,
    "youtube_transcript_langs": ["zh-Hans", "zh", "en"],
    "youtube_max_input_chars": 20000,
    "youtube_chunk_size": 4000,
    "youtube_enable_metadata_fallback": True,
    "prompt_template": DEFAULT_PROMPT_TEMPLATE,
}


PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
    },
    "gemini": {
        "base_url": None,
        "model": "gemini-2.5-flash",
    },
    "glm": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "model": "glm-4",
    },
}


class ConfigurationError(ValueError):
    """Raised when summarize configuration is invalid."""


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
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid `{field_name}` value: {value!r}. Expected float."
        ) from exc


def _to_int(value: Any, default: int, field_name: str) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Invalid `{field_name}` value: {value!r}. Expected integer."
        ) from exc


def _to_bool(value: Any, default: bool, field_name: str) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ConfigurationError(
        f"Invalid `{field_name}` value: {value!r}. Expected boolean."
    )


def _to_list(value: Any, default: list[str]) -> list[str]:
    if value is None or value == "":
        return list(default)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def load_config(
    config: Optional[Dict[str, Any]] = None,
    env_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """Load summarize config with priority: argument > .env > defaults."""

    overrides = dict(config or {})
    resolved_env_path = Path(env_path) if env_path else Path(".env")
    env_values = _read_dotenv_values(resolved_env_path)

    provider = str(
        overrides.get("provider")
        or _pick_value(env_values, "LLM_PROVIDER")
        or DEFAULT_CONFIG["provider"]
    ).strip().lower()
    if provider not in PROVIDER_CONFIGS:
        supported = ", ".join(sorted(PROVIDER_CONFIGS))
        raise ConfigurationError(f"Unsupported provider `{provider}`. Supported: {supported}")

    provider_prefix = f"LLM_{provider.upper()}_"
    provider_defaults = PROVIDER_CONFIGS[provider]

    api_key = overrides.get("api_key") or _pick_value(env_values, f"{provider_prefix}API_KEY")
    if isinstance(api_key, str):
        api_key = api_key.strip()
    if not api_key:
        raise ConfigurationError(
            f"Missing API key for provider `{provider}`. "
            f"Please set `{provider_prefix}API_KEY` in .env."
        )

    model = str(
        overrides.get("model")
        or _pick_value(env_values, f"{provider_prefix}MODEL")
        or provider_defaults.get("model")
        or DEFAULT_CONFIG["model"]
    ).strip()

    base_url = overrides.get("base_url")
    if base_url is None:
        base_url = _pick_value(env_values, f"{provider_prefix}BASE_URL")
    if not base_url:
        base_url = provider_defaults.get("base_url")
    if isinstance(base_url, str):
        base_url = base_url.strip() or None

    temperature_raw = overrides.get("temperature")
    if temperature_raw is None:
        temperature_raw = _pick_value(env_values, "LLM_TEMPERATURE")
    temperature = _to_float(
        temperature_raw, float(DEFAULT_CONFIG["temperature"]), "temperature"
    )
    if not (0 <= temperature <= 1):
        raise ConfigurationError("`temperature` must be between 0 and 1.")

    max_tokens_raw = overrides.get("max_tokens")
    if max_tokens_raw is None:
        max_tokens_raw = _pick_value(env_values, "LLM_MAX_TOKENS")
    max_tokens = _to_int(max_tokens_raw, int(DEFAULT_CONFIG["max_tokens"]), "max_tokens")
    if max_tokens <= 0:
        raise ConfigurationError("`max_tokens` must be greater than 0.")

    timeout_raw = overrides.get("timeout")
    if timeout_raw is None:
        timeout_raw = _pick_value(env_values, "LLM_TIMEOUT")
    timeout = _to_int(timeout_raw, int(DEFAULT_CONFIG["timeout"]), "timeout")
    if timeout <= 0:
        raise ConfigurationError("`timeout` must be greater than 0.")

    retries_raw = overrides.get("max_retries")
    if retries_raw is None:
        retries_raw = _pick_value(env_values, "LLM_MAX_RETRIES")
    max_retries = _to_int(retries_raw, int(DEFAULT_CONFIG["max_retries"]), "max_retries")
    if max_retries <= 0:
        raise ConfigurationError("`max_retries` must be greater than 0.")

    youtube_langs = _to_list(
        overrides.get("youtube_transcript_langs")
        or _pick_value(env_values, "YOUTUBE_TRANSCRIPT_LANGS"),
        list(DEFAULT_CONFIG["youtube_transcript_langs"]),
    )
    if not youtube_langs:
        raise ConfigurationError("`youtube_transcript_langs` must contain at least 1 language.")

    youtube_max_input_chars_raw = overrides.get("youtube_max_input_chars")
    if youtube_max_input_chars_raw is None:
        youtube_max_input_chars_raw = _pick_value(env_values, "YOUTUBE_MAX_INPUT_CHARS")
    youtube_max_input_chars = _to_int(
        youtube_max_input_chars_raw,
        int(DEFAULT_CONFIG["youtube_max_input_chars"]),
        "youtube_max_input_chars",
    )
    if youtube_max_input_chars <= 0:
        raise ConfigurationError("`youtube_max_input_chars` must be greater than 0.")

    youtube_chunk_size_raw = overrides.get("youtube_chunk_size")
    if youtube_chunk_size_raw is None:
        youtube_chunk_size_raw = _pick_value(env_values, "YOUTUBE_CHUNK_SIZE")
    youtube_chunk_size = _to_int(
        youtube_chunk_size_raw,
        int(DEFAULT_CONFIG["youtube_chunk_size"]),
        "youtube_chunk_size",
    )
    if youtube_chunk_size <= 0:
        raise ConfigurationError("`youtube_chunk_size` must be greater than 0.")

    youtube_fallback_raw = overrides.get("youtube_enable_metadata_fallback")
    if youtube_fallback_raw is None:
        youtube_fallback_raw = _pick_value(env_values, "YOUTUBE_ENABLE_METADATA_FALLBACK")
    youtube_enable_metadata_fallback = _to_bool(
        youtube_fallback_raw,
        bool(DEFAULT_CONFIG["youtube_enable_metadata_fallback"]),
        "youtube_enable_metadata_fallback",
    )

    prompt_template = str(
        overrides.get("prompt_template")
        or _pick_value(env_values, "LLM_PROMPT_TEMPLATE")
        or DEFAULT_CONFIG["prompt_template"]
    ).strip()
    if "{url}" not in prompt_template:
        raise ConfigurationError("`prompt_template` must include `{url}` placeholder.")

    return {
        "provider": provider,
        "api_key": str(api_key),
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "max_retries": max_retries,
        "youtube_transcript_langs": youtube_langs,
        "youtube_max_input_chars": youtube_max_input_chars,
        "youtube_chunk_size": youtube_chunk_size,
        "youtube_enable_metadata_fallback": youtube_enable_metadata_fallback,
        "prompt_template": prompt_template,
    }
