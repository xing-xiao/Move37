"""Main writer entry for write-feishu-docx."""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

from move37.summarize.config import ConfigurationError as LLMConfigurationError
from move37.summarize.config import load_config as load_llm_config
from move37.summarize.llm_client import LLMClient

from .blog_processor import BlogArticleProcessor
from .config import load_write_docx_config
from .content_extractor import ContentExtractor
from .content_processor import ContentProcessor
from .document_manager import DocumentManager
from .errors import ConfigurationError, DocumentOperationError, LLMError
from .feishu_client import FeishuAPIClient
from .translator import ArticleTranslator
from .wechat_generator import WeChatArticleGenerator

LOGGER = logging.getLogger(__name__)


class _DisabledArticleTranslator:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def translate_article(self, content: str) -> str:
        raise LLMError(self.reason)


class _DisabledWeChatGenerator:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def generate_wechat_article(self, content: str) -> str:
        raise LLMError(self.reason)


def _flatten_content_items(summary_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for source in summary_result.get("results", []):
        if not isinstance(source, dict):
            continue
        source_type = source.get("source_type")
        source_title = source.get("source_title")
        source_success = source.get("success", True)
        source_items = source.get("items")
        if source_success is False or not isinstance(source_items, list):
            continue

        for raw_item in source_items:
            if not isinstance(raw_item, dict):
                continue
            item = copy.deepcopy(raw_item)
            item["source_type"] = source_type
            item["source_title"] = source_title
            items.append(item)
    return items


def _create_llm_deps(
    llm_overrides: Optional[Dict[str, Any]] = None,
) -> tuple[ArticleTranslator | _DisabledArticleTranslator, WeChatArticleGenerator | _DisabledWeChatGenerator, Optional[str]]:
    llm_error: Optional[str] = None
    try:
        llm_loaded = load_llm_config(llm_overrides)
        llm_client = LLMClient(
            provider=llm_loaded["provider"],
            api_key=llm_loaded["api_key"],
            model=llm_loaded["model"],
            base_url=llm_loaded["base_url"],
            temperature=llm_loaded["temperature"],
            max_tokens=llm_loaded["max_tokens"],
            timeout=llm_loaded["timeout"],
            max_retries=llm_loaded["max_retries"],
        )
        return ArticleTranslator(llm_client), WeChatArticleGenerator(llm_client), None
    except (LLMConfigurationError, ValueError) as exc:
        llm_error = (
            "LLM configuration is invalid for blog translation/generation: "
            f"{exc}"
        )
        LOGGER.warning(llm_error)
        return _DisabledArticleTranslator(llm_error), _DisabledWeChatGenerator(llm_error), llm_error


def write_to_feishu_docx(
    summary_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Write summarize result to Feishu wiki documents."""
    default_result = {
        "success": False,
        "main_doc_token": None,
        "main_doc_url": None,
        "processed": 0,
        "successful": 0,
        "failed": 0,
        "details": [],
        "errors": [],
    }

    if not isinstance(summary_result, dict):
        default_result["errors"].append("summary_result must be a dictionary")
        return default_result

    target_date = str(summary_result.get("target_date") or "").strip()
    if not target_date:
        default_result["errors"].append("summary_result.target_date is required")
        return default_result

    try:
        loaded_config = load_write_docx_config(config)
    except ConfigurationError as exc:
        default_result["errors"].append(f"configuration_error: {exc}")
        return default_result

    feishu_client = FeishuAPIClient(
        app_id=loaded_config["app_id"],
        app_secret=loaded_config["app_secret"],
        timeout=loaded_config["timeout"],
        max_retries=loaded_config["max_retries"],
        base_url=loaded_config["base_url"],
    )
    document_manager = DocumentManager(
        feishu_client=feishu_client,
        space_id=loaded_config["wiki_space_id"],
    )

    try:
        main_doc_token = document_manager.create_main_document(
            title=target_date,
            parent_node_token=loaded_config["wiki_parent_node_token"],
        )
    except DocumentOperationError as exc:
        default_result["errors"].append(f"main_doc_create_failed: {exc}")
        return default_result

    translator, wechat_generator, llm_error = _create_llm_deps(loaded_config.get("llm_config"))

    blog_processor = BlogArticleProcessor(
        document_manager=document_manager,
        content_extractor=ContentExtractor(timeout=loaded_config["timeout"]),
        translator=translator,
        wechat_generator=wechat_generator,
    )
    content_processor = ContentProcessor(
        document_manager=document_manager,
        blog_processor=blog_processor,
    )

    content_items = _flatten_content_items(summary_result)
    LOGGER.info("write_to_feishu_docx start target_date=%s items=%s", target_date, len(content_items))

    process_result = content_processor.process_content_items(
        main_doc_token=main_doc_token,
        content_items=content_items,
    )

    errors = list(process_result.get("errors", []))
    if llm_error:
        errors.append(llm_error)

    failed_count = int(process_result.get("failed", 0) or 0)

    return {
        "success": failed_count == 0,
        "main_doc_token": main_doc_token,
        "main_doc_url": document_manager.build_document_url(main_doc_token),
        "processed": int(process_result.get("processed", 0) or 0),
        "successful": int(process_result.get("successful", 0) or 0),
        "failed": failed_count,
        "details": process_result.get("details", []),
        "errors": errors,
    }
