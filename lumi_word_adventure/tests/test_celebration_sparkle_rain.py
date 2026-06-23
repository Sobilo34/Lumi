"""Headless draw tests for correct-popup sparkle rain."""
from __future__ import annotations

import pygame
import pytest

from ui.celebration_sparkle_rain import draw_celebration_sparkle_rain


@pytest.fixture(scope="module", autouse=True)
def _init_pygame() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)


def test_sparkle_rain_draws_at_mid_popup() -> None:
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    draw_celebration_sparkle_rain(surface, elapsed_ms=600, duration_ms=1200)
    assert surface.get_at((640, 120))[3] >= 0


def test_sparkle_rain_skips_after_duration() -> None:
    surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
    before = surface.copy()
    draw_celebration_sparkle_rain(surface, elapsed_ms=2000, duration_ms=1200)
    assert list(before.get_at((200, 200))) == list(surface.get_at((200, 200)))
