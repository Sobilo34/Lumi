"""Teacher report overlay configuration tests."""
from __future__ import annotations

import os

import pygame
import pytest

from config import (
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TEACHER_REPORT_OVERLAY_POSITIONS,
    TEACHER_REPORT_PRACTICE_HITBOX,
)
from ui.report_overlay import _overlay_lines


def test_overlay_positions_are_normalized() -> None:
    required = {
        "stars_earned",
        "accuracy_percent",
        "strong_skill",
        "needs_practice",
        "recommended_next_activity",
    }
    assert required.issubset(TEACHER_REPORT_OVERLAY_POSITIONS)
    for key, (x_pct, y_pct) in TEACHER_REPORT_OVERLAY_POSITIONS.items():
        assert 0.0 <= x_pct <= 1.0, key
        assert 0.0 <= y_pct <= 1.0, key


def test_practice_hitbox_is_normalized() -> None:
    x_pct, y_pct, w_pct, h_pct = TEACHER_REPORT_PRACTICE_HITBOX
    assert 0.0 <= x_pct <= 1.0
    assert 0.0 <= y_pct <= 1.0
    assert 0.0 < w_pct <= 1.0
    assert 0.0 < h_pct <= 1.0


def test_overlay_lines_include_b3_fields() -> None:
    report = {
        "stars_earned": 9,
        "accuracy_percent": 80,
        "strong_skill": "Letter recognition",
        "needs_practice": "Letters B and D",
        "recommended_next_activity": "B/D Practice",
    }
    lines = dict((key, (label, value)) for key, label, value in _overlay_lines(report))
    assert lines["stars_earned"] == ("Stars earned", "9")
    assert lines["accuracy_percent"] == ("Accuracy", "80%")
    assert lines["strong_skill"] == ("Strong skill", "Letter recognition")
    assert lines["needs_practice"] == ("Needs practice", "Letters B and D")
    assert lines["recommended_next_activity"] == ("Recommended", "B/D Practice")


def test_draw_teacher_report_overlays_runs_headless() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    from ui.report_overlay import draw_teacher_report_overlays

    draw_teacher_report_overlays(
        screen,
        {
            "stars_earned": 3,
            "accuracy_percent": 75,
            "strong_skill": "Word reading",
            "needs_practice": "None",
            "recommended_next_activity": "World Map",
        },
    )
