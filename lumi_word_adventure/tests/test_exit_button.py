"""Tests for the world-map EXIT button overlay."""
from __future__ import annotations

import os

import pygame
import pytest

from ui.exit_button_overlay import (
    EXIT_EXCLUDED_SCREEN_IDS,
    EXIT_SCREEN_ID,
    exit_button_clicked,
    exit_button_rect,
    exit_button_visible,
)


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    pygame.display.set_mode((1280, 720))


def test_exit_hidden_on_menu_flow_pages() -> None:
    for screen_id in ("welcome", "main_menu", "how_to_play", "settings", "teacher_report", "practice_weak_skills"):
        assert screen_id in EXIT_EXCLUDED_SCREEN_IDS
        assert exit_button_visible(screen_id) is False


def test_exit_visible_only_on_world_map() -> None:
    assert exit_button_visible(EXIT_SCREEN_ID) is True
    assert exit_button_visible("letter_island_game") is False
    assert exit_button_visible("voice_challenge") is False
    assert exit_button_visible("writing_castle_game") is False


def test_exit_button_rect_is_top_right() -> None:
    rect = exit_button_rect((1280, 720))
    assert rect.right <= 1280
    assert rect.top >= 0
    assert rect.centerx > 1000


def test_exit_button_click_detection() -> None:
    rect = exit_button_rect((1280, 720))
    assert exit_button_clicked(rect.center, "world_map", (1280, 720)) is True
    assert exit_button_clicked((10, 10), "world_map", (1280, 720)) is False
    assert exit_button_clicked(rect.center, "main_menu", (1280, 720)) is False
    assert exit_button_clicked(rect.center, "letter_island_game", (1280, 720)) is False


def test_exit_button_quits_from_world_map(tmp_path) -> None:
    from engine.game_engine import GameEngine
    from engine.learner_model import LearnerModel
    from engine.settings_manager import SettingsManager

    screen = pygame.display.get_surface() or pygame.display.set_mode((1280, 720))
    engine = GameEngine(screen)
    engine.settings = SettingsManager(settings_path=tmp_path / "settings.json")
    engine.learner = LearnerModel(profile_path=tmp_path / "player.json")
    engine._apply_loaded_settings(engine.settings.load_settings())

    engine.set_screen("world_map")
    engine._handle_exit_button_click(exit_button_rect((1280, 720)).center)
    assert engine.running is False
