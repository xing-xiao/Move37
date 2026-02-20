"""Blog article content extractor."""

from __future__ import annotations

import logging
from typing import List

import requests
from bs4 import BeautifulSoup

from .errors import ContentExtractionError

LOGGER = logging.getLogger(__name__)


class ContentExtractor:
    """Extract readable article text from HTML pages."""

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = float(timeout)

    def extract_article_content(self, url: str) -> str:
        """Extract article content as plain text from URL."""
        target_url = str(url or "").strip()
        if not target_url:
            raise ContentExtractionError("Article URL is empty.")

        try:
            response = requests.get(
                target_url,
                timeout=self.timeout,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                },
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ContentExtractionError(f"Failed to fetch article URL: {exc}") from exc

        soup = BeautifulSoup(response.text, "lxml")

        # Remove typical noisy blocks before extraction.
        for selector in ["script", "style", "nav", "footer", "header", "aside"]:
            for node in soup.select(selector):
                node.extract()

        content_root = (
            soup.find("article")
            or soup.find("main")
            or soup.find("section")
            or soup.body
        )
        if content_root is None:
            raise ContentExtractionError("Failed to locate HTML content body.")

        paragraphs: List[str] = []
        for tag in content_root.find_all(["h1", "h2", "h3", "p", "li"]):
            text = " ".join(tag.get_text(" ", strip=True).split())
            if len(text) >= 20:
                paragraphs.append(text)

        if not paragraphs:
            text = " ".join(content_root.get_text(" ", strip=True).split())
            if len(text) < 20:
                raise ContentExtractionError("Extracted article content is empty.")
            paragraphs = [text]

        # Guardrail to avoid oversized prompt payloads.
        content = "\n\n".join(paragraphs)
        return content[:20000]
