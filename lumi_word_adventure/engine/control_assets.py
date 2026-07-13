"""Load and cache shared UI control button artwork."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import UI_CONTROLS_DIR

CONTROL_NAMES = frozenset(
    {
        "home",
        "letter_island_world",
        "word_garden_world",
        "writing_castle_world",
        "repeat",
        "hint",
        "speaker",
        "settings",
        "skip",
        "mic",
        "verify",
        "clear",
        "try_again",
        "switch_to_letters",
        "switch_to_word",
        "exit",
    }
)


class ControlAssets:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root or UI_CONTROLS_DIR)
        self._cache: dict[str, pygame.Surface] = {}
        self._scaled_cache: dict[tuple[str, int, int], pygame.Surface] = {}

    def available(self) -> bool:
        marker = self.root / ".shipped_ready"
        return marker.is_file() and any(self.root.glob("*.png"))

    def load(self, name: str) -> pygame.Surface | None:
        key = str(name or "").strip().lower()
        if key not in CONTROL_NAMES:
            return None
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        path = self.root / f"{key}.png"
        if not path.is_file():
            return None
        surface = pygame.image.load(str(path)).convert_alpha()
        self._cache[key] = surface
        return surface

    def scaled(self, name: str, width: int, height: int) -> pygame.Surface | None:
        key = str(name or "").strip().lower()
        w = max(1, int(width))
        h = max(1, int(height))
        cache_key = (key, w, h)
        cached = self._scaled_cache.get(cache_key)
        if cached is not None:
            return cached
        source = self.load(key)
        if source is None:
            return None
        sw, sh = source.get_size()
        scale = min(w / sw, h / sh)
        nw = max(1, int(sw * scale))
        nh = max(1, int(sh * scale))
        scaled = pygame.transform.smoothscale(source, (nw, nh))
        self._scaled_cache[cache_key] = scaled
        return scaled

    def invalidate(self) -> None:
        self._cache.clear()
        self._scaled_cache.clear()
