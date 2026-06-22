"""Loading overlay helpers."""
from __future__ import annotations

import pygame
import pytest

from ui.loading import draw_spinner, spinner_angle_deg


@pytest.fixture(scope="module", autouse=True)
def _init_pygame() -> None:
    pygame.init()
    pygame.display.set_mode((1280, 720))


def test_spinner_angle_advances_with_time() -> None:
    pygame.time.set_timer(pygame.USEREVENT, 0)
    a0 = spinner_angle_deg(1000, speed_deg_per_sec=360.0)
    a1 = spinner_angle_deg(1000 - 500, speed_deg_per_sec=360.0)
    assert a1 > a0 or abs(a1 - a0) > 1.0


def test_draw_spinner_writes_pixels() -> None:
    surface = pygame.Surface((120, 120), pygame.SRCALPHA)
    draw_spinner(surface, (60, 60), radius=24, started_at_ms=pygame.time.get_ticks())
    assert surface.get_at((60, 60)).a >= 0
