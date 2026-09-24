#!/usr/bin/env python3
"""My Pocket Go → Deck Host"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROD = Path(__file__).resolve().parent
SYS = PROD / "www_sys"
DECK = PROD.parents[2] / "the-deck-host" / "shell" / "deck_host.py"
PORT = os.environ.get("GO_PORT", os.environ.get("LIBRARY_PORT", "43210"))
os.environ.setdefault("GO_HOST", "0.0.0.0")
URL = f"http://127.0.0.1:{PORT}/"
HEALTH = f"http://127.0.0.1:{PORT}/api/health"


def main() -> int:
    if not (SYS / "server.py").is_file():
        print("server missing", file=sys.stderr)
        return 1
    if not DECK.is_file():
        print(f"Deck Host missing: {DECK}", file=sys.stderr)
        return 1
    # Microsite first: 800×600, then ⤢ steps to 1024×768.
    w = os.environ.get("GO_WIDTH", "800")
    h = os.environ.get("GO_HEIGHT", "600")
    os.environ.setdefault("DECK_HOST_EXPANDED_WIDTH", "1024")
    os.environ.setdefault("DECK_HOST_EXPANDED_HEIGHT", "768")
    cmd = [
        sys.executable,
        str(DECK),
        "--title",
        "My Pocket Go",
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
    print("My Pocket Go · CO.MYPT-004-GO · Deck Host")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
