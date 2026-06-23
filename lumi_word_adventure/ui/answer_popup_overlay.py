"""Lightweight on-screen Correct / Try again popup for gameplay challenges."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import (
    blit_outlined_text,
    draw_rounded_rect,
    fit_font_size,
    font,
)

_CORRECT_CARD = (157, 212, 136)
_CORRECT_BORDER = (109, 178, 93)
_WRONG_CARD = (251, 186, 121)
_WRONG_BORDER = (227, 142, 73)
_HINT_CARD = (255, 244, 186)
_HINT_BORDER = (240, 196, 84)
_TEXT_DARK = (94, 63, 33)

# Letter Island "Find X" prompt sits at y_pct=0.305, h_pct=0.1 in ui_chunk_manifest.
LETTER_ISLAND_POPUP_ANCHOR_Y_PCT = 0.355


def _wrap_lines(text: str, max_width: int, size: int) -> list[str]:
    words = (text or "").split()
    if not words:
        return []
    f = font(size, bold=False)
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if f.size(candidate)[0] <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:4]


def _draw_hint_banner(screen: pygame.Surface, message: str) -> None:
    """A friendly, non-blocking hint banner near the top — does not dim the board."""
    message = str(message or "").strip()
    if not message:
        return
    body_size = 28
    lines = _wrap_lines(message, int(SCREEN_WIDTH * 0.62) - 80, body_size)
    if not lines:
        return
    line_h = body_size + 6
    card_w = int(SCREEN_WIDTH * 0.66)
    card_h = int(line_h * len(lines) + 78)
    card = pygame.Rect(0, 0, card_w, card_h)
    card.center = (SCREEN_WIDTH // 2, int(SCREEN_HEIGHT * 0.16))

    draw_rounded_rect(screen, card, _HINT_CARD, radius=22, border=_HINT_BORDER, border_width=4)
    blit_outlined_text(
        screen,
        "Hint",
        (card.centerx, card.y + 26),
        30,
        (255, 255, 255),
        outline=_HINT_BORDER,
        outline_width=3,
    )
    base_y = card.y + 60
    body_font = font(body_size, bold=False)
    for idx, line in enumerate(lines):
        label = body_font.render(line, True, _TEXT_DARK)
        screen.blit(label, label.get_rect(center=(card.centerx, base_y + idx * line_h)))


def draw_answer_popup_overlay(
    screen: pygame.Surface,
    *,
    kind: str,
    message: str = "",
    anchor_y_pct: float | None = None,
    compact: bool = False,
    elapsed_ms: int = 0,
    duration_ms: int = 1200,
) -> None:
    """Draw a centered, auto-dismissing feedback card over the current screen."""
    kind = str(kind or "").strip().lower()
    if kind == "hint":
        _draw_hint_banner(screen, message)
        return
    if kind not in {"correct", "wrong"}:
        return

    correct = kind == "correct"
    title = "Correct!" if correct else "Try again"
    card_color = _CORRECT_CARD if correct else _WRONG_CARD
    border_color = _CORRECT_BORDER if correct else _WRONG_BORDER

    if compact:
        card_w = int(SCREEN_WIDTH * 0.36)
        card_h = int(SCREEN_HEIGHT * 0.13)
    else:
        card_w = int(SCREEN_WIDTH * 0.5)
        card_h = int(SCREEN_HEIGHT * 0.34)

    card = pygame.Rect(0, 0, card_w, card_h)
    anchor_y = int(SCREEN_HEIGHT * anchor_y_pct) if anchor_y_pct is not None else SCREEN_HEIGHT // 2
    card.center = (SCREEN_WIDTH // 2, anchor_y)

    if not compact:
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 70))
        screen.blit(dim, (0, 0))

    if correct:
        from ui.celebration_sparkle_rain import draw_celebration_sparkle_rain

        draw_celebration_sparkle_rain(
            screen,
            elapsed_ms=elapsed_ms,
            duration_ms=duration_ms,
        )

    draw_rounded_rect(screen, card, card_color, radius=20 if compact else 26, border=border_color, border_width=4)

    title_rect = pygame.Rect(
        card.x,
        card.y + int(card.height * (0.12 if compact else 0.14)),
        card.width,
        int(card.height * (0.76 if compact else 0.34)),
    )
    title_size = fit_font_size(title, title_rect, fill_height_ratio=0.82)
    blit_outlined_text(
        screen,
        title,
        title_rect.center,
        title_size,
        (255, 255, 255),
        outline=border_color,
        outline_width=3,
    )

    message = str(message or "").strip()
    if message and not compact:
        body_size = 30
        lines = _wrap_lines(message, card.width - 60, body_size)
        base_y = card.y + int(card.height * 0.58)
        for idx, line in enumerate(lines):
            label = font(body_size, bold=False).render(line, True, _TEXT_DARK)
            screen.blit(label, label.get_rect(center=(card.centerx, base_y + idx * (body_size + 6))))
