"""CLI entry point for Feishu notify demo."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.notify import notify_feishu  # noqa: E402

SAMPLE_SUMMARY_RESULT: Dict[str, Any] = {
    "collection_date": "2026-02-20",
    "target_date": "2026-02-19",
    "results": [
        {
            "source_type": "Blogs",
            "source_title": "Example Blog",
            "success": True,
            "items": [
                {
                    "title": "How Michael Abrash doubled Quake framerate",
                    "url": "https://fabiensanglard.net/quake_asm_optimizations/index.html",
                    "published": "2026-02-14T00:00:00Z",
                    "processing_time": "2.4s",
                    "model_used": "gpt-4o-mini",
                    "tokens_consumed": 845,
                    "brief": "文章回顾了 Michael Abrash 如何通过汇编优化将 Quake 帧率提升一倍。",
                    "summary": "本文详细分析了 Quake 渲染路径中的关键瓶颈与优化技巧。",
                    "success": True,
                    "error": None,
                }
            ],
        },
        {
            "source_type": "YouTube Channels",
            "source_title": "Example Channel",
            "success": True,
            "items": [
                {
                    "title": "Example Failed Video",
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "published": "2026-02-19T12:00:00Z",
                    "processing_time": "0.8s",
                    "model_used": "gemini-2.5-flash",
                    "tokens_consumed": 0,
                    "brief": "",
                    "summary": "",
                    "success": False,
                    "error": "LLM response parsing failed",
                }
            ],
        },
    ],
}


def _mock_send_group_notify(**_: Any) -> Dict[str, Any]:
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "message_id": "om_mock_message_id",
        },
    }


def _build_override_config(args: argparse.Namespace) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    if args.app_id:
        config["app_id"] = args.app_id
    if args.app_secret:
        config["app_secret"] = args.app_secret
    if args.chat_receive_id:
        config["chat_receive_id"] = args.chat_receive_id
    if args.chat_receive_id_type:
        config["chat_receive_id_type"] = args.chat_receive_id_type
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run notify_feishu with sample payload.")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real Feishu API requests. Default is mock mode.",
    )
    parser.add_argument("--app-id", type=str, default=None, help="Override FEISHU_APP_ID")
    parser.add_argument(
        "--app-secret",
        type=str,
        default=None,
        help="Override FEISHU_APP_SECRET",
    )
    parser.add_argument(
        "--chat-receive-id",
        type=str,
        default=None,
        help="Override FEISHU_CHAT_RECEIVE_ID",
    )
    parser.add_argument(
        "--chat-receive-id-type",
        type=str,
        default="chat_id",
        help="Override FEISHU_CHAT_RECEIVE_ID_TYPE (default: chat_id)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    sample_payload = copy.deepcopy(SAMPLE_SUMMARY_RESULT)
    override_config = _build_override_config(args)
    config: Dict[str, Any] | None = override_config or None

    if args.real:
        result = notify_feishu(sample_payload, config=config)
    else:
        mock_config = {
            "app_id": "cli_mock_app_id",
            "app_secret": "cli_mock_app_secret",
            "chat_receive_id": "oc_mock_chat_id",
            "chat_receive_id_type": "chat_id",
        }
        mock_config.update(override_config)
        with patch(
            "move37.notify.notifier.FeishuClient.send_group_notify",
            side_effect=_mock_send_group_notify,
        ):
            result = notify_feishu(sample_payload, config=mock_config)

    print(f"success: {result.get('success')}")
    print(f"message: {result.get('message')}")
    print("statistics:")
    print(json.dumps(result.get("statistics", {}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
