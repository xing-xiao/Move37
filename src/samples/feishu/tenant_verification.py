"""Sample script to query Feishu tenant verification info."""

from __future__ import annotations

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
    """Read Feishu config from .env and print tenant verification info."""
    load_dotenv(PROJECT_ROOT / ".env")

    app_id = str(os.getenv("FEISHU_APP_ID", "")).strip()
    app_secret = str(os.getenv("FEISHU_APP_SECRET", "")).strip()

    client = FeishuClient(app_id=app_id, app_secret=app_secret)
    verification_info = client.get_tenant_verification_info()
    print(json.dumps(verification_info, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
