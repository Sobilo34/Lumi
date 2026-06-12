"""Reusable asset loading and caching helpers."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import BABY_PINK, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH


class AssetManager:
    def __init__(self, reference_dir: Path | None = None) -> None:
        self.reference_dir = Path(reference_dir) if reference_dir is not None else REFERENCE_INTERFACES_DIR
        self._image_cache: dict[str, pygame.Surface] = {}
        self._missing_images: set[str] = set()

    def _placeholder_surface(self, filename: str) -> pygame.Surface:
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        surface.fill(pygame.Color(BABY_PINK))
        if filename not in self._missing_images:
            self._missing_images.add(filename)
            print(
                f"[Lumi Assets] Missing reference image '{filename}' "
                f"in {self.reference_dir}. Using baby-pink placeholder."
            )
        return surface

    def load_image(self, filename: str) -> pygame.Surface:
        if filename not in self._image_cache:
            image_path = self.reference_dir / filename
            if not image_path.is_file():
                self._image_cache[filename] = self._placeholder_surface(filename)
                return self._image_cache[filename]

            try:
                image = pygame.image.load(str(image_path))
            except (pygame.error, FileNotFoundError, OSError) as error:
                print(f"[Lumi Assets] Failed to load '{filename}': {error}")
                self._image_cache[filename] = self._placeholder_surface(filename)
                return self._image_cache[filename]

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
