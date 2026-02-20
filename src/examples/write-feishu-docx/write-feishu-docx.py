"""Sample utilities for write-feishu-docx flow based on spec constraints."""

from __future__ import annotations

import argparse
import copy
import json
from typing import Any, Dict, List

WIKI_NODE_CREATE_ENDPOINT = (
    "https://open.feishu.cn/document/server-docs/docs/wiki-v2/space-node/create"
)
DOCUMENT_BLOCK_CREATE_ENDPOINT = (
    "https://open.feishu.cn/document/docs/docs/document-block/create-2"
)

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
        },
        {
            "source_type": "YouTube Channels",
            "source_title": "Example Channel",
            "success": True,
            "items": [
                {
                    "title": "Example Video",
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "published": "2026-02-19T12:00:00Z",
                    "processing_time": "0.8s",
                    "model_used": "gemini-2.5-flash",
                    "tokens_consumed": 520,
                    "brief": "示例视频简介。",
                    "summary": "示例视频总结。",
                    "success": True,
                    "error": None,
                }
            ],
        },
    ],
}


def build_required_config(space_id: str, parent_node_token: str) -> Dict[str, str]:
    """Build required wiki config and validate non-empty values."""
    if not space_id.strip():
        raise ValueError("FEISHU_WIKI_SPACE_ID is required")
    if not parent_node_token.strip():
        raise ValueError("FEISHU_WIKI_PARENT_NODE_TOKEN is required")
    return {
        "space_id": space_id.strip(),
        "parent_node_token": parent_node_token.strip(),
    }


def flatten_items(summary_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten source groups into item rows with source metadata."""
    rows: List[Dict[str, Any]] = []
    for source in summary_result.get("results", []):
        source_type = source.get("source_type", "")
        source_title = source.get("source_title", "")
        for item in source.get("items", []):
            row = copy.deepcopy(item)
            row["source_type"] = source_type
            row["source_title"] = source_title
            rows.append(row)
    return rows


def build_sub_doc_markdown(item: Dict[str, Any]) -> str:
    """Build sub-document markdown text according to spec template."""
    title = item.get("title", "")
    source_title = item.get("source_title", "")
    source_type = item.get("source_type", "")
    url = item.get("url", "")
    published = item.get("published", "")
    tokens = item.get("tokens_consumed", 0)
    brief = item.get("brief", "") or "无简介内容"
    summary = item.get("summary", "") or "无总结内容"
    success = item.get("success", False)
    error = item.get("error", "")
    status_line = "成功" if success else f"失败（{error or 'unknown error'}）"

    lines = [
        "## 1 文章标题",
        f"### {title}",
        f"* 来源：{source_title}（{source_type}）",
        f"* 原文链接：{url}",
        f"* 发布时间：{published}",
        f"* 消耗Token：{tokens}个",
        f"* 文章简介：{brief}",
        f"* 处理结果：{status_line}",
        "",
        "## 2 文章总结",
        "",
        summary,
    ]

    if source_type == "Blogs":
        lines.extend(
            [
                "",
                "## 3 翻译文章",
                "",
                "待创建翻译子文档并回填链接",
                "",
                "## 4 生成公众号文章",
                "",
                "待创建公众号子文档并回填链接",
            ]
        )

    return "\n".join(lines)


def build_wiki_node_create_payload(
    space_id: str,
    parent_node_token: str,
    title: str,
) -> Dict[str, Any]:
    """Build request payload for wiki node creation."""
    return {
        "space_id": space_id,
        "parent_node_token": parent_node_token,
        "obj_type": "docx",
        "title": title,
    }


def build_document_block_create_payload(
    document_id: str,
    markdown: str,
) -> Dict[str, Any]:
    """Build minimal request payload for document block creation."""
    return {
        "children_id": [],
        "index": 0,
        "document_id": document_id,
        "children": [
            {
                "block_type": 2,
                "text": {"elements": [{"text_run": {"content": markdown}}]},
            }
        ],
    }


def main() -> None:
    """Print sample payloads aligned to the two fixed API endpoints."""
    parser = argparse.ArgumentParser(description="Preview write-feishu-docx sample payloads.")
    parser.add_argument("--space-id", type=str, required=True, help="FEISHU_WIKI_SPACE_ID")
    parser.add_argument(
        "--parent-node-token",
        type=str,
        required=True,
        help="FEISHU_WIKI_PARENT_NODE_TOKEN",
    )
    args = parser.parse_args()

    config = build_required_config(args.space_id, args.parent_node_token)
    first_item = flatten_items(SAMPLE_SUMMARY_RESULT)[0]
    markdown = build_sub_doc_markdown(first_item)
    create_node_payload = build_wiki_node_create_payload(
        space_id=config["space_id"],
        parent_node_token=config["parent_node_token"],
        title=SAMPLE_SUMMARY_RESULT["target_date"],
    )
    create_block_payload = build_document_block_create_payload(
        document_id="doccn_sample",
        markdown=markdown,
    )

    print(f"node_create_endpoint: {WIKI_NODE_CREATE_ENDPOINT}")
    print(json.dumps(create_node_payload, ensure_ascii=False, indent=2))
    print(f"block_create_endpoint: {DOCUMENT_BLOCK_CREATE_ENDPOINT}")
    print(json.dumps(create_block_payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
