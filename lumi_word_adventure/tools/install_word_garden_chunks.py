#!/usr/bin/env python3
"""Install Word Garden assets: background, object cards, and word prompt PNGs."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from engine.asset_manager import (
    _crop_to_opaque_bbox,
    _extract_word_object_illustration,
    _knock_out_export_padding,
    _knock_out_light_backdrop,
    _process_word_garden_object,
    write_shipped_assets_marker,
)

ASSETS = Path("/home/bilal/.cursor/projects/home-bilal-bilal-projects-Learning-AIU-python-Lumi/assets")
DEST = PROJECT / "assets" / "ui_chunks" / "word_garden_game"

BACKGROUND_FILE = "image-285d73a5-cb3c-481d-98d4-c5fcb4c1de98.png"
SUCCESS_BACKGROUND_FILE = "image-d720d304-07b9-4a8f-bbd9-550aeb8001fb.png"
FAILURE_BACKGROUND_FILE = "image-04e89b03-c223-46a3-b1a2-3ca4886ce06c.png"
SPEAK_BACKGROUND_FILE = "image-47d4bf35-7631-430f-bea0-e2f3963c25e2.png"

OBJECT_FILES: dict[str, str] = {
    "cat": "image-c58d2e7e-4f4f-41e5-8da0-8739214352f3.png",
    "dog": "image-8b736f82-46fe-46d7-888b-246c1e0ec672.png",
    "sun": "image-e2455ce6-8242-4c70-bdd1-bf771ece3bc0.png",
    "ball": "image-36ca1ce7-533f-481c-aa15-37d2b3364e92.png",
    "hat": "image-1de74328-3ff2-429d-95f2-db66081c3408.png",
    "fish": "image-87690f29-dfc8-4806-955c-7487363f7a43.png",
    "tree": "image-b2a03122-1341-4f75-9673-138c34e57334.png",
    "apple": "image-98a9feea-b7f7-49d1-a909-01dbda0f4cec.png",
    "bird": "image-41d77c1c-b65e-467c-a1b8-9d24f11a083c.png",
    "cup": "image-a75ae720-068e-449a-a0fc-ca3443987c04.png",
    "frog": "image-2f7f2634-f373-43ca-80a8-b88b4b6c3e55.png",
    "star": "image-dbc166b8-fb1e-4ce4-afbd-af5fd465452f.png",
    "duck": "image-48d68d0b-1a8c-4788-b0aa-036d4fef163b.png",
}

PROMPT_FILES: dict[str, str] = {
    "cat": "image-87196ff7-62e6-4130-a511-3cb247813ed7.png",
    "dog": "image-cf9fe5a2-3ee8-474e-82a2-0334f613f2fe.png",
    "sun": "image-48b2922b-d25e-42bc-a998-538d7e8aea7f.png",
    "ball": "image-96aa428c-d9f2-4b7a-a041-c85e2814ea44.png",
    "hat": "image-f9878cac-6aa0-4154-b6d0-42e177139c34.png",
    "fish": "image-3ec88c9c-ad8f-45ca-b036-e47caa1d01a9.png",
    "tree": "image-e32e07ac-0c34-4493-b147-cbbcb8b6503e.png",
    "apple": "image-e2200405-7515-42f6-ad82-017f90bfcf0a.png",
    "bird": "image-2149ac9e-e82c-4392-8188-db0380815997.png",
    "cup": "image-57331544-23fd-4983-9d8b-8538ff76c4c8.png",
    "frog": "image-3ee9b3fc-09c3-42d6-8a00-96310799a43b.png",
    "star": "image-6f9c510f-b1ee-43e2-a3c3-16faf33f940c.png",
    "duck": "image-ff3beb20-c004-4229-b5f5-f4dc2c58eee8.png",
}


def _copy(src_name: str, dest: Path, *, process: bool = False, crop: bool = False) -> None:
    src = ASSETS / src_name
    if not src.is_file():
        raise FileNotFoundError(f"Missing asset: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if process:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))
        image = pygame.image.load(str(src))
        if image.get_alpha() is not None:
            image = image.convert_alpha()
        else:
            image = image.convert()
        image = _knock_out_export_padding(image)
        if crop:
            image = _extract_word_object_illustration(image)
        elif "objects" in dest.as_posix().replace("\\", "/"):
            image = _process_word_garden_object(image)
        else:
            image = _crop_to_opaque_bbox(_knock_out_light_backdrop(image))
        pygame.image.save(image, str(dest))
    else:
        shutil.copy2(src, dest)
    print(f"  -> {dest.relative_to(PROJECT)}")


def main() -> None:
    print(f"Installing Word Garden chunks to {DEST}")
    _copy(BACKGROUND_FILE, DEST / "background.png")
    _copy(SUCCESS_BACKGROUND_FILE, DEST / "success_background.png")
    _copy(FAILURE_BACKGROUND_FILE, DEST / "failure_background.png")
    _copy(SPEAK_BACKGROUND_FILE, DEST / "speak_background.png")
    for word, filename in OBJECT_FILES.items():
        _copy(filename, DEST / "objects" / f"{word}.png", process=True, crop=False)
    for word, filename in PROMPT_FILES.items():
        _copy(filename, DEST / "prompts" / f"{word}.png", process=True)
    write_shipped_assets_marker(DEST.parent, "word_garden_game")
    print("Done.")


if __name__ == "__main__":
    main()
