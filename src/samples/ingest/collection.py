"""CLI entry point for data ingest collection."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.ingest.collection import collect_all  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect blog and YouTube links by date.")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date in YYYY-MM-DD. Default is yesterday (UTC).",
    )
    parser.add_argument(
        "--opml",
        type=str,
        default=None,
        help="Optional OPML file path. Default: src/move37/sources/rss.opml",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    try:
        results = collect_all(target_date=args.date, opml_path=args.opml)
    except ValueError as exc:
        parser.error(str(exc))
        return

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

