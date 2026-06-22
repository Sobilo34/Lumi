#!/usr/bin/env python3
"""Install full-screen menu art into reference_interfaces (1280x720)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
DEST = WORKSPACE_DIR / "reference_interfaces"
CURSOR_ASSETS = Path.home() / ".cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets"
TARGET_SIZE = (1280, 720)

SCREEN_SOURCES: dict[str, str] = {
    "04_main_menu.png": "image-feafc8b6-7202-4e29-86e0-978e7f0cbf10.png",
    "05_instruction_how_to_play.png": "image-52debc34-eca4-4544-8983-c0cbe0a30c0b.png",
}


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Installing menu screens to {DEST}")
    for filename, source_name in SCREEN_SOURCES.items():
        src = CURSOR_ASSETS / source_name
        if not src.is_file():
            raise FileNotFoundError(f"Missing source for {filename}: {src}")
        image = Image.open(src).convert("RGB")
        if image.size != TARGET_SIZE:
            image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        dest = DEST / filename
        image.save(dest, compress_level=1)
        print(f"  {source_name} -> {filename} ({image.width}x{image.height})")
    print(f"Installed {len(SCREEN_SOURCES)} menu screens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
