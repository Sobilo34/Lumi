#!/usr/bin/env python3
"""Install shared UI control art — backdrop removal, transparent PNGs."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from engine.letter_tile_bg import knock_out_letter_backdrop  # noqa: E402

CURSOR_ASSETS = Path.home() / ".cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets"
DEST = PROJECT_DIR / "assets" / "ui_controls"

# User uploads in order: home, letter island, word garden, writing castle,
# repeat, hint, speaker, settings, skip, mic.
CONTROL_SOURCES: dict[str, str] = {
    "home": "image-b58285ec-1d67-426c-86cc-5f4e8aeef516.png",
    "letter_island_world": "image-9ab08cc5-15ae-4b26-a417-02ad09433327.png",
    "word_garden_world": "image-cc0fabb2-1ea8-419b-a904-a4090de65569.png",
    "writing_castle_world": "image-9648cc95-a044-4366-a691-aa5be5a91c2f.png",
    "repeat": "image-f03f367d-0f0c-4bc6-af86-4894ddc478ae.png",
    "hint": "image-ed6dfdbf-0b98-4a35-a206-5e48699bc055.png",
    "speaker": "image-b0bb906a-f710-4174-9d0b-fdff91a7bc51.png",
    "settings": "image-6823fc1e-c0ce-42e8-87d9-8804173cf580.png",
    "skip": "image-0f085657-9e27-430f-999e-9b6bedc5bc59.png",
    "mic": "image-7c72c42c-51b8-44f8-8c2e-42d6950c19a2.png",
    "verify": "image-88ca6be3-05f3-4b52-b07b-36fbe1272c24.png",
    "clear": "image-64d0d1ec-94f8-418b-b375-9238aa7df7d7.png",
    "switch_to_letters": "image-bc958503-1f63-4b1f-882e-1a06ae28b8e6.png",
    "switch_to_word": "image-ef83155a-8d79-4673-a588-3c28c23f0056.png",
}


def _process(src: Path) -> Image.Image:
    image = knock_out_letter_backdrop(Image.open(src).convert("RGBA"))
    bbox = image.getbbox()
    if not bbox:
        return image
    return image.crop(bbox)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Installing UI controls to {DEST}")
    for name, filename in CONTROL_SOURCES.items():
        src = CURSOR_ASSETS / filename
        if not src.is_file():
            raise FileNotFoundError(f"Missing source for {name}: {src}")
        out = _process(src)
        dest = DEST / f"{name}.png"
        out.save(dest, compress_level=1)
        print(f"  {name}: {out.width}x{out.height} -> {dest.name}")
    marker = DEST / ".shipped_ready"
    marker.write_text("ui_controls_v2\n", encoding="utf-8")
    print(f"Installed {len(CONTROL_SOURCES)} control images.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
