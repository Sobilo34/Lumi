"""C3 settings screen wiring tests (headless pygame)."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel


@pytest.fixture()
def engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    from engine.settings_manager import SettingsManager

    game = GameEngine(screen)
    game.settings = SettingsManager(settings_path=tmp_path / "settings.json")
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    game._apply_loaded_settings(game.settings.load_settings())
    return game


def test_settings_back_and_home_go_to_main_menu(engine: GameEngine) -> None:
    engine.set_screen("settings")
    engine._handle_action("back")
    assert engine.state.current_screen_id == "main_menu"

    engine.set_screen("settings")
    engine._handle_action("home")
    assert engine.state.current_screen_id == "main_menu"


def test_settings_music_toggle_persists(engine: GameEngine) -> None:
    engine.set_screen("settings")
    engine._handle_action("toggle_music")

    saved = json.loads(engine.settings.settings_path.read_text(encoding="utf-8"))
    assert saved["music_enabled"] is False
    assert engine.state.music_enabled is False


def test_settings_voice_toggle_persists(engine: GameEngine) -> None:
    engine.set_screen("settings")
    engine._handle_action("toggle_voice")

    saved = json.loads(engine.settings.settings_path.read_text(encoding="utf-8"))
    assert saved["voice_enabled"] is False
    assert engine.state.voice_enabled is False


def test_settings_difficulty_cycles_easy_medium_hard(engine: GameEngine) -> None:
    engine.set_screen("settings")

    engine._handle_action("change_difficulty")
    assert engine.settings.load_settings()["difficulty_mode"] == "Hard"
    assert engine.state.difficulty == 3

    engine._handle_action("change_difficulty")
    assert engine.settings.load_settings()["difficulty_mode"] == "Easy"
    assert engine.state.difficulty == 1


def test_settings_reset_progress_keeps_settings(engine: GameEngine) -> None:
    engine.learner.total_stars = 10
    engine.learner.save_profile()
    engine.settings.toggle_music()
    engine.set_screen("settings")

    engine._handle_action("reset_progress")

    assert engine.learner.total_stars == 0
    assert engine.state.settings_status_message == "Profile reset successfully"
    assert engine.settings.load_settings()["music_enabled"] is False


def test_settings_test_mic_hitbox_target(engine: GameEngine) -> None:
    engine.set_screen("settings")
    hitboxes = engine.registry.get_hitboxes("settings")
    mic = next(box for box in hitboxes if box.name == "Test Mic")
    clicked = engine.current_screen.handle_click(mic.rect.center)
    assert clicked is not None
    assert (clicked.target or clicked.action) == "microphone_check"
