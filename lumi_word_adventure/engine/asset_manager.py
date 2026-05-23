"""Reusable asset loading and caching helpers."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


class AssetManager:
    def __init__(self, reference_dir: Path | None = None) -> None:
        self.reference_dir = Path(reference_dir) if reference_dir is not None else REFERENCE_INTERFACES_DIR
        self._image_cache: dict[str, pygame.Surface] = {}

    def load_image(self, filename: str) -> pygame.Surface:
        if filename not in self._image_cache:
            image_path = self.reference_dir / filename
            image = pygame.image.load(str(image_path))
            if pygame.display.get_surface() is not None:
                if image.get_alpha() is not None:
                    image = image.convert_alpha()
                else:
                    image = image.convert()
            self._image_cache[filename] = pygame.transform.smoothscale(
                image,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
            )
        return self._image_cache[filename]
