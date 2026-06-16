"""Gameplay overlays that sync dynamic tutor content with reference PNG layouts."""
from __future__ import annotations

import pygame

from config import BABY_PINK, SCREEN_HEIGHT, SCREEN_WIDTH

_PANEL_RGBA = (255, 255, 255, 235)
_TEXT_COLOR = (72, 58, 88)
_ACCENT = (244, 114, 114)
_BROWN = (120, 72, 48)

# Hitbox-aligned card regions on 07_letter_island_gameplay.png (x, y, w, h as fractions).
LETTER_CARD_RECTS = (
    (0.29, 0.41, 0.13, 0.25),
    (0.43, 0.41, 0.13, 0.25),
    (0.57, 0.41, 0.13, 0.25),
    (0.71, 0.41, 0.13, 0.25),
)
LETTER_CARD_TINTS = (
    (210, 195, 235),
    (195, 225, 195),
    (240, 200, 215),
    (245, 210, 175),
)

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


def _pct_rect(x_pct: float, y_pct: float, w_pct: float, h_pct: float) -> pygame.Rect:
    return pygame.Rect(
        int(SCREEN_WIDTH * x_pct),
        int(SCREEN_HEIGHT * y_pct),
        int(SCREEN_WIDTH * w_pct),
        int(SCREEN_HEIGHT * h_pct),
    )


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


def _draw_find_prompt(surface: pygame.Surface, target_letter: str) -> None:
    """Cover the baked-in 'Find B' art and draw the active target prompt."""
    cover = _pct_rect(0.30, 0.165, 0.40, 0.12)
    panel = pygame.Surface(cover.size, pygame.SRCALPHA)
    panel.fill(_PANEL_RGBA)
    pygame.draw.rect(panel, pygame.Color(BABY_PINK), panel.get_rect(), width=2, border_radius=16)
    surface.blit(panel, cover.topleft)

    find_font = _font(34)
    letter_font = _font(52)
    find_label = find_font.render("Find", True, _BROWN)
    letter_label = letter_font.render(target_letter.upper(), True, _ACCENT)
    gap = 14
    total_w = find_label.get_width() + gap + letter_label.get_width()
    start_x = cover.x + (cover.width - total_w) // 2
    y = cover.y + (cover.height - max(find_label.get_height(), letter_label.get_height())) // 2
    surface.blit(find_label, (start_x, y + 8))
    surface.blit(letter_label, (start_x + find_label.get_width() + gap, y))


def _draw_letter_card(
    surface: pygame.Surface,
    letter: str,
    x_pct: float,
    y_pct: float,
    w_pct: float,
    h_pct: float,
    tint: tuple[int, int, int],
) -> None:
    """Cover each decorative card letter with the active round letter."""
    rect = _pct_rect(x_pct, y_pct, w_pct, h_pct)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((*tint, 245))
    pygame.draw.rect(panel, pygame.Color(255, 255, 255), panel.get_rect(), width=3, border_radius=18)
    glyph = _font(int(rect.height * 0.55)).render(letter.upper(), True, _TEXT_COLOR)
    panel.blit(glyph, glyph.get_rect(center=(rect.width // 2, rect.height // 2)))
    surface.blit(panel, rect.topleft)


def _draw_label(surface: pygame.Surface, text: str, center: tuple[int, int], *, font_size: int = 34) -> None:
    label = _font(font_size).render(text, True, _TEXT_COLOR)
    padding = 8
    panel = pygame.Surface((label.get_width() + padding * 2, label.get_height() + padding), pygame.SRCALPHA)
    panel.fill(_PANEL_RGBA)
    panel.blit(label, (padding, padding // 2))
    rect = panel.get_rect(center=center)
    surface.blit(panel, rect.topleft)


def _draw_message_panel(
    surface: pygame.Surface,
    message: str,
    rect: pygame.Rect,
    *,
    font_size: int = 26,
    accent_letter: str | None = None,
) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(_PANEL_RGBA)
    pygame.draw.rect(panel, pygame.Color(BABY_PINK), panel.get_rect(), width=2, border_radius=16)
    surface.blit(panel, rect.topleft)

    font = _font(font_size)
    if accent_letter:
        accent = _font(int(font_size * 1.8)).render(accent_letter.upper(), True, _ACCENT)
        surface.blit(accent, accent.get_rect(center=(rect.centerx, rect.y + rect.height // 2 - 10)))
        msg_y = rect.y + rect.height // 2 + accent.get_height() // 2
    else:
        msg_y = rect.centery

    wrapped = _wrap_text(font, message, rect.width - 24)
    line_height = font.get_linesize()
    total_h = line_height * len(wrapped)
    start_y = rect.y + (rect.height - total_h) // 2 if not accent_letter else msg_y
    for index, line in enumerate(wrapped):
        label = font.render(line, True, _TEXT_COLOR)
        surface.blit(label, label.get_rect(midtop=(rect.centerx, start_y + index * line_height)))


def _wrap_text(font: pygame.font.Font, text: str, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def draw_letter_island_overlay(
    surface: pygame.Surface,
    *,
    target_letter: str,
    slot_letters: list[str],
    progress_text: str,
) -> None:
    _draw_banner(surface, progress_text)
    _draw_find_prompt(surface, target_letter)
    for index, (x_pct, y_pct, w_pct, h_pct) in enumerate(LETTER_CARD_RECTS):
        if index >= len(slot_letters):
            break
        tint = LETTER_CARD_TINTS[index % len(LETTER_CARD_TINTS)]
        _draw_letter_card(surface, slot_letters[index], x_pct, y_pct, w_pct, h_pct, tint)


def draw_letter_correct_overlay(
    surface: pygame.Surface,
    *,
    target_letter: str,
    message: str,
) -> None:
    rect = _pct_rect(0.28, 0.28, 0.44, 0.22)
    _draw_message_panel(surface, message, rect, font_size=24, accent_letter=target_letter)


def draw_letter_mistake_overlay(
    surface: pygame.Surface,
    *,
    message: str,
) -> None:
    rect = _pct_rect(0.08, 0.06, 0.34, 0.16)
    _draw_message_panel(surface, message, rect, font_size=20)


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
