"""Minimal status overlay for the Microphone Check screen."""
from __future__ import annotations

import pygame

from config import (
    MICROPHONE_CHECK_OVERLAY_COLOR,
    MICROPHONE_CHECK_OVERLAY_PANEL_RGBA,
    MICROPHONE_CHECK_OVERLAY_POSITION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


def draw_microphone_check_overlay(screen: pygame.Surface, status_message: str) -> None:
    if not status_message:
        return
    try:
        font = pygame.font.SysFont(None, 20)
    except Exception:
        return

    rendered = font.render(status_message, True, MICROPHONE_CHECK_OVERLAY_COLOR)
    panel = pygame.Surface((rendered.get_width() + 14, rendered.get_height() + 10), pygame.SRCALPHA)
    panel.fill(MICROPHONE_CHECK_OVERLAY_PANEL_RGBA)
    panel.blit(rendered, (7, 5))
    x = int(MICROPHONE_CHECK_OVERLAY_POSITION[0] * SCREEN_WIDTH)
    y = int(MICROPHONE_CHECK_OVERLAY_POSITION[1] * SCREEN_HEIGHT)
    screen.blit(panel, (x, y))
