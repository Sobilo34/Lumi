"""Dynamic overlay for the badge unlock screen (21_badge_unlock.png)."""
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
        title_font = pygame.font.SysFont(None, 42, bold=True)
        badge_font = pygame.font.SysFont(None, 34, bold=True)
        subtitle_font = pygame.font.SysFont(None, 24)
    except Exception:
        return

    # Cover the baked-in ribbon label on the PNG and draw the milestone badge name.
    ribbon = pygame.Rect(int(SCREEN_WIDTH * 0.31), int(SCREEN_HEIGHT * 0.505), int(SCREEN_WIDTH * 0.38), int(SCREEN_HEIGHT * 0.07))
    ribbon_bg = pygame.Surface((ribbon.width, ribbon.height), pygame.SRCALPHA)
    ribbon_bg.fill((156, 98, 196, 235))
    screen.blit(ribbon_bg, ribbon.topleft)

    badge_label = badge_font.render(badge_name, True, (255, 255, 255))
    badge_rect = badge_label.get_rect(center=ribbon.center)
    screen.blit(badge_label, badge_rect)

    subtitle_label = subtitle_font.render(subtitle, True, (255, 248, 255))
    subtitle_rect = subtitle_label.get_rect(center=(ribbon.centerx, ribbon.bottom + int(SCREEN_HEIGHT * 0.035)))
    subtitle_bg = pygame.Surface((subtitle_label.get_width() + 24, subtitle_label.get_height() + 12), pygame.SRCALPHA)
    subtitle_bg.fill((255, 255, 255, 210))
    screen.blit(subtitle_bg, (subtitle_rect.x - 12, subtitle_rect.y - 6))
    screen.blit(subtitle_label, subtitle_rect)
