"""WeChat-style article generator for blog content."""

from __future__ import annotations

import logging

from move37.summarize.llm_client import LLMClient

from .errors import LLMError

LOGGER = logging.getLogger(__name__)

WECHAT_PROMPT_TEMPLATE = """
你是一个 AI 咨询类公众号编辑。请基于提供内容生成可直接发布的中文文章。
严格返回 JSON：
{
  "brief": "文章标题（30字以内）",
  "summary": "公众号正文（分段，1000字以内）"
}

要求：
1. 内容结构清晰，包含引言、核心观点、落地建议
2. 不要出现 JSON 之外的额外文本

URL: {url}
内容:
{content}
""".strip()


class WeChatArticleGenerator:
    """Generate WeChat-style article from blog content."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate_wechat_article(self, content: str) -> str:
        """Generate formatted markdown for WeChat article."""
        raw_text = str(content or "").strip()
        if not raw_text:
            raise LLMError("Cannot generate WeChat article from empty content.")

        result = self.llm_client.generate_summary(
            url="about:wechat-article",
            prompt_template=WECHAT_PROMPT_TEMPLATE,
            content=raw_text[:16000],
        )
        if not result.get("success"):
            error = str(result.get("error") or "unknown LLM error")
            raise LLMError(f"WeChat article generation failed: {error}")

        title = str(result.get("brief") or "AI 咨询速览").strip()
        body = str(result.get("summary") or "").strip()
        if not body:
            raise LLMError("WeChat article generation returned empty body.")

        LOGGER.info("WeChat article generation finished title=%s", title)
        return f"# {title}\n\n{body}"
