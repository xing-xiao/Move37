"""Compatibility CLI wrapper.

Usage:
    python samples/ingest/collection.py --date 2026-02-17
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from samples.ingest.collection import main  # type: ignore  # noqa: E402


if __name__ == "__main__":
    main()

