"""Parse OPML source files into structured source lists."""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from typing import Dict, List

from lxml import etree

LOGGER = logging.getLogger(__name__)


def parse_opml(file_path: str | Path) -> List[Dict[str, str]]:
    """
    Parse an OPML file and return source entries.

    Output format:
    [
        {"sourceType": "Blogs", "xmlTitle": "...", "xmlUrl": "..."},
        ...
    ]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"OPML file not found: {path}")

    tree = etree.parse(str(path))
    outlines = tree.xpath("//body/outline")

    sources: List[Dict[str, str]] = []

    def walk(node: etree._Element, inherited_source_type: str | None = None) -> None:
        source_type = (
            node.attrib.get("sourceType")
            or node.attrib.get("source_type")
            or inherited_source_type
            or node.attrib.get("text")
            or node.attrib.get("title")
        )
        xml_url = node.attrib.get("xmlUrl") or node.attrib.get("xmlurl")
        xml_title = node.attrib.get("text") or node.attrib.get("title") or ""

        if xml_url:
            sources.append(
                {
                    "sourceType": source_type or "Unknown",
                    "xmlTitle": xml_title or xml_url,
                    "xmlUrl": xml_url,
                }
            )

        for child in node.xpath("./outline"):
            walk(child, source_type)

    for outline in outlines:
        walk(outline, None)

    stats = Counter(item["sourceType"] for item in sources)
    LOGGER.info("OPML解析完成，类型统计: %s", dict(stats))
    return sources

