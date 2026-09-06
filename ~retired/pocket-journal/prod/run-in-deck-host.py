#!/usr/bin/env python3
"""My Pocket Journal → Deck Host"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROD = Path(__file__).resolve().parent
SYS = PROD / "journal_sys"
DECK = PROD.parents[2] / "the-deck-host" / "shell" / "deck_host.py"
PORT = os.environ.get("JOURNAL_PORT", "43166")
URL = f"http://127.0.0.1:{PORT}/"
HEALTH = f"http://127.0.0.1:{PORT}/api/health"


def main() -> int:
    if not (SYS / "server.py").is_file():
        print("server missing", file=sys.stderr)
        return 1
    if not DECK.is_file():
        print(f"Deck Host missing: {DECK}", file=sys.stderr)
        return 1
    w = os.environ.get("JOURNAL_WIDTH", "720")
    h = os.environ.get("JOURNAL_HEIGHT", "700")
    os.environ.setdefault(
        "DECK_HOST_EXPANDED_WIDTH", os.environ.get("JOURNAL_EXPANDED_WIDTH", "760")
    )
    os.environ.setdefault(
        "DECK_HOST_EXPANDED_HEIGHT", os.environ.get("JOURNAL_EXPANDED_HEIGHT", "920")
    )
    cmd = [
        sys.executable,
        str(DECK),
        "--title",
        "My Pocket Journal",
        "--profile",
        "desk",
        "--width",
        str(w),
        "--height",
        str(h),
        "--url",
        URL,
        "--health",
        HEALTH,
        "--health-timeout",
        "20",
        "--spawn",
        f"{sys.executable} server.py",
        "--spawn-cwd",
        str(SYS),
    ]
    print("My Pocket Journal · CO.MYPT-003-JOURNAL · Deck Host")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
