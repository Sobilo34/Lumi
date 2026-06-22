#!/usr/bin/env python3
"""Install Word Garden object tiles — backdrop removal only, box intact, uniform canvas."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from engine.letter_tile_bg import knock_out_letter_backdrop  # noqa: E402
from engine.asset_manager import write_shipped_assets_marker  # noqa: E402

CURSOR_ASSETS = Path.home() / ".cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets"
DEST = PROJECT_DIR / "assets" / "ui_chunks" / "word_garden_game" / "objects"
CANVAS = (1024, 1024)
MARGIN = 40

# New user uploads (Sun, Fish, Apple, Bird, Cup, Frog, Duck, Hat).
NEW_OBJECT_FILES: dict[str, str] = {
    "sun": "image-25fb8f5d-aa4a-4b33-867b-0836f91d1ea6.png",
    "fish": "image-e19b75e6-4959-4bdd-a06d-58afb4134efc.png",
    "apple": "image-9dad1f18-8544-4475-9aad-030479aa8f18.png",
    "bird": "image-3303bdce-836b-4c29-ae82-a9c99ecbdb08.png",
    "cup": "image-a7a8ea0d-9ba3-4755-9368-ace084020855.png",
    "frog": "image-c18336ea-b505-4eb2-9194-ad917f491986.png",
    "duck": "image-ec275402-d8e0-4143-9d62-d8e8a4fe3262.png",
    "hat": "image-488d1101-6480-481e-b1bb-ba18f01b6000.png",
}

# Re-process with the same pipeline until new art is supplied.
LEGACY_OBJECT_FILES: dict[str, str] = {
    "star": "image-dbc166b8-fb1e-4ce4-afbd-af5fd465452f.png",
    "tree": "image-b2a03122-1341-4f75-9673-138c34e57334.png",
}


def _normalize_canvas(image: Image.Image) -> Image.Image:
    cleaned = knock_out_letter_backdrop(image.convert("RGBA"))
    bbox = cleaned.getbbox()
    if not bbox:
        return Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    tile = cleaned.crop(bbox)
    canvas_w, canvas_h = CANVAS
    max_w = canvas_w - MARGIN * 2
    max_h = canvas_h - MARGIN * 2
    scale = min(max_w / tile.width, max_h / tile.height)
    if scale < 0.999:
        tile = tile.resize(
            (max(1, int(tile.width * scale)), max(1, int(tile.height * scale))),
            Image.Resampling.LANCZOS,
        )
    out = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    x = (canvas_w - tile.width) // 2
    y = (canvas_h - tile.height) // 2
    out.paste(tile, (x, y), tile)
    return out


def _install_word(word: str, src_name: str) -> None:
    src = CURSOR_ASSETS / src_name
    if not src.is_file():
        raise FileNotFoundError(f"Missing source for {word}: {src}")
    dest = DEST / f"{word}.png"
    dest.parent.mkdir(parents=True, exist_ok=True)
    _normalize_canvas(Image.open(src)).save(dest, compress_level=1)
    print(f"  {word}: {src_name} -> {dest.name} ({CANVAS[0]}x{CANVAS[1]})")


def main() -> int:
    print(f"Installing Word Garden object tiles to {DEST}")
    for word, filename in NEW_OBJECT_FILES.items():
        _install_word(word, filename)
    for word, filename in LEGACY_OBJECT_FILES.items():
        _install_word(word, filename)
    marker = DEST.parent / ".shipped_ready"
    marker.write_text("word_object_tiles_v2\n", encoding="utf-8")
    write_shipped_assets_marker(PROJECT_DIR / "assets" / "ui_chunks", "word_garden_game")
    print(f"Installed {len(NEW_OBJECT_FILES) + len(LEGACY_OBJECT_FILES)} object tiles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
