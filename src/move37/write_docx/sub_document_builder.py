"""Sub document content builder for write-feishu-docx."""

from __future__ import annotations

from typing import Any, Dict, Optional


def is_blog_item(content_item: Dict[str, Any]) -> bool:
    """Infer blog-vs-youtube from source_type/url."""
    source_type = str(content_item.get("source_type") or "").lower()
    url = str(content_item.get("url") or "").lower()
    if "youtube" in source_type:
        return False
    if "youtube.com" in url or "youtu.be" in url:
        return False
    return True


def _escape_markdown(value: Any) -> str:
    text = str(value or "")
    # Keep escaping lightweight; enough to avoid accidental list/header breakage.
    for src, dst in [
        ("\\", "\\\\"),
        ("`", "\\`"),
    ]:
        text = text.replace(src, dst)
    return text


class SubDocumentBuilder:
    """Build markdown content for each content item sub-document."""

    @staticmethod
    def build_content(
        content_item: Dict[str, Any],
        translation_doc_url: Optional[str] = None,
        wechat_doc_url: Optional[str] = None,
    ) -> str:
        title = _escape_markdown(content_item.get("title") or "无标题")
        source_title = _escape_markdown(content_item.get("source_title") or "未知来源")
        url = _escape_markdown(content_item.get("url") or "")
        published = _escape_markdown(content_item.get("published") or "")
        tokens = int(content_item.get("tokens_consumed") or 0)
        brief = _escape_markdown(content_item.get("brief") or "无简介内容")
        summary = _escape_markdown(content_item.get("summary") or "无总结内容")
        success = bool(content_item.get("success", False))
        error = _escape_markdown(content_item.get("error") or "")

        if success:
            status = "成功"
        else:
            status = "失败"
            if error:
                summary = f"{summary}\n\n失败原因：{error}" if summary else f"失败原因：{error}"

        lines = [
            "## 1 文章标题",
            f"### {title}",
            f"* 来源：{source_title}",
            f"* 原文链接：{url}",
            f"* 发布时间：{published}",
            f"* 消耗Token：{tokens}个",
            f"* 文章简介：{brief}",
            f"* 处理结果：{status}",
            "",
            "## 2 文章总结",
            "",
            summary,
        ]

        if is_blog_item(content_item):
            translated_link = _escape_markdown(translation_doc_url or "待生成")
            wechat_link = _escape_markdown(wechat_doc_url or "待生成")
            lines.extend(
                [
                    "",
                    "## 3 翻译文章",
                    "",
                    translated_link,
                    "",
                    "## 4 生成公众号文章",
                    "",
                    wechat_link,
                ]
            )

        return "\n".join(lines)
