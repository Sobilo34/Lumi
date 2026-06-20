"""Dynamic text overlay for the badge unlock screen."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from engine.scoring import badge_subtitle


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
        badge_font = pygame.font.SysFont(None, 36, bold=True)
        subtitle_font = pygame.font.SysFont(None, 24)
    except Exception:
        return

    # Purple ribbon on the stone pedestal — title sits on the banner art.
    ribbon = pygame.Rect(
        int(SCREEN_WIDTH * 0.27),
        int(SCREEN_HEIGHT * 0.528),
        int(SCREEN_WIDTH * 0.46),
        int(SCREEN_HEIGHT * 0.072),
    )

    badge_label = badge_font.render(badge_name, True, (255, 255, 255))
    badge_rect = badge_label.get_rect(center=ribbon.center)
    screen.blit(badge_label, badge_rect)

    subtitle_label = subtitle_font.render(subtitle, True, (255, 248, 255))
    subtitle_rect = subtitle_label.get_rect(
        center=(ribbon.centerx, ribbon.bottom + int(SCREEN_HEIGHT * 0.038)),
    )
    subtitle_bg = pygame.Surface(
        (subtitle_label.get_width() + 24, subtitle_label.get_height() + 12),
        pygame.SRCALPHA,
    )
    subtitle_bg.fill((255, 255, 255, 210))
    screen.blit(subtitle_bg, (subtitle_rect.x - 12, subtitle_rect.y - 6))
    screen.blit(subtitle_label, subtitle_rect)
