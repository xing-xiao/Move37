"""Blog article processing for translation and WeChat article generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .content_extractor import ContentExtractor
from .document_manager import DocumentManager
from .errors import ContentExtractionError, DocumentOperationError, LLMError
from .sub_document_builder import is_blog_item
from .translator import ArticleTranslator
from .wechat_generator import WeChatArticleGenerator

LOGGER = logging.getLogger(__name__)


class BlogArticleProcessor:
    """Process blog articles to create translation and WeChat docs."""

    def __init__(
        self,
        document_manager: DocumentManager,
        content_extractor: ContentExtractor,
        translator: ArticleTranslator,
        wechat_generator: WeChatArticleGenerator,
    ) -> None:
        self.document_manager = document_manager
        self.content_extractor = content_extractor
        self.translator = translator
        self.wechat_generator = wechat_generator

    def is_blog_article(self, content_item: Dict[str, Any]) -> bool:
        """Return True for non-YouTube items."""
        return is_blog_item(content_item)

    def process_blog_article(
        self,
        parent_doc_token: str,
        article_url: str,
        article_title: str,
    ) -> Dict[str, Any]:
        """Generate translation and WeChat sub-documents for a blog article."""
        errors: List[str] = []
        source_content = ""

        try:
            source_content = self.content_extractor.extract_article_content(article_url)
        except ContentExtractionError as exc:
            errors.append(f"content_extract_failed: {exc}")

        translation_success = False
        wechat_success = False
        translation_text = ""
        wechat_text = ""

        if source_content:
            try:
                translation_text = self.translator.translate_article(source_content)
                translation_success = True
            except LLMError as exc:
                errors.append(f"translation_failed: {exc}")

            try:
                wechat_text = self.wechat_generator.generate_wechat_article(source_content)
                wechat_success = True
            except LLMError as exc:
                errors.append(f"wechat_generation_failed: {exc}")

        if not source_content:
            translation_text = "翻译失败：原文提取失败。"
            wechat_text = "生成失败：原文提取失败。"
        else:
            if not translation_success:
                translation_text = "翻译失败：LLM 翻译失败。"
            if not wechat_success:
                wechat_text = "生成失败：LLM 改写失败。"

        translation_doc_token = ""
        wechat_doc_token = ""

        try:
            translation_doc_token = self.document_manager.create_sub_document(
                parent_node_token=parent_doc_token,
                title=f"翻译文章 - {article_title}",
                content=translation_text,
            )
        except DocumentOperationError as exc:
            errors.append(f"translation_doc_create_failed: {exc}")

        try:
            wechat_doc_token = self.document_manager.create_sub_document(
                parent_node_token=parent_doc_token,
                title=f"公众号文章 - {article_title}",
                content=wechat_text,
            )
        except DocumentOperationError as exc:
            errors.append(f"wechat_doc_create_failed: {exc}")

        return {
            "translation_doc_token": translation_doc_token or None,
            "wechat_doc_token": wechat_doc_token or None,
            "translation_doc_url": (
                self.document_manager.build_document_url(translation_doc_token)
                if translation_doc_token
                else None
            ),
            "wechat_doc_url": (
                self.document_manager.build_document_url(wechat_doc_token)
                if wechat_doc_token
                else None
            ),
            "translation_success": translation_success and bool(translation_doc_token),
            "wechat_success": wechat_success and bool(wechat_doc_token),
            "errors": errors,
        }
