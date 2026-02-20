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

    collection_date = str(summary_result.get("collection_date") or "").strip()
    target_date = str(summary_result.get("target_date") or "").strip()

    lines = [
        "## 执行结果总结",
        f"- 处理文章/视频数：{total_count}个，成功{success_count}个，失败{failure_count}个",
        f"- 执行时间：{total_time_minutes}分{total_time_seconds}秒",
        f"- 消耗Token：{total_tokens}个",
    ]
    if target_date:
        lines.append(f"- 目标日期：{target_date}")
    if collection_date:
        lines.append(f"- 收集日期：{collection_date}")

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
                f"  * 来源：{source_label}",
                f"  * 原文链接：{url}",
                f"  * 消耗Token：{tokens_consumed}个",
                f"  * 文章简介：{brief}",
                f"  * 处理结果：{status_text}",
            ]
        )

    if item_count == 0:
        lines.append("- 无可用条目")

    return "\n".join(lines)
