"""Minimal reassurance overlay for the Offline Continue screen."""
from __future__ import annotations

import pygame

from config import (
    OFFLINE_OVERLAY_COLOR,
    OFFLINE_OVERLAY_PANEL_RGBA,
    OFFLINE_OVERLAY_POSITION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


def draw_offline_overlay(screen: pygame.Surface, status_message: str) -> None:
    if not status_message:
        return
    try:
        font = pygame.font.SysFont(None, 20)
    except Exception:
        return

    rendered = font.render(status_message, True, OFFLINE_OVERLAY_COLOR)
    panel = pygame.Surface((rendered.get_width() + 14, rendered.get_height() + 10), pygame.SRCALPHA)
    panel.fill(OFFLINE_OVERLAY_PANEL_RGBA)
    panel.blit(rendered, (7, 5))
    x = int(OFFLINE_OVERLAY_POSITION[0] * SCREEN_WIDTH)
    y = int(OFFLINE_OVERLAY_POSITION[1] * SCREEN_HEIGHT)
    screen.blit(panel, (x, y))
