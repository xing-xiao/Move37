"""Summarization coordinator functions."""

from __future__ import annotations

import copy
import logging
import time
from typing import Any, Dict, Optional

from .config import ConfigurationError, load_config
from .content_fetcher import extract_youtube_video_id, is_youtube_url
from .llm_client import LLMClient

LOGGER = logging.getLogger(__name__)


def _create_llm_client(loaded_config: Dict[str, Any]) -> LLMClient:
    return LLMClient(
        provider=loaded_config["provider"],
        api_key=loaded_config["api_key"],
        model=loaded_config["model"],
        base_url=loaded_config["base_url"],
        temperature=loaded_config["temperature"],
        max_tokens=loaded_config["max_tokens"],
        timeout=loaded_config["timeout"],
        max_retries=loaded_config["max_retries"],
    )


def _create_gemini_youtube_client(base_config: Dict[str, Any]) -> LLMClient:
    gemini_config = load_config(
        {
            "provider": "gemini",
            "temperature": base_config["temperature"],
            "max_tokens": base_config["max_tokens"],
            "timeout": base_config["timeout"],
            "max_retries": base_config["max_retries"],
        }
    )
    return _create_llm_client(gemini_config)


def summarize_single_url(
    url: str,
    title: str,
    llm_client: LLMClient,
    prompt_template: str,
    content: str | None = None,
    chunk_size: int | None = None,
) -> Dict[str, Any]:
    """Summarize one URL and collect processing metadata."""
    started_at = time.time()
    LOGGER.info("Start summarizing title=%s url=%s", title, url)

    try:
        response = llm_client.generate_summary(
            url=url,
            prompt_template=prompt_template,
            content=content,
            chunk_size=chunk_size,
        )
    except Exception as exc:  # noqa: BLE001
        duration = f"{time.time() - started_at:.1f}s"
        LOGGER.error("Unexpected summarize error, url=%s, error=%s", url, exc)
        return {
            "processing_time": duration,
            "model_used": llm_client.model,
            "tokens_consumed": 0,
            "brief": "",
            "summary": "",
            "success": False,
            "error": str(exc),
        }

    duration = f"{time.time() - started_at:.1f}s"
    result = {
        "processing_time": duration,
        "model_used": response.get("model_used", llm_client.model),
        "tokens_consumed": int(response.get("tokens_consumed", 0) or 0),
        "brief": str(response.get("brief", "")),
        "summary": str(response.get("summary", "")),
        "success": bool(response.get("success", False)),
        "error": response.get("error"),
    }

    if result["success"]:
        brief_preview = result["brief"][:50]
        LOGGER.info(
            "Summary completed, url=%s, title=%s, time=%s, tokens=%s, brief=%s",
            url,
            title,
            result["processing_time"],
            result["tokens_consumed"],
            brief_preview,
        )
    else:
        LOGGER.error(
            "Summary failed, url=%s, title=%s, time=%s, error=%s",
            url,
            title,
            result["processing_time"],
            result["error"],
        )

    return result


def summarize_all(
    collection_result: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate summaries for all URL items in collection_result."""
    if not isinstance(collection_result, dict):
        raise ValueError("`collection_result` must be a dictionary.")

    loaded_config = load_config(config)
    llm_client = _create_llm_client(loaded_config)
    gemini_client: LLMClient | None = None
    prompt_template = loaded_config["prompt_template"]

    output = copy.deepcopy(collection_result)
    sources = output.get("results")
    if not isinstance(sources, list):
        LOGGER.warning("No `results` list found. Return original structure.")
        return output

    total_items = sum(
        len(source.get("items", []))
        for source in sources
        if isinstance(source, dict)
        and source.get("success", True)
        and isinstance(source.get("items"), list)
    )

    processed_items = 0
    for source in sources:
        if not isinstance(source, dict):
            LOGGER.warning("Skip invalid source entry: %r", source)
            continue

        if source.get("success") is False:
            LOGGER.warning(
                "Skip source with success=false: %s (%s)",
                source.get("source_title", "Unknown"),
                source.get("source_type", "Unknown"),
            )
            continue

        items = source.get("items")
        if not isinstance(items, list):
            LOGGER.warning("Skip source with invalid items: %s", source.get("source_title"))
            continue

        for item in items:
            processed_items += 1
            if not isinstance(item, dict):
                LOGGER.warning("Skip invalid item: %r", item)
                continue

            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()

            LOGGER.info("Processing progress %s/%s: %s", processed_items, total_items, url)
            if not url:
                item.update(
                    {
                        "processing_time": "0.0s",
                        "model_used": loaded_config["model"],
                        "tokens_consumed": 0,
                        "brief": "",
                        "summary": "",
                        "success": False,
                        "error": "Missing URL",
                    }
                )
                LOGGER.error("Missing URL in item, title=%s", title)
                continue

            extra_summary_fields: Dict[str, Any] = {}
            active_client = llm_client
            active_prompt_template = prompt_template
            if is_youtube_url(url):
                if gemini_client is None:
                    try:
                        gemini_client = _create_gemini_youtube_client(loaded_config)
                    except ConfigurationError as gemini_cfg_error:
                        item.update(
                            {
                                "processing_time": "0.0s",
                                "model_used": loaded_config["model"],
                                "tokens_consumed": 0,
                                "brief": "",
                                "summary": "",
                                "success": False,
                                "error": (
                                    "YouTube summary requires Gemini configuration: "
                                    f"{gemini_cfg_error}"
                                ),
                                "summary_basis": "none",
                            }
                        )
                        continue

                active_client = gemini_client
                extra_summary_fields = {
                    "summary_basis": "gemini_url",
                    "youtube_video_id": str(extract_youtube_video_id(url) or ""),
                }

            summary = summarize_single_url(
                url=url,
                title=title,
                llm_client=active_client,
                prompt_template=active_prompt_template,
            )
            if extra_summary_fields:
                summary.update(extra_summary_fields)
            item.update(summary)

    LOGGER.info("Summarization completed. processed=%s", processed_items)
    return output
