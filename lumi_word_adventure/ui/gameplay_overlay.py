"""Overlays for word garden (Letter Island uses component screens in ui/components/)."""
from __future__ import annotations

import pygame

from config import BABY_PINK, SCREEN_HEIGHT, SCREEN_WIDTH

_PANEL_RGBA = (255, 255, 255, 215)
_TEXT_COLOR = (72, 58, 88)
_ACCENT = (244, 114, 114)

WORD_SLOT_POSITIONS = (
    (0.24, 0.52),
    (0.40, 0.52),
    (0.56, 0.52),
    (0.72, 0.52),
)


def _font(size: int, *, bold: bool = True) -> pygame.font.Font:
    try:
        return pygame.font.SysFont("dejavusans", size, bold=bold)
    except Exception:
        return pygame.font.SysFont(None, size)


def _draw_banner(surface: pygame.Surface, text: str, y_pct: float = 0.07) -> None:
    font = _font(22)
    label = font.render(text, True, _TEXT_COLOR)
    panel = pygame.Surface((label.get_width() + 24, label.get_height() + 12), pygame.SRCALPHA)
    panel.fill(_PANEL_RGBA)
    pygame.draw.rect(panel, pygame.Color(BABY_PINK), panel.get_rect(), width=2, border_radius=12)
    panel.blit(label, (12, 6))
    x = (SCREEN_WIDTH - panel.get_width()) // 2
    y = int(SCREEN_HEIGHT * y_pct)
    surface.blit(panel, (x, y))


def _draw_label(surface: pygame.Surface, text: str, center: tuple[int, int], *, font_size: int = 34) -> None:
    label = _font(font_size).render(text, True, _TEXT_COLOR)
    padding = 8
    panel = pygame.Surface((label.get_width() + padding * 2, label.get_height() + padding), pygame.SRCALPHA)
    panel.fill(_PANEL_RGBA)
    panel.blit(label, (padding, padding // 2))
    rect = panel.get_rect(center=center)
    surface.blit(panel, rect.topleft)


def draw_word_garden_overlay(
    surface: pygame.Surface,
    *,
    target_word: str,
    slot_words: list[str],
    progress_text: str,
) -> None:
    _draw_banner(surface, progress_text)
    target_banner = _font(24).render(f"Touch: {target_word.lower()}", True, _ACCENT)
    target_panel = pygame.Surface((target_banner.get_width() + 20, target_banner.get_height() + 10), pygame.SRCALPHA)
    target_panel.fill(_PANEL_RGBA)
    target_panel.blit(target_banner, (10, 5))
    surface.blit(target_panel, ((SCREEN_WIDTH - target_panel.get_width()) // 2, int(SCREEN_HEIGHT * 0.18)))

    for index, (x_pct, y_pct) in enumerate(WORD_SLOT_POSITIONS):
        if index >= len(slot_words):
            break
        word = slot_words[index].lower()
        center = (int(SCREEN_WIDTH * x_pct), int(SCREEN_HEIGHT * y_pct))
        font_size = 28 if len(word) <= 4 else 22
        _draw_label(surface, word, center, font_size=font_size)
