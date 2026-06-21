"""Shared global app background image.

A single soft, child-friendly background is painted under every screen except
the ones listed in ``config.BACKGROUND_EXEMPT_SCREENS``. Loading is cached and
degrades to ``None`` (callers keep their own procedural background) if the image
is missing, so the app never crashes when the asset is absent.
"""
from __future__ import annotations

import pygame

from config import APP_BACKGROUND_PATH, BACKGROUND_EXEMPT_SCREENS, SCREEN_HEIGHT, SCREEN_WIDTH

_cache: pygame.Surface | None = None
_load_failed = False


def get_app_background() -> pygame.Surface | None:
    """Return the screen-sized app background, or None when unavailable."""
    global _cache, _load_failed
    if _cache is not None:
        return _cache
    if _load_failed:
        return None
    if not APP_BACKGROUND_PATH.is_file():
        _load_failed = True
        return None
    try:
        image = pygame.image.load(str(APP_BACKGROUND_PATH))
        if pygame.display.get_surface() is not None:
            image = image.convert()
        _cache = pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except pygame.error:
        _load_failed = True
        return None
    return _cache


def screen_uses_app_background(screen_id: str) -> bool:
    return screen_id not in BACKGROUND_EXEMPT_SCREENS


def paint_app_background(surface: pygame.Surface, screen_id: str | None = None) -> bool:
    """Blit the global background. Returns True if it was painted."""
    if screen_id is not None and not screen_uses_app_background(screen_id):
        return False
    background = get_app_background()
    if background is None:
        return False
    surface.blit(background, (0, 0))
    return True
