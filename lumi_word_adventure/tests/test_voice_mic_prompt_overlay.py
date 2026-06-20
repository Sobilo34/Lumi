"""Tests for the idle-mic speak prompt overlay."""
from __future__ import annotations

import os

import pygame
import pytest

from ui.voice_mic_prompt_overlay import draw_voice_mic_prompt_overlay


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()


def test_voice_mic_prompt_overlay_renders() -> None:
    surface = pygame.Surface((1280, 720))
    draw_voice_mic_prompt_overlay(surface, shown_at_ms=1000, now_ms=1200)
    assert surface.get_at((640, 500)).a == 255
