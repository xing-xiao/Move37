"""Feishu wiki writer built on move37.utils.feishu.FeishuClient."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from move37.utils.feishu import FeishuClient


def _validate_summary_result(summary_result: Dict[str, Any]) -> None:
    if not isinstance(summary_result, dict):
        raise ValueError("`summary_result` must be a dictionary.")
    if not isinstance(summary_result.get("results"), list):
        raise ValueError("`summary_result.results` must be a list.")


def _build_doc_title(summary_result: Dict[str, Any]) -> str:
    target_date = str(summary_result.get("target_date") or "").strip()
    if not target_date:
        return "每日咨询摘要"
    return f"{target_date}咨询摘要"


def _build_children_blocks(summary_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    children: List[Dict[str, Any]] = []
    for source in summary_result.get("results", []):
        if not isinstance(source, dict):
            continue

        source_title = str(source.get("source_title") or "Unknown").strip()
        source_type = str(source.get("source_type") or "Unknown").strip()
        source_heading = f"{source_title} ({source_type})"

        children.append(
            {
                "block_type": 3,
                "heading1": {"elements": [{"text_run": {"content": source_heading}}]},
            }
        )

        items = source.get("items", [])
        if not isinstance(items, list):
            continue

        for item in items:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title") or "未命名内容").strip()
            url = str(item.get("url") or "").strip() or "N/A"
            published = str(item.get("published") or "").strip() or "N/A"
            model_used = str(item.get("model_used") or "").strip() or "N/A"
            processing_time = str(item.get("processing_time") or "").strip() or "N/A"
            tokens = str(item.get("tokens_consumed") or "0").strip()
            brief = str(item.get("brief") or "").strip()
            summary = str(item.get("summary") or "").strip()
            success = bool(item.get("success"))
            error = str(item.get("error") or "").strip()

            children.append(
                {
                    "block_type": 4,
                    "heading2": {"elements": [{"text_run": {"content": title}}]},
                }
            )
            children.append(
                {
                    "block_type": 2,
                    "paragraph": {
                        "elements": [
                            {
                                "text_run": {
                                    "content": (
                                        f"链接: {url}\n发布时间: {published}\n模型: {model_used}\n"
                                        f"耗时: {processing_time}\nToken: {tokens}"
                                    )
                                }
                            }
                        ]
                    },
                }
            )
            if brief:
                children.append(
                    {
                        "block_type": 5,
                        "quote": {"elements": [{"text_run": {"content": brief}}]},
                    }
                )
            if summary:
                children.append(
                    {
                        "block_type": 2,
                        "paragraph": {"elements": [{"text_run": {"content": summary}}]},
                    }
                )
            if (not success) and error:
                children.append(
                    {
                        "block_type": 5,
                        "quote": {"elements": [{"text_run": {"content": f"失败原因: {error}"}}]},
                    }
                )
    return children


class FeishuWikiWriter:
    """Write summary_result into Feishu wiki/docx."""

    def __init__(self, client: FeishuClient) -> None:
        self.client = client

    def write_summary_to_wiki(
        self,
        summary_result: Dict[str, Any],
        space_id: str,
        parent_node_token: str,
        title: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        _validate_summary_result(summary_result)

        resolved_space_id = str(space_id or "").strip()
        resolved_parent_token = str(parent_node_token or "").strip()
        if not resolved_space_id:
            raise ValueError("`space_id` is required.")
        if not resolved_parent_token:
            raise ValueError("`parent_node_token` is required.")

        doc_title = str(title or _build_doc_title(summary_result)).strip()
        if not doc_title:
            doc_title = "每日咨询摘要"

        children = _build_children_blocks(summary_result)
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "title": doc_title,
                "children_count": len(children),
            }

        created = self.client.create_docx(
            space_id=resolved_space_id,
            parent_node_token=resolved_parent_token,
            node_name="origin",
            title=doc_title,
        )
        node = created.get("node") if isinstance(created, dict) else None
        node_token = ""
        if isinstance(node, dict):
            node_token = str(node.get("node_token") or "").strip()
        document_id = ""
        if isinstance(node, dict):
            document_id = str(node.get("obj_token") or "").strip()
        if not document_id:
            document_id = str(created.get("obj_token") or "").strip() if isinstance(created, dict) else ""
        if not node_token:
            node_token = str(created.get("node_token") or "").strip() if isinstance(created, dict) else ""
        if not document_id or not node_token:
            raise RuntimeError("create_docx response missing node_token or obj_token.")

        write_result = self.client.write_docx_content(
            document_id=document_id,
            block_id=node_token,
            children=children,
        )
        return {
            "success": True,
            "title": doc_title,
            "document_id": document_id,
            "node_token": node_token,
            "create_response": created,
            "write_response": write_result,
            "children_count": len(children),
        }


def write_to_feishu_docx(
    summary_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Public API for all-in-one workflow step 4."""
    overrides = dict(config or {})
    app_id = str(overrides.get("app_id") or os.getenv("FEISHU_APP_ID", "")).strip()
    app_secret = str(overrides.get("app_secret") or os.getenv("FEISHU_APP_SECRET", "")).strip()
    space_id = str(overrides.get("space_id") or os.getenv("FEISHU_WIKI_SPACE_ID", "")).strip()
    parent_node_token = str(
        overrides.get("parent_node_token") or os.getenv("FEISHU_WIKI_PARENT_NODE_TOKEN", "")
    ).strip()
    timeout = float(overrides.get("timeout") or 30.0)
    base_url = str(overrides.get("base_url") or "https://open.feishu.cn").strip()
    dry_run = bool(overrides.get("dry_run", False))
    title = overrides.get("title")

    if not app_id:
        raise ValueError("Missing required config: FEISHU_APP_ID")
    if not app_secret:
        raise ValueError("Missing required config: FEISHU_APP_SECRET")
    if not space_id:
        raise ValueError("Missing required config: FEISHU_WIKI_SPACE_ID")
    if not parent_node_token:
        raise ValueError("Missing required config: FEISHU_WIKI_PARENT_NODE_TOKEN")

    client = FeishuClient(
        app_id=app_id,
        app_secret=app_secret,
        timeout=timeout,
        base_url=base_url,
    )
    writer = FeishuWikiWriter(client)
    return writer.write_summary_to_wiki(
        summary_result=summary_result,
        space_id=space_id,
        parent_node_token=parent_node_token,
        title=str(title).strip() if title is not None else None,
        dry_run=dry_run,
    )
