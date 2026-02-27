"""Build Feishu notification message from summarize result."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from .errors import DataParseError


def _to_int(value: Any) -> int:
    if value is None or isinstance(value, bool):
        return 0
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return 0


def _iter_items(summary_result: Dict[str, Any]) -> Iterable[Tuple[Dict[str, Any], Dict[str, Any]]]:
    results = summary_result.get("results", [])
    if not isinstance(results, list):
        raise DataParseError("`summary_result.results` must be a list.")

    for source in results:
        if not isinstance(source, dict):
            continue
        items = source.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                yield source, item


def build_message(summary_result: Dict[str, Any], statistics: Dict[str, Any]) -> str:
    """Construct Feishu message body."""
    if not isinstance(summary_result, dict):
        raise DataParseError("`summary_result` must be a dictionary.")
    if not isinstance(statistics, dict):
        raise DataParseError("`statistics` must be a dictionary.")

    total_count = _to_int(statistics.get("total_count"))
    success_count = _to_int(statistics.get("success_count"))
    failure_count = _to_int(statistics.get("failure_count"))
    total_time_minutes = _to_int(statistics.get("total_time_minutes"))
    total_time_seconds = _to_int(statistics.get("total_time_seconds"))
    total_tokens = _to_int(statistics.get("total_tokens"))
    models_used = sorted(
        {
            str(item.get("model_used") or "").strip()
            for _, item in _iter_items(summary_result)
            if str(item.get("model_used") or "").strip()
        }
    )

    collection_date = str(summary_result.get("collection_date") or "").strip()
    target_date = str(summary_result.get("target_date") or "").strip()
    wiki_url = str(
        summary_result.get("wiki_url")
        or summary_result.get("wiki_node_url")
        or summary_result.get("wiki_doc_url")
        or summary_result.get("url")
        or ""
    ).strip()

    lines = [
        "## Move37今日安全咨询概览",
        f"- 为您提供文章咨询：{total_count}个，处理成功{success_count}个，处理失败{failure_count}个",
        f"- 程序执行耗时：{total_time_minutes}分{total_time_seconds}秒",
        f"- 消耗Token：{total_tokens}个",
    ]
    if models_used:
        lines.append(f"- 使用模型：{', '.join(models_used)}")
    if wiki_url:
        lines.append(f"- 详情请查看飞书wiki：{wiki_url}")
    if target_date:
        lines.append(f"- 文章发表日期：{target_date}")

    lines.append("")
    lines.append("## 文章清单")

    item_count = 0
    for source, item in _iter_items(summary_result):
        item_count += 1
        source_title = str(source.get("source_title") or "Unknown").strip()
        source_type = str(source.get("source_type") or "").strip()
        source_label = source_title
        if source_type:
            source_label = f"{source_title} ({source_type})"

        title = str(item.get("title") or "未命名内容").strip()
        url = str(item.get("url") or "").strip() or "N/A"
        tokens_consumed = _to_int(item.get("tokens_consumed"))
        success = bool(item.get("success"))
        error = str(item.get("error") or "").strip()
        brief = str(item.get("brief") or "").strip()

        if not brief:
            brief = "（空）" if success else "处理失败，未生成简介。"
        if not success and error:
            brief = f"{brief}（失败原因：{error}）"

        status_text = "成功" if success else "失败"

        lines.extend(
            [
                f"- {title}",
                f"  * 文章简介：{brief}",
                f"  * 原文链接：{url}",
                f"  * 处理结果：{status_text}，消耗Token：{tokens_consumed}个",
            ]
        )

    if item_count == 0:
        lines.append("- 无可用条目")

    return "\n".join(lines)
