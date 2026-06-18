"""One-time preprocess: trim chunk PNG padding and write assets/ui_chunks/.trim_cache/."""
from __future__ import annotations

import sys
from pathlib import Path

import pygame

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import UI_CHUNKS_DIR
from engine.asset_manager import AssetManager


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1))
    assets = AssetManager(chunks_dir=UI_CHUNKS_DIR)
    total = 0
    for screen_dir in sorted(UI_CHUNKS_DIR.iterdir()):
        if not screen_dir.is_dir() or screen_dir.name.startswith("."):
            continue
        for png in sorted(screen_dir.glob("*.png")):
            if png.name == "background.png":
                continue
            assets.load_chunk(screen_dir.name, png.name)
            total += 1
            print(f"trimmed {screen_dir.name}/{png.name}")
    print(f"Done. {total} chunks cached under {UI_CHUNKS_DIR / '.trim_cache'}")


if __name__ == "__main__":
    main()
