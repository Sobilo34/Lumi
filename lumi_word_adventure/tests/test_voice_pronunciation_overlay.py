"""Tests for voice pronunciation on-screen feedback overlay."""
from __future__ import annotations

import os

import pygame
import pytest

from ui.voice_pronunciation_overlay import draw_voice_pronunciation_overlay


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()


def test_voice_pronunciation_overlay_renders_correct() -> None:
    surface = pygame.Surface((1280, 720))
    draw_voice_pronunciation_overlay(
        surface,
        feedback="correct",
        shown_at_ms=1000,
        now_ms=1200,
    )
    assert surface.get_at((640, 360)).a == 255


def test_voice_pronunciation_overlay_renders_try_again() -> None:
    surface = pygame.Surface((1280, 720))
    draw_voice_pronunciation_overlay(
        surface,
        feedback="try_again",
        shown_at_ms=1000,
        now_ms=1300,
    )
    assert surface.get_at((640, 360)).a == 255


def test_voice_pronunciation_overlay_fades_out() -> None:
    surface = pygame.Surface((1280, 720))
    draw_voice_pronunciation_overlay(
        surface,
        feedback="correct",
        shown_at_ms=0,
        now_ms=5000,
    )
    # After fade window the overlay should not repaint the center.
    before = surface.get_at((640, 360))
    draw_voice_pronunciation_overlay(
        surface,
        feedback="correct",
        shown_at_ms=0,
        now_ms=5000,
    )
    assert surface.get_at((640, 360)) == before
