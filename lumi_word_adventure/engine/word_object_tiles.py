"""Word Garden object tile validation (boxed tiles only)."""
from __future__ import annotations

from pathlib import Path

from config import PROJECT_DIR

OBJECT_TILE_SIZE = (1024, 1024)

# Shipped boxed object words (no cat/dog/ball — those lack card frames).
BOXED_WORD_GARDEN_WORDS: tuple[str, ...] = (
    "sun",
    "fish",
    "apple",
    "bird",
    "cup",
    "frog",
    "duck",
    "hat",
    "star",
    "tree",
)


def is_boxed_object_tile_path(path: Path | str) -> bool:
    """True when PNG is a full card tile: 1024² with transparent outer corners."""
    try:
        from PIL import Image
    except ImportError:
        return False
    image_path = Path(path)
    if not image_path.is_file():
        return False
    with Image.open(image_path) as image:
        if image.size != OBJECT_TILE_SIZE:
            return False
        rgba = image.convert("RGBA")
        w, h = rgba.size
        corners = (
            rgba.getpixel((0, 0))[3],
            rgba.getpixel((w - 1, 0))[3],
            rgba.getpixel((0, h - 1))[3],
            rgba.getpixel((w - 1, h - 1))[3],
        )
        return all(alpha == 0 for alpha in corners)


def word_garden_objects_dir(chunks_root: Path | str | None = None) -> Path:
    default = PROJECT_DIR / "assets" / "ui_chunks" / "word_garden_game" / "objects"
    if chunks_root is None:
        return default
    root = Path(chunks_root)
    if root.is_absolute():
        if root.name == "objects" and root.is_dir():
            return root
        nested = root / "objects"
        if nested.is_dir():
            return nested
    screen_objects = PROJECT_DIR / "assets" / "ui_chunks" / root.name / "objects"
    if screen_objects.is_dir():
        return screen_objects
    nested = root / "objects"
    if nested.is_dir():
        return nested
    return default
