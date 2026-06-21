#!/usr/bin/env python3
"""Install Level Complete button PNGs with transparent backgrounds."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from engine.letter_tile_bg import knock_out_letter_backdrop  # noqa: E402

CURSOR_ASSETS = Path.home() / ".cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets"
DEST = PROJECT_DIR / "assets" / "ui_chunks" / "progress_complete"

BUTTONS: dict[str, str] = {
    "next_world.png": "image-5711e420-10ae-4c46-9035-25ed9c51d095.png",
    "practice_again.png": "image-b82cefa9-aed6-433a-b68d-29a700c229be.png",
    "view_report.png": "image-d691838c-736d-4faf-87cc-bd50f208247b.png",
}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    for dest_name, src_name in BUTTONS.items():
        src = CURSOR_ASSETS / src_name
        if not src.is_file():
            print(f"Missing source: {src}", file=sys.stderr)
            return 1
        knock_out_letter_backdrop(Image.open(src)).save(DEST / dest_name, compress_level=1)
        print(f"  installed {dest_name}")
    print(f"Installed {len(BUTTONS)} buttons into {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
