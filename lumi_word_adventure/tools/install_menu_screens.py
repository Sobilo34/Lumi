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
}

# Source art that may include captured control overlays (home on CTA, speaker).
HOW_TO_PLAY_SOURCE = "image-52debc34-eca4-4544-8983-c0cbe0a30c0b.png"
HOW_TO_PLAY_DEST = "05_instruction_how_to_play.png"


def _resize(image: Image.Image) -> Image.Image:
    if image.size != TARGET_SIZE:
        return image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    return image


def _paste_clone(img: Image.Image, dst_box: tuple[int, int, int, int], src_box: tuple[int, int, int, int]) -> None:
    patch = img.crop(src_box).resize(
        (dst_box[2] - dst_box[0], dst_box[3] - dst_box[1]),
        Image.Resampling.LANCZOS,
    )
    img.paste(patch, (dst_box[0], dst_box[1]))


def _clean_how_to_play_overlay_icons(image: Image.Image) -> Image.Image:
    """Remove home/speaker controls baked into captured how-to-play art."""
    img = _resize(image.convert("RGB"))
    # Home icon on the Let's Go button.
    _paste_clone(img, (505, 590, 560, 645), (620, 590, 675, 645))
    # Speaker button and replay circle — sample the panel interior (not the OS taskbar).
    panel_fill = (600, 450, 700, 530)
    _paste_clone(img, (892, 575, 988, 670), panel_fill)
    _paste_clone(img, (910, 610, 990, 690), panel_fill)
    return img


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    print(f"Installing menu screens to {DEST}")
    for filename, source_name in SCREEN_SOURCES.items():
        src = CURSOR_ASSETS / source_name
        if not src.is_file():
            raise FileNotFoundError(f"Missing source for {filename}: {src}")
        image = Image.open(src).convert("RGB")
        image = _resize(image)
        dest = DEST / filename
        image.save(dest, compress_level=1)
        print(f"  {source_name} -> {filename} ({image.width}x{image.height})")

    src = CURSOR_ASSETS / HOW_TO_PLAY_SOURCE
    if not src.is_file():
        raise FileNotFoundError(f"Missing source for {HOW_TO_PLAY_DEST}: {src}")
    cleaned = _clean_how_to_play_overlay_icons(Image.open(src))
    dest = DEST / HOW_TO_PLAY_DEST
    cleaned.save(dest, compress_level=1)
    print(f"  {HOW_TO_PLAY_SOURCE} -> {HOW_TO_PLAY_DEST} ({cleaned.width}x{cleaned.height}, overlays stripped)")

    print(f"Installed {len(SCREEN_SOURCES) + 1} menu screens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
