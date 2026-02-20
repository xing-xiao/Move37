"""Unit tests for move37.write_docx."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import patch

import pytest
import requests

from move37.write_docx.config import load_write_docx_config
from move37.write_docx.errors import ConfigurationError
from move37.write_docx.sub_document_builder import SubDocumentBuilder
from move37.write_docx.writer import write_to_feishu_docx


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


def test_load_write_docx_config_requires_space_and_parent() -> None:
    with pytest.raises(ConfigurationError):
        load_write_docx_config(
            {
                "app_id": "cli_xxx",
                "app_secret": "secret",
                "wiki_space_id": "",
                "wiki_parent_node_token": "",
            },
            env_path="/tmp/move37_write_docx_missing_env_for_test.env",
        )


def test_sub_document_builder_blog_and_youtube_sections() -> None:
    blog_item = {
        "title": "blog title",
        "source_type": "Blogs",
        "source_title": "blog source",
        "url": "https://example.com/a",
        "published": "2026-02-19",
        "tokens_consumed": 100,
        "brief": "brief",
        "summary": "summary",
        "success": True,
    }
    youtube_item = {
        **blog_item,
        "source_type": "YouTube Channels",
        "url": "https://www.youtube.com/watch?v=abc",
    }

    blog_content = SubDocumentBuilder.build_content(blog_item)
    youtube_content = SubDocumentBuilder.build_content(youtube_item)

    assert "## 3 翻译文章" in blog_content
    assert "## 4 生成公众号文章" in blog_content
    assert "## 3 翻译文章" not in youtube_content
    assert "## 4 生成公众号文章" not in youtube_content


def test_write_to_feishu_docx_end_to_end_with_mock() -> None:
    summary_result = {
        "collection_date": "2026-02-20",
        "target_date": "2026-02-19",
        "results": [
            {
                "source_type": "Blogs",
                "source_title": "example.com",
                "success": True,
                "items": [
                    {
                        "title": "Example blog",
                        "url": "https://example.com/post",
                        "published": "2026-02-19T00:00:00Z",
                        "tokens_consumed": 321,
                        "brief": "brief",
                        "summary": "summary",
                        "success": True,
                        "error": None,
                    }
                ],
            }
        ],
    }

    counter = {"value": 0}

    def mock_post(url: str, json: Dict[str, Any] | None = None, **_: Any) -> _MockResponse:
        if url.endswith("/open-apis/auth/v3/tenant_access_token/internal"):
            return _MockResponse({"code": 0, "msg": "ok", "tenant_access_token": "token"})

        if "/open-apis/wiki/v2/spaces/" in url and url.endswith("/nodes"):
            counter["value"] += 1
            return _MockResponse({"code": 0, "msg": "ok", "data": {"node_token": f"wikcn_{counter['value']}"}})

        if "/open-apis/docx/v1/documents/" in url and "/children" in url:
            return _MockResponse({"code": 0, "msg": "ok", "data": {"children": []}})

        return _MockResponse({"code": 404, "msg": "not found"}, status_code=404)

    def mock_get(url: str, **_: Any) -> _MockResponse:
        html = """
        <html><body><article>
          <p>This is paragraph one for extraction and translation sample content.</p>
          <p>This is paragraph two for extraction and translation sample content.</p>
        </article></body></html>
        """
        if "example.com" in url:
            return _MockResponse({}, status_code=200, text=html)
        return _MockResponse({}, status_code=404, text="")

    with patch("requests.post", side_effect=mock_post), patch("requests.get", side_effect=mock_get):
        result = write_to_feishu_docx(
            summary_result,
            config={
                "app_id": "cli_mock",
                "app_secret": "secret_mock",
                "wiki_space_id": "7600000000000000000",
                "wiki_parent_node_token": "wikcn_parent",
                # Force LLM init failure so test does not depend on real keys/network.
                "llm_config": {"provider": "openai"},
            },
        )

    assert result["main_doc_token"]
    assert result["processed"] == 1
    assert result["successful"] == 1
    assert result["failed"] == 0
    assert len(result["details"]) == 1
    detail = result["details"][0]
    assert detail["sub_doc_token"]
    assert detail["translation_doc_token"]
    assert detail["wechat_doc_token"]
