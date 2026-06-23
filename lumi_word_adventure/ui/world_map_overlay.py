"""Status message overlay for the world map screen (transient toasts)."""
from __future__ import annotations

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from ui.components.primitives import (
    HUD_PINK,
    blit_outlined_text,
    draw_rect_shadow,
    draw_rounded_rect,
    font,
)


def _wrap_message(text: str, max_width: int, *, size: int) -> list[str]:
    words = str(text or "").split()
    if not words:
        return [""]
    draw_font = font(size, bold=True)
    lines: list[str] = []
    active = words[0]
    for word in words[1:]:
        trial = f"{active} {word}"
        if draw_font.size(trial)[0] <= max_width:
            active = trial
        else:
            lines.append(active)
            active = word
    lines.append(active)
    return lines


def draw_world_map_overlay(
    screen: pygame.Surface,
    *,
    status_message: str = "",
) -> None:
    cleaned = str(status_message or "").strip()
    if not cleaned:
        return
    try:
        font_size = 26
        max_panel_width = int(SCREEN_WIDTH * 0.72)
        padding_x = 24
        padding_y = 14
        line_gap = 6
        inner_width = max_panel_width - padding_x * 2
        lines = _wrap_message(cleaned, inner_width, size=font_size)
        draw_font = font(font_size, bold=True)
        while len(lines) > 2 and font_size > 20:
            font_size -= 2
            draw_font = font(font_size, bold=True)
            lines = _wrap_message(cleaned, inner_width, size=font_size)

        line_height = draw_font.get_height()
        text_block_height = len(lines) * line_height + max(0, len(lines) - 1) * line_gap
        panel_height = text_block_height + padding_y * 2
        longest_line = max((draw_font.size(line)[0] for line in lines), default=0)
        panel_width = min(max_panel_width, longest_line + padding_x * 2)

        panel = pygame.Rect(0, 0, panel_width, panel_height)
        panel.centerx = SCREEN_WIDTH // 2
        panel.y = int(SCREEN_HEIGHT * 0.78)

        draw_rect_shadow(screen, panel, radius=18, offset=(0, 4), alpha=30)
        draw_rounded_rect(
            screen,
            panel,
            (255, 252, 246),
            radius=18,
            border=HUD_PINK,
            border_width=2,
        )

        y = panel.y + padding_y
        for line in lines:
            blit_outlined_text(
                screen,
                line,
                (panel.centerx, y + line_height // 2),
                font_size,
                (88, 52, 108),
                outline=(255, 255, 255),
                outline_width=2,
            )
            y += line_height + line_gap
    except Exception:
        return
