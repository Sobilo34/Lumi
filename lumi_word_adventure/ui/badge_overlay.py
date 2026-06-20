"""Dynamic text overlay for the badge unlock screen."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from engine.scoring import badge_subtitle
from ui.components.primitives import blit_outlined_text, fit_font_size


def draw_badge_unlock_overlay(
    screen: pygame.Surface,
    *,
    badge_names: tuple[str, ...] | list[str],
) -> None:
    if not badge_names:
        return

    badge_name = str(badge_names[0]).strip()
    subtitle = badge_subtitle(badge_name)

    try:
        subtitle_font = pygame.font.SysFont(None, 32, bold=True)
    except Exception:
        return

    # Purple ribbon on the stone pedestal — white subtitle only, no extra box.
    ribbon = pygame.Rect(
        int(SCREEN_WIDTH * 0.26),
        int(SCREEN_HEIGHT * 0.532),
        int(SCREEN_WIDTH * 0.48),
        int(SCREEN_HEIGHT * 0.068),
    )
    font_size = fit_font_size(subtitle, ribbon, fill_height_ratio=0.72)
    blit_outlined_text(
        screen,
        subtitle,
        ribbon.center,
        font_size,
        (255, 255, 255),
        outline=(120, 70, 160),
        outline_width=2,
    )
