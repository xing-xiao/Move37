"""CLI entry point for write-feishu-docx demo."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.write_docx import write_to_feishu_docx  # noqa: E402

SAMPLE_SUMMARY_RESULT: Dict[str, Any] = {
    "collection_date": "2026-02-20",
    "target_date": "2026-02-19",
    "results": [
        {
            "source_type": "Blogs",
            "source_title": "fabiensanglard.net",
            "success": True,
            "items": [
                {
                    "title": "How Michael Abrash doubled Quake framerate",
                    "url": "https://fabiensanglard.net/quake_asm_optimizations/index.html",
                    "published": "2026-02-19T00:00:00Z",
                    "processing_time": "2.4s",
                    "model_used": "gpt-4o-mini",
                    "tokens_consumed": 845,
                    "brief": "文章回顾了 Quake 的汇编优化思路。",
                    "summary": "本文分析了渲染路径中的关键瓶颈与优化技巧。",
                    "success": True,
                    "error": None,
                }
            ],
        }
    ],
}


class _MockResponse:
    def __init__(self, payload: Dict[str, Any], status_code: int = 200, text: str = "") -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


_doc_counter = 0


def _mock_requests_post(url: str, json: Dict[str, Any] | None = None, **_: Any) -> _MockResponse:
    global _doc_counter
    if url.endswith("/open-apis/auth/v3/tenant_access_token/internal"):
        return _MockResponse({"code": 0, "msg": "ok", "tenant_access_token": "t-mock-token"})

    if "/open-apis/wiki/v2/spaces/" in url and url.endswith("/nodes"):
        _doc_counter += 1
        return _MockResponse(
            {
                "code": 0,
                "msg": "ok",
                "data": {
                    "node_token": f"wikcn_mock_{_doc_counter}",
                    "title": (json or {}).get("title", ""),
                },
            }
        )

    if "/open-apis/docx/v1/documents/" in url and "/children" in url:
        return _MockResponse({"code": 0, "msg": "ok", "data": {"children": []}})

    return _MockResponse({"code": 404, "msg": "not found"}, status_code=404)


def _mock_requests_get(url: str, **_: Any) -> _MockResponse:
    if "fabiensanglard.net" in url:
        html = """
        <html><body><article>
        <h1>Quake optimization</h1>
        <p>Michael Abrash explained how profile-first optimization works.</p>
        <p>Assembly optimization removed expensive inner-loop costs.</p>
        </article></body></html>
        """
        return _MockResponse({}, status_code=200, text=html)
    return _MockResponse({}, status_code=404, text="")


def _build_override_config(args: argparse.Namespace) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "app_id": args.app_id,
        "app_secret": args.app_secret,
        "wiki_space_id": args.space_id,
        "wiki_parent_node_token": args.parent_node_token,
    }
    if args.disable_llm:
        config["disable_blog_llm"] = True
    return config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run write_to_feishu_docx with sample payload.")
    parser.add_argument("--real", action="store_true", help="Use real requests instead of mocks.")
    parser.add_argument("--app-id", default="cli_mock_app_id", help="FEISHU_APP_ID")
    parser.add_argument("--app-secret", default="cli_mock_app_secret", help="FEISHU_APP_SECRET")
    parser.add_argument("--space-id", default="7600000000000000000", help="FEISHU_WIKI_SPACE_ID")
    parser.add_argument(
        "--parent-node-token",
        default="wikcn_parent_mock",
        help="FEISHU_WIKI_PARENT_NODE_TOKEN",
    )
    parser.add_argument(
        "--disable-llm",
        action="store_true",
        help="Disable blog translation/generation LLM calls.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    payload = copy.deepcopy(SAMPLE_SUMMARY_RESULT)
    config = _build_override_config(args)

    if args.real:
        result = write_to_feishu_docx(payload, config=config)
    else:
        with patch("requests.post", side_effect=_mock_requests_post), patch(
            "requests.get", side_effect=_mock_requests_get
        ):
            result = write_to_feishu_docx(payload, config=config)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
