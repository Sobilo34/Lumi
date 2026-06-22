"""Tests for the idle-mic hint badge."""
from __future__ import annotations

import os

import pygame
import pytest

from ui.voice_mic_prompt_overlay import (
    draw_mic_hint_badge,
    mic_hint_badge_rect,
    mic_hitbox_from_hitboxes,
)
from ui.hitboxes import Hitbox


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    pygame.display.set_mode((1280, 720))


def test_mic_hint_badge_renders_on_mic_corner() -> None:
    surface = pygame.Surface((1280, 720))
    mic_rect = pygame.Rect(500, 560, 140, 115)
    badge = draw_mic_hint_badge(surface, mic_rect)
    assert badge.width > 0
    assert surface.get_at(badge.center).a == 255


def test_mic_hitbox_lookup_prefers_speak_button() -> None:
    boxes = [
        Hitbox(name="Repeat", rect=pygame.Rect(0, 0, 10, 10), action="repeat_letter"),
        Hitbox(name="Speak", rect=pygame.Rect(200, 560, 140, 115), action="start_letter_listening"),
    ]
    rect = mic_hitbox_from_hitboxes(boxes)
    assert rect is not None
    assert rect.x == 200


def test_mic_hint_badge_rect_sits_on_top_right() -> None:
    mic_rect = pygame.Rect(200, 560, 140, 115)
    badge = mic_hint_badge_rect(mic_rect)
    assert badge.right >= mic_rect.right - 8
    assert badge.top <= mic_rect.top + 8
