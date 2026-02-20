"""Content item processor for write-feishu-docx pipeline."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .blog_processor import BlogArticleProcessor
from .document_manager import DocumentManager
from .errors import DocumentOperationError
from .sub_document_builder import SubDocumentBuilder

LOGGER = logging.getLogger(__name__)


class ContentProcessor:
    """Process content items and create wiki sub-documents."""

    def __init__(
        self,
        document_manager: DocumentManager,
        blog_processor: BlogArticleProcessor,
    ) -> None:
        self.document_manager = document_manager
        self.blog_processor = blog_processor

    def process_content_items(
        self,
        main_doc_token: str,
        content_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create sub-documents for content items with partial-failure tolerance."""
        processed = 0
        successful = 0
        failed = 0
        details: List[Dict[str, Any]] = []
        errors: List[str] = []

        for item in content_items:
            processed += 1
            title = str(item.get("title") or "无标题")
            url = str(item.get("url") or "")

            detail: Dict[str, Any] = {
                "title": title,
                "url": url,
                "sub_doc_token": None,
                "sub_doc_url": None,
                "translation_doc_token": None,
                "translation_doc_url": None,
                "wechat_doc_token": None,
                "wechat_doc_url": None,
                "success": False,
                "errors": [],
            }

            try:
                sub_doc_token = self.document_manager.create_sub_document(
                    parent_node_token=main_doc_token,
                    title=title,
                    content="",
                )
            except DocumentOperationError as exc:
                failed += 1
                message = f"sub_doc_create_failed title={title}: {exc}"
                detail["errors"].append(message)
                errors.append(message)
                details.append(detail)
                continue

            detail["sub_doc_token"] = sub_doc_token
            detail["sub_doc_url"] = self.document_manager.build_document_url(sub_doc_token)

            blog_result: Dict[str, Any] = {
                "translation_doc_token": None,
                "translation_doc_url": None,
                "wechat_doc_token": None,
                "wechat_doc_url": None,
                "errors": [],
            }
            if self.blog_processor.is_blog_article(item):
                blog_result = self.blog_processor.process_blog_article(
                    parent_doc_token=sub_doc_token,
                    article_url=url,
                    article_title=title,
                )
                detail["translation_doc_token"] = blog_result.get("translation_doc_token")
                detail["translation_doc_url"] = blog_result.get("translation_doc_url")
                detail["wechat_doc_token"] = blog_result.get("wechat_doc_token")
                detail["wechat_doc_url"] = blog_result.get("wechat_doc_url")
                for err in blog_result.get("errors", []):
                    text = str(err)
                    detail["errors"].append(text)
                    errors.append(f"blog_process_failed title={title}: {text}")

            content = SubDocumentBuilder.build_content(
                content_item=item,
                translation_doc_url=blog_result.get("translation_doc_url"),
                wechat_doc_url=blog_result.get("wechat_doc_url"),
            )

            try:
                self.document_manager.write_document_content(sub_doc_token, content)
            except DocumentOperationError as exc:
                failed += 1
                message = f"sub_doc_write_failed title={title}: {exc}"
                detail["errors"].append(message)
                errors.append(message)
                details.append(detail)
                continue

            detail["success"] = True
            successful += 1
            details.append(detail)

        return {
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "details": details,
            "errors": errors,
        }
