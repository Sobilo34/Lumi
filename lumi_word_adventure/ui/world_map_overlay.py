"""Status message overlay for the world map screen."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


def _chip(text: str, font: pygame.font.Font) -> pygame.Surface:
    rendered = font.render(text, True, (72, 58, 88))
    panel = pygame.Surface((rendered.get_width() + 18, rendered.get_height() + 12), pygame.SRCALPHA)
    panel.fill((255, 255, 255, 220))
    panel.blit(rendered, (9, 6))
    return panel


def draw_world_map_overlay(
    screen: pygame.Surface,
    *,
    status_message: str = "",
) -> None:
    if not status_message:
        return
    try:
        font = pygame.font.SysFont(None, 20)
    except Exception:
        return

    chip = _chip(status_message, font)
    x = (SCREEN_WIDTH - chip.get_width()) // 2
    y = int(SCREEN_HEIGHT * 0.86)
    screen.blit(chip, (x, y))
