"""Careful dynamic overlays for the Teacher Report screen."""
from __future__ import annotations

from typing import Any

import pygame

from config import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEACHER_REPORT_OVERLAY_COLOR,
    TEACHER_REPORT_OVERLAY_FONT_LABEL,
    TEACHER_REPORT_OVERLAY_FONT_VALUE,
    TEACHER_REPORT_OVERLAY_LINE_GAP,
    TEACHER_REPORT_OVERLAY_PANEL_RGBA,
    TEACHER_REPORT_OVERLAY_POSITIONS,
)


def _anchor_xy(position: tuple[float, float]) -> tuple[int, int]:
    return int(position[0] * SCREEN_WIDTH), int(position[1] * SCREEN_HEIGHT)


def _render_chip(text: str, font: pygame.font.Font) -> pygame.Surface:
    rendered = font.render(text, True, TEACHER_REPORT_OVERLAY_COLOR)
    panel = pygame.Surface(
        (rendered.get_width() + 14, rendered.get_height() + 10),
        pygame.SRCALPHA,
    )
    panel.fill(TEACHER_REPORT_OVERLAY_PANEL_RGBA)
    panel.blit(rendered, (7, 5))
    return panel


def _overlay_lines(report: dict[str, Any]) -> list[tuple[str, str, str]]:
    return [
        ("stars_earned", "Stars earned", str(report.get("stars_earned", 0))),
        ("accuracy_percent", "Accuracy", f"{report.get('accuracy_percent', 0)}%"),
        ("strong_skill", "Strong skill", str(report.get("strong_skill", "Practice in progress"))),
        ("needs_practice", "Needs practice", str(report.get("needs_practice", "None"))),
        (
            "recommended_next_activity",
            "Recommended",
            str(report.get("recommended_next_activity", "World Map")),
        ),
    ]


def draw_teacher_report_overlays(screen: pygame.Surface, report: dict[str, Any]) -> None:
    """Draw the five B3 report values on top of 24_teacher_report.png."""
    if not report:
        return

    try:
        value_font = pygame.font.SysFont(None, TEACHER_REPORT_OVERLAY_FONT_VALUE)
        label_font = pygame.font.SysFont(None, TEACHER_REPORT_OVERLAY_FONT_LABEL)
    except Exception:
        return

    for key, label, value in _overlay_lines(report):
        position = TEACHER_REPORT_OVERLAY_POSITIONS.get(key)
        if position is None:
            continue

        anchor_x, anchor_y = _anchor_xy(position)
        label_chip = _render_chip(f"{label}: {value}", value_font)
        screen.blit(label_chip, (anchor_x, anchor_y))

        # Optional compact hint under the recommendation card only.
        if key == "recommended_next_activity":
            hint = _render_chip("Tap here to practice", label_font)
            screen.blit(
                hint,
                (anchor_x, anchor_y + label_chip.get_height() + TEACHER_REPORT_OVERLAY_LINE_GAP),
            )
