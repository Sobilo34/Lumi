"""EXIT button on the world map only — quits the game.

Other screens use the Home hitbox to navigate back; settings keeps its own
Back/Home controls unchanged.
"""
from __future__ import annotations

import pygame

from engine.control_assets import ControlAssets

# Back-compat alias for tests that assert these screens never show EXIT.
EXIT_EXCLUDED_SCREEN_IDS = frozenset(
    {
        "splash_loading",
        "welcome",
        "how_to_play",
        "main_menu",
        "practice_weak_skills",
        "teacher_report",
        "settings",
    }
)

EXIT_SCREEN_ID = "world_map"

_EXIT_W_PCT = 0.11
_EXIT_H_PCT = 0.09
_EXIT_MARGIN_X_PCT = 0.015
_EXIT_MARGIN_Y_PCT = 0.018


def exit_button_visible(screen_id: str) -> bool:
    return str(screen_id or "").strip() == EXIT_SCREEN_ID


def exit_button_rect(
    screen_size: tuple[int, int] = (1280, 720),
) -> pygame.Rect:
    width, height = screen_size
    w = max(1, int(width * _EXIT_W_PCT))
    h = max(1, int(height * _EXIT_H_PCT))
    x = width - w - int(width * _EXIT_MARGIN_X_PCT)
    y = int(height * _EXIT_MARGIN_Y_PCT)
    return pygame.Rect(x, y, w, h)


def draw_exit_button(
    surface: pygame.Surface,
    controls: ControlAssets | None = None,
) -> pygame.Rect | None:
    rect = exit_button_rect(surface.get_size())
    assets = controls or ControlAssets()
    image = assets.scaled("exit", rect.width, rect.height)
    if image is None:
        pygame.draw.ellipse(surface, (220, 48, 48), rect)
        label = pygame.font.SysFont(None, 22, bold=True).render("EXIT", True, (255, 255, 255))
        surface.blit(label, label.get_rect(center=rect.center))
        return rect
    x = rect.x + (rect.width - image.get_width()) // 2
    y = rect.y + (rect.height - image.get_height()) // 2
    surface.blit(image, (x, y))
    return rect


def exit_button_clicked(position: tuple[int, int], screen_id: str, screen_size: tuple[int, int]) -> bool:
    if not exit_button_visible(screen_id):
        return False
    return exit_button_rect(screen_size).collidepoint(position)
