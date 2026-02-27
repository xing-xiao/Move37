"""Sample script to create a Feishu wiki DOCX node."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from move37.utils.feishu import FeishuClient


def main() -> None:
    """Read Feishu config from .env and create a wiki docx node."""
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Create a Feishu wiki DOCX node.")
    parser.add_argument("--node-name", default="origin", help="Wiki node name.")
    parser.add_argument("--title", default="", help="Docx title; defaults to node name.")
    parser.add_argument(
        "--space-id",
        default=str(os.getenv("FEISHU_WIKI_SPACE_ID", "")).strip(),
        help="Wiki space id; defaults to FEISHU_WIKI_SPACE_ID.",
    )
    parser.add_argument(
        "--parent-node-token",
        default=str(os.getenv("FEISHU_WIKI_PARENT_NODE_TOKEN", "")).strip(),
        help="Parent node token; defaults to FEISHU_WIKI_PARENT_NODE_TOKEN.",
    )
    args = parser.parse_args()

    app_id = str(os.getenv("FEISHU_APP_ID", "")).strip()
    app_secret = str(os.getenv("FEISHU_APP_SECRET", "")).strip()

    client = FeishuClient(app_id=app_id, app_secret=app_secret)
    created = client.create_docx(
        space_id=args.space_id,
        node_name=args.node_name,
        parent_node_token=args.parent_node_token or None,
        title=args.title or None,
    )
    print(json.dumps(created, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
