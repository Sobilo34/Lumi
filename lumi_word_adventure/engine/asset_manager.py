"""Reusable asset loading and caching helpers."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import BABY_PINK, REFERENCE_INTERFACES_DIR, SCREEN_HEIGHT, SCREEN_WIDTH, UI_CHUNKS_DIR


def _is_flat_backdrop(r: int, g: int, b: int, a: int) -> bool:
    if a < 10:
        return True
    peak = max(r, g, b)
    if peak - min(r, g, b) < 28 and peak > 195:
        return True
    return False


def _find_content_bbox(surface: pygame.Surface) -> tuple[int, int, int, int] | None:
    width, height = surface.get_size()
    min_x, min_y, max_x, max_y = width, height, 0, 0
    found = False
    step = 3
    for y in range(0, height, step):
        for x in range(0, width, step):
            color = surface.get_at((x, y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                continue
            found = True
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if not found:
        return None
    min_x = max(0, min_x - 6)
    min_y = max(0, min_y - 6)
    max_x = min(width - 1, max_x + 6)
    max_y = min(height - 1, max_y + 6)
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            color = surface.get_at((x, y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    return min_x, min_y, max_x - min_x + 1, max_y - min_y + 1


def _trim_flat_backdrop(image: pygame.Surface) -> pygame.Surface:
    """Remove flat gray/white export padding from chunked PNGs."""
    surface = image.convert_alpha()
    bbox = _find_content_bbox(surface)
    if bbox is None:
        return surface
    min_x, min_y, bw, bh = bbox
    trimmed = pygame.Surface((bw, bh), pygame.SRCALPHA)
    for y in range(bh):
        for x in range(bw):
            color = surface.get_at((min_x + x, min_y + y))
            if _is_flat_backdrop(color.r, color.g, color.b, color.a):
                trimmed.set_at((x, y), (0, 0, 0, 0))
            else:
                trimmed.set_at((x, y), color)
    return trimmed


class AssetManager:
    def __init__(
        self,
        reference_dir: Path | None = None,
        chunks_dir: Path | None = None,
    ) -> None:
        self.reference_dir = Path(reference_dir) if reference_dir is not None else REFERENCE_INTERFACES_DIR
        self.chunks_dir = Path(chunks_dir) if chunks_dir is not None else UI_CHUNKS_DIR
        self._image_cache: dict[str, pygame.Surface] = {}
        self._chunk_cache: dict[str, pygame.Surface | None] = {}
        self._scaled_cache: dict[str, pygame.Surface] = {}
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

    def _prepare_surface(self, image: pygame.Surface) -> pygame.Surface:
        if pygame.display.get_surface() is not None:
            if image.get_alpha() is not None:
                return image.convert_alpha()
            return image.convert()
        return image

    def scaled_chunk(
        self,
        screen_id: str,
        filename: str,
        width: int,
        height: int,
        *,
        fit: str = "contain",
    ) -> pygame.Surface | None:
        if width <= 0 or height <= 0:
            return None
        cache_key = f"{screen_id}/{filename}@{width}x{height}:{fit}"
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]
        image = self.load_chunk(screen_id, filename)
        if image is None:
            return None
        prepared = self._fit_surface(image, width, height, fit=fit)
        self._scaled_cache[cache_key] = prepared
        return prepared

    def _fit_surface(self, image: pygame.Surface, width: int, height: int, *, fit: str) -> pygame.Surface:
        source_w, source_h = image.get_size()
        if source_w <= 0 or source_h <= 0:
            return image
        if fit == "fill":
            if source_w == width and source_h == height:
                return image
            return pygame.transform.smoothscale(image, (width, height))
        scale = min(width / source_w, height / source_h)
        target_w = max(1, int(source_w * scale))
        target_h = max(1, int(source_h * scale))
        if target_w == source_w and target_h == source_h:
            return image
        return pygame.transform.smoothscale(image, (target_w, target_h))

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

            image = self._prepare_surface(image)
            self._image_cache[filename] = pygame.transform.smoothscale(
                image,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
            )
        return self._image_cache[filename]

    def load_chunk(self, screen_id: str, filename: str) -> pygame.Surface | None:
        """Load a PNG chunk from assets/ui_chunks/<screen_id>/<filename>."""
        if not filename:
            return None
        cache_key = f"{screen_id}/{filename}"
        if cache_key not in self._chunk_cache:
            image_path = self.chunks_dir / screen_id / filename
            if not image_path.is_file():
                self._chunk_cache[cache_key] = None
            else:
                try:
                    trimmed_path = self.chunks_dir / ".trim_cache" / screen_id / filename
                    if (
                        filename != "background.png"
                        and trimmed_path.is_file()
                        and trimmed_path.stat().st_mtime >= image_path.stat().st_mtime
                    ):
                        image = pygame.image.load(str(trimmed_path))
                        self._chunk_cache[cache_key] = self._prepare_surface(image)
                    else:
                        image = pygame.image.load(str(image_path))
                        image = self._prepare_surface(image)
                        if filename != "background.png":
                            image = _trim_flat_backdrop(image)
                            trimmed_path.parent.mkdir(parents=True, exist_ok=True)
                            pygame.image.save(image, str(trimmed_path))
                        self._chunk_cache[cache_key] = image
                except (pygame.error, FileNotFoundError, OSError) as error:
                    print(f"[Lumi Assets] Failed to load chunk '{cache_key}': {error}")
                    self._chunk_cache[cache_key] = None
        return self._chunk_cache[cache_key]

    def chunk_exists(self, screen_id: str, filename: str) -> bool:
        return (self.chunks_dir / screen_id / filename).is_file()

    def preload_screen(self, screen_id: str, filenames: tuple[str, ...]) -> None:
        for filename in filenames:
            self.load_chunk(screen_id, filename)
