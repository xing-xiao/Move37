"""Tests for src/examples/write-feishu-docx/write-feishu-docx.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


def _load_module() -> Any:
    module_path = Path(__file__).with_name("write-feishu-docx.py")
    spec = importlib.util.spec_from_file_location("write_feishu_docx_sample", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load write-feishu-docx.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_spec_endpoints_are_fixed() -> None:
    module = _load_module()
    assert (
        module.WIKI_NODE_CREATE_ENDPOINT
        == "https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create"
    )
    assert (
        module.DOCUMENT_BLOCK_CREATE_ENDPOINT
        == "https://open.feishu.cn/document/docs/docs/document-block/create-2"
    )


def test_required_wiki_config_validation() -> None:
    module = _load_module()
    config = module.build_required_config("7600000000000000000", "CzovwU3CaiVcXgk418acWqBKnLh")
    assert config["space_id"] == "7600000000000000000"
    assert config["parent_node_token"] == "CzovwU3CaiVcXgk418acWqBKnLh"


def test_blog_markdown_contains_translation_and_wechat_sections() -> None:
    module = _load_module()
    blog_item = module.flatten_items(module.SAMPLE_SUMMARY_RESULT)[0]
    markdown = module.build_sub_doc_markdown(blog_item)
    assert "## 3 翻译文章" in markdown
    assert "## 4 生成公众号文章" in markdown


def test_youtube_markdown_excludes_translation_and_wechat_sections() -> None:
    module = _load_module()
    youtube_item = module.flatten_items(module.SAMPLE_SUMMARY_RESULT)[1]
    markdown = module.build_sub_doc_markdown(youtube_item)
    assert "## 3 翻译文章" not in markdown
    assert "## 4 生成公众号文章" not in markdown


def test_wiki_node_payload_contains_space_and_parent_token() -> None:
    module = _load_module()
    payload = module.build_wiki_node_create_payload(
        space_id="7600000000000000000",
        parent_node_token="CzovwU3CaiVcXgk418acWqBKnLh",
        title="2026-02-19",
    )
    assert payload["space_id"] == "7600000000000000000"
    assert payload["parent_node_token"] == "CzovwU3CaiVcXgk418acWqBKnLh"
    assert payload["obj_type"] == "docx"
    assert payload["title"] == "2026-02-19"
