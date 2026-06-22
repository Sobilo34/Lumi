#!/usr/bin/env python3
"""Install looping background music from a source MP3 into assets/sounds/."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DEST = PROJECT_DIR / "assets" / "sounds" / "background.mp3"
DEFAULT_SOURCE = Path.home() / "Downloads" / "VID_20260622_214554.mp3"


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.is_file():
        raise SystemExit(f"Missing source audio: {source}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, DEST)
    print(f"Installed background music: {source} -> {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
