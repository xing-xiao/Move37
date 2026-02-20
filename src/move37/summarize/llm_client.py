"""LLM client for URL summarization."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, Tuple

LOGGER = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = {"openai", "deepseek", "gemini", "glm"}


def exponential_backoff(attempt: int, base_delay: float = 1.0) -> float:
    """Calculate exponential backoff delay in seconds."""
    return base_delay * (2**attempt)


class LLMClient:
    """LLM client with provider-specific adapters and retry support."""

    def __init__(
        self,
        provider: str,
        api_key: str,
        model: str,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        timeout: int = 60,
        max_retries: int = 3,
    ) -> None:
        self.provider = provider.strip().lower()
        if self.provider not in SUPPORTED_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
            raise ValueError(f"Unsupported provider `{self.provider}`. Supported: {supported}")

        self.api_key = api_key.strip()
        self.model = model.strip()
        self.base_url = base_url.strip() if isinstance(base_url, str) and base_url.strip() else None
        self.temperature = float(temperature)
        self.max_tokens = int(max_tokens)
        self.timeout = int(timeout)
        self.max_retries = max(1, int(max_retries))
        self._runtime_model: str | None = None

    def generate_summary(
        self,
        url: str,
        prompt_template: str,
        content: str | None = None,
        chunk_size: int | None = None,
    ) -> Dict[str, Any]:
        """Generate summary for a URL/content using the selected provider."""
        if content and chunk_size and len(content) > chunk_size:
            return self._generate_summary_with_chunking(
                url=url,
                prompt_template=prompt_template,
                content=content,
                chunk_size=chunk_size,
            )
        return self._generate_summary_once(url=url, prompt_template=prompt_template, content=content)

    def _generate_summary_once(
        self,
        url: str,
        prompt_template: str,
        content: str | None = None,
    ) -> Dict[str, Any]:
        prompt = self._render_prompt(url=url, prompt_template=prompt_template, content=content)
        last_error = "Unknown LLM error"

        for attempt in range(self.max_retries):
            try:
                LOGGER.info(
                    "Calling provider=%s model=%s for URL=%s (attempt %s/%s)",
                    self.provider,
                    self._effective_model(),
                    url,
                    attempt + 1,
                    self.max_retries,
                )
                raw_text, token_count = self._request_summary(prompt)
                parsed = self._parse_summary_payload(raw_text)
                brief = self._truncate(parsed["brief"], 100, "brief", url)
                summary = self._truncate(parsed["summary"], 1000, "summary", url)
                return {
                    "brief": brief,
                    "summary": summary,
                    "model_used": self._effective_model(),
                    "tokens_consumed": int(token_count),
                    "success": True,
                    "error": None,
                }
            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                is_last_attempt = attempt == self.max_retries - 1
                if is_last_attempt:
                    LOGGER.error(
                        "LLM request failed after %s attempts, URL=%s, error=%s",
                        self.max_retries,
                        url,
                        last_error,
                    )
                    break

                delay = exponential_backoff(attempt)
                LOGGER.warning(
                    "LLM request failed (attempt %s/%s), URL=%s, retry in %.1fs, error=%s",
                    attempt + 1,
                    self.max_retries,
                    url,
                    delay,
                    last_error,
                )
                time.sleep(delay)

        return {
            "brief": "",
            "summary": "",
            "model_used": self._effective_model(),
            "tokens_consumed": 0,
            "success": False,
            "error": last_error,
        }

    def _generate_summary_with_chunking(
        self,
        url: str,
        prompt_template: str,
        content: str,
        chunk_size: int,
    ) -> Dict[str, Any]:
        chunks = [content[i : i + chunk_size] for i in range(0, len(content), chunk_size)]
        LOGGER.info("Chunking content for URL=%s into %s chunks", url, len(chunks))

        chunk_prompt_template = """
你将收到一个 YouTube 字幕片段内容。请基于片段生成中文 JSON：
{
  "brief": "片段简介（50字以内）",
  "summary": "片段要点（300字以内）"
}

URL: {url}
片段内容:
{content}
""".strip()

        chunk_summaries: list[str] = []
        total_tokens = 0
        failed_chunks = 0

        for index, chunk in enumerate(chunks, start=1):
            chunk_result = self._generate_summary_once(
                url=url,
                prompt_template=chunk_prompt_template,
                content=chunk,
            )
            if not chunk_result.get("success"):
                failed_chunks += 1
                LOGGER.warning(
                    "Chunk summarize failed for URL=%s chunk=%s/%s error=%s",
                    url,
                    index,
                    len(chunks),
                    chunk_result.get("error"),
                )
                continue

            total_tokens += int(chunk_result.get("tokens_consumed", 0) or 0)
            chunk_summary = str(chunk_result.get("summary", "")).strip()
            if chunk_summary:
                chunk_summaries.append(f"[片段{index}] {chunk_summary}")

        if not chunk_summaries:
            return {
                "brief": "",
                "summary": "",
                "model_used": self._effective_model(),
                "tokens_consumed": total_tokens,
                "success": False,
                "error": "All content chunks failed to summarize.",
            }

        merged_content = "\n\n".join(chunk_summaries)
        final_result = self._generate_summary_once(
            url=url,
            prompt_template=prompt_template,
            content=merged_content,
        )
        final_result["tokens_consumed"] = int(final_result.get("tokens_consumed", 0) or 0) + total_tokens
        if failed_chunks > 0:
            warning = f"{failed_chunks}/{len(chunks)} chunks failed during chunk summarization."
            if final_result.get("success"):
                final_result["error"] = warning
            else:
                existing_error = str(final_result.get("error") or "")
                final_result["error"] = f"{warning} final_error={existing_error}".strip()
        return final_result

    @staticmethod
    def _render_prompt(url: str, prompt_template: str, content: str | None = None) -> str:
        # Use explicit token replacement instead of str.format().
        # Prompt templates may include JSON braces which would break format parsing.
        prompt = prompt_template.replace("{url}", url)
        if "{content}" in prompt:
            prompt = prompt.replace("{content}", content or "")
            return prompt

        if content:
            return (
                f"{prompt}\n\n"
                "下面是你可直接使用的内容材料，请优先基于这些材料总结，"
                "不要回答“无法访问链接”：\n"
                f"{content}"
            )
        return prompt

    def _request_summary(self, prompt: str) -> Tuple[str, int]:
        if self.provider == "gemini":
            return self._call_gemini(prompt)
        return self._call_openai_compatible(prompt)

    def _call_openai_compatible(self, prompt: str) -> Tuple[str, int]:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "openai package is required. Install with `pip install openai`."
            ) from exc

        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )
        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Chinese summarization assistant. "
                        "Always return strict JSON with keys `brief` and `summary`."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        message = completion.choices[0].message
        content = message.content or ""
        if isinstance(content, list):
            text_chunks = []
            for part in content:
                if isinstance(part, dict):
                    text_chunks.append(str(part.get("text", "")))
                else:
                    text_chunks.append(str(part))
            content = "".join(text_chunks)

        usage = getattr(completion, "usage", None)
        total_tokens = getattr(usage, "total_tokens", None)
        if total_tokens is None:
            prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(usage, "completion_tokens", 0) or 0
            total_tokens = int(prompt_tokens) + int(completion_tokens)

        return str(content).strip(), int(total_tokens or 0)

    def _call_gemini(self, prompt: str) -> Tuple[str, int]:
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "google-generativeai package is required. "
                "Install with `pip install google-generativeai`."
            ) from exc

        genai.configure(api_key=self.api_key)
        current_model = self._effective_model()
        try:
            response = self._gemini_generate(genai, current_model, prompt)
        except Exception as exc:  # noqa: BLE001
            if not self._is_gemini_model_not_found(exc):
                raise

            LOGGER.warning(
                "Configured Gemini model unavailable: %s. Trying fallback models. error=%s",
                current_model,
                exc,
            )
            fallback_models = self._gemini_fallback_candidates(genai, exclude=current_model)

            last_fallback_error = f"{type(exc).__name__}: {exc}"
            for fallback_model in fallback_models:
                try:
                    response = self._gemini_generate(genai, fallback_model, prompt)
                    self._runtime_model = fallback_model
                    LOGGER.warning(
                        "Switched Gemini model from %s to %s",
                        current_model,
                        fallback_model,
                    )
                    break
                except Exception as fallback_exc:  # noqa: BLE001
                    last_fallback_error = f"{type(fallback_exc).__name__}: {fallback_exc}"
                    if self._is_gemini_model_not_found(fallback_exc):
                        continue
                    raise
            else:
                available_models = self._list_gemini_generate_models(genai)
                model_hint = ", ".join(available_models[:8]) if available_models else "unknown"
                raise RuntimeError(
                    "Gemini model is unavailable and fallback failed. "
                    f"configured={current_model}, available_sample=[{model_hint}], "
                    f"last_error={last_fallback_error}"
                ) from exc

        text = getattr(response, "text", None)
        if not text:
            text_parts = []
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        text_parts.append(part_text)
            text = "".join(text_parts).strip()

        if not text:
            raise ValueError("Gemini returned empty content.")

        usage = getattr(response, "usage_metadata", None)
        token_count = getattr(usage, "total_token_count", None)
        if token_count is None:
            prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
            candidates_tokens = getattr(usage, "candidates_token_count", 0) or 0
            token_count = int(prompt_tokens) + int(candidates_tokens)

        return str(text).strip(), int(token_count or 0)

    def _effective_model(self) -> str:
        return self._runtime_model or self.model

    def _gemini_generate(self, genai: Any, model_name: str, prompt: str) -> Any:
        model = genai.GenerativeModel(model_name)
        return model.generate_content(
            prompt,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            },
            request_options={"timeout": self.timeout},
        )

    @staticmethod
    def _normalize_gemini_model_name(model_name: str) -> str:
        model_name = str(model_name).strip()
        if model_name.startswith("models/"):
            return model_name.split("/", 1)[1]
        return model_name

    @staticmethod
    def _is_gemini_model_not_found(exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "not found" in message
            or "not supported for generatecontent" in message
            or ("404" in message and "model" in message)
        )

    def _list_gemini_generate_models(self, genai: Any) -> list[str]:
        try:
            models = []
            for item in genai.list_models():
                methods = [str(m).lower() for m in getattr(item, "supported_generation_methods", [])]
                if "generatecontent" not in methods:
                    continue
                name = self._normalize_gemini_model_name(getattr(item, "name", ""))
                if name:
                    models.append(name)

            deduped: list[str] = []
            seen = set()
            for model in models:
                if model in seen:
                    continue
                seen.add(model)
                deduped.append(model)
            return deduped
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Failed to list Gemini models: %s", exc)
            return []

    def _gemini_fallback_candidates(self, genai: Any, exclude: str) -> list[str]:
        preferred = [
            "gemini-2.5-flash",
            "gemini-flash-latest",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ]
        exclude_norm = self._normalize_gemini_model_name(exclude)

        available = self._list_gemini_generate_models(genai)
        available_set = set(available)
        candidates: list[str] = []

        for model in preferred:
            if model == exclude_norm:
                continue
            if model in available_set:
                candidates.append(model)

        if not candidates:
            for model in available:
                if model == exclude_norm:
                    continue
                if model.startswith("gemini-2.5-flash") or model.startswith("gemini-flash"):
                    candidates.append(model)
            for model in available:
                if model == exclude_norm or model in candidates:
                    continue
                candidates.append(model)

        if not candidates:
            for model in preferred:
                if model != exclude_norm:
                    candidates.append(model)

        return candidates

    def _parse_summary_payload(self, response_text: str) -> Dict[str, str]:
        payload = self._extract_json_object(response_text)
        brief = str(payload.get("brief", "")).strip()
        summary = str(payload.get("summary", "")).strip()
        if not brief or not summary:
            raise ValueError("LLM response must include non-empty `brief` and `summary`.")
        return {"brief": brief, "summary": summary}

    @staticmethod
    def _extract_json_object(text: str) -> Dict[str, Any]:
        stripped = text.strip()
        if not stripped:
            raise ValueError("Empty response from LLM.")

        candidates = [stripped]
        if "```" in stripped:
            no_fence = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
            no_fence = re.sub(r"\s*```$", "", no_fence).strip()
            candidates.append(no_fence)

        brace_match = re.search(r"\{[\s\S]*\}", stripped)
        if brace_match:
            candidates.append(brace_match.group(0))

        for candidate in candidates:
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue

        raise ValueError("Could not parse JSON from model response.")

    @staticmethod
    def _truncate(value: str, max_length: int, field_name: str, url: str) -> str:
        if len(value) <= max_length:
            return value
        LOGGER.warning(
            "Truncating %s for URL=%s from %s to %s chars",
            field_name,
            url,
            len(value),
            max_length,
        )
        return value[:max_length]
