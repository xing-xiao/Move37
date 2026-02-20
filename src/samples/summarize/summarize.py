"""CLI entry point for content summarization demo."""

from __future__ import annotations

import argparse
import copy
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.summarize.config import ConfigurationError  # noqa: E402
from move37.summarize.summarizer import summarize_all  # noqa: E402

SAMPLE_COLLECTION_RESULT: Dict[str, Any] = {
    "collection_date": "2026-02-20",
    "target_date": "2026-02-19",
    "results": [
        {
      "source_type": "Blogs",
      "source_title": "fabiensanglard.net",
      "success": True,
      "items": [
        {
          "title": "How Michael Abrash doubled Quake framerate",
          "url": "https://fabiensanglard.net/quake_asm_optimizations/index.html",
          "published": "2026-02-14T00:00:00Z"
        }
      ]
    },
        {
            "source_type": "YouTube Channels",
            "source_title": "OpenAI YouTube",
            "success": True,
            "items": [
                {
                    "title": "Example YouTube Video",
                    "url": "https://www.youtube.com/watch?v=EvtPBaaykdo",
                    "published": "2026-02-19T12:00:00Z",
                }
            ],
        },
    ],
}


def _build_override_config(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    config: Dict[str, Any] = {}
    if args.provider:
        config["provider"] = args.provider
    if args.model:
        config["model"] = args.model
    if args.api_key:
        config["api_key"] = args.api_key
    return config or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run summarize_all with sample payload.")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "deepseek", "gemini", "glm"],
        default=None,
        help="Override LLM provider from .env",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model from .env",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Override API key from .env",
    )
    parser.add_argument(
        "--url",
        type=str,
        default=None,
        help="Override the first sample URL.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    sample_payload = copy.deepcopy(SAMPLE_COLLECTION_RESULT)
    if args.url:
        sample_payload["results"][0]["items"][0]["url"] = args.url

    override_config = _build_override_config(args)
    try:
        result = summarize_all(sample_payload, config=override_config)
    except ConfigurationError as exc:
        parser.error(str(exc))
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
