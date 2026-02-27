"""Main Feishu notification orchestration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from move37.utils.feishu import FeishuClient
from move37.utils.feishu import FeishuClientError, FeishuMessageError

from .config import load_feishu_config
from .errors import ConfigurationError, DataParseError
from .message_builder import build_message
from .statistics import calculate_statistics

LOGGER = logging.getLogger(__name__)


def _empty_statistics() -> Dict[str, Any]:
    return {
        "total_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "total_time_minutes": 0,
        "total_time_seconds": 0,
        "total_tokens": 0,
        "total_time_raw_seconds": 0.0,
    }


def notify_feishu(
    summary_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Send summarize result notification to Feishu chat.

    Returns a dictionary with:
    - success: bool
    - message: str
    - statistics: Dict[str, Any]
    - response: Optional[Dict[str, Any]]
    """
    statistics: Dict[str, Any] = _empty_statistics()

    try:
        loaded_config = load_feishu_config(config=config)
    except ConfigurationError as exc:
        LOGGER.error("Failed to load Feishu config: %s", exc)
        return {
            "success": False,
            "message": f"Configuration error: {exc}",
            "statistics": statistics,
            "response": None,
        }

    try:
        statistics = calculate_statistics(summary_result)
        message = build_message(summary_result, statistics)
    except DataParseError as exc:
        LOGGER.error("Failed to parse summary_result for notify: %s", exc)
        return {
            "success": False,
            "message": f"Data parse error: {exc}",
            "statistics": statistics,
            "response": None,
        }
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Unexpected data processing error in notify_feishu")
        return {
            "success": False,
            "message": f"Unexpected data processing error: {type(exc).__name__}: {exc}",
            "statistics": statistics,
            "response": None,
        }

    client = FeishuClient(
        app_id=loaded_config["app_id"],
        app_secret=loaded_config["app_secret"],
        timeout=loaded_config["timeout"],
        base_url=loaded_config["base_url"],
    )
    try:
        response_payload = client.send_group_notify(
            content=message,
            receive_id=loaded_config["chat_receive_id"],
            msg_type="text",
            receive_id_type=loaded_config["chat_receive_id_type"],
        )
        data = response_payload.get("data")
        message_id = ""
        if isinstance(data, dict):
            message_id = str(data.get("message_id") or "").strip()
        success_message = "Feishu message sent successfully."
        if message_id:
            success_message = f"Feishu message sent successfully. message_id={message_id}"
        send_result: Dict[str, Any] = {
            "success": True,
            "message": success_message,
            "response": response_payload,
        }
    except (FeishuClientError, FeishuMessageError, ValueError) as exc:
        send_result = {
            "success": False,
            "message": str(exc),
            "response": None,
        }

    return {
        "success": bool(send_result.get("success")),
        "message": str(send_result.get("message") or ""),
        "statistics": statistics,
        "response": send_result.get("response"),
    }
