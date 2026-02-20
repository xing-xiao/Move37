"""Article translator for blog content."""

from __future__ import annotations

import logging
from typing import List

from move37.summarize.llm_client import LLMClient

from .errors import LLMError

LOGGER = logging.getLogger(__name__)

TRANSLATION_PROMPT_TEMPLATE = """
你将收到一段英文文章内容。请严格返回 JSON：
{
  "brief": "可留空",
  "summary": "该段内容的中文翻译"
}

要求：
1. 只返回 JSON
2. summary 字段只包含中文翻译，不要额外解释

URL: {url}
内容:
{content}
""".strip()


class ArticleTranslator:
    """Translate article content paragraph by paragraph using LLM."""

    def __init__(self, llm_client: LLMClient, max_paragraphs: int = 12) -> None:
        self.llm_client = llm_client
        self.max_paragraphs = max(1, int(max_paragraphs))

    def translate_article(self, content: str) -> str:
        """Return bilingual markdown with original paragraph followed by translation."""
        raw_text = str(content or "").strip()
        if not raw_text:
            raise LLMError("Cannot translate empty article content.")

        paragraphs = self._split_paragraphs(raw_text)[: self.max_paragraphs]
        if not paragraphs:
            raise LLMError("No valid paragraph found for translation.")

        lines: List[str] = []
        for index, paragraph in enumerate(paragraphs, start=1):
            result = self.llm_client.generate_summary(
                url="about:blog-translation",
                prompt_template=TRANSLATION_PROMPT_TEMPLATE,
                content=paragraph,
            )
            if not result.get("success"):
                error = str(result.get("error") or "unknown LLM error")
                raise LLMError(f"Paragraph {index} translation failed: {error}")

            translated_text = str(result.get("summary") or "").strip()
            if not translated_text:
                raise LLMError(f"Paragraph {index} translation returned empty content.")

            lines.extend(
                [
                    f"### 段落 {index} 原文",
                    paragraph,
                    "",
                    f"### 段落 {index} 译文",
                    translated_text,
                    "",
                ]
            )

        LOGGER.info("Article translation finished paragraphs=%s", len(paragraphs))
        return "\n".join(lines).strip()

    @staticmethod
    def _split_paragraphs(content: str) -> List[str]:
        blocks = [part.strip() for part in content.split("\n\n")]
        return [part for part in blocks if len(part) >= 20]
