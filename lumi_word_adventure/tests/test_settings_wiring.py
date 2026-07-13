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


def test_settings_home_goes_to_main_menu(engine: GameEngine) -> None:
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
    engine.learner.child_name = "Alex"
    engine.learner.total_stars = 10
    engine.learner.current_letter_index = 12
    engine.learner.mastered_letters = ["A", "B", "C"]
    engine.learner.badges = ["First Star"]
    engine.learner.lumi_energy = 42
    engine.learner.save_profile()
    engine.state.completed_letter_target = "M"
    engine.state.completed_letter_choices = ["M", "N", "O", "P"]
    engine.state.pending_letter_curriculum_advance = True
    engine.state.preserve_letter_island_task = True
    engine.settings.toggle_music()
    engine.set_screen("settings")

    engine._handle_action("reset_progress")

    assert engine.learner.child_name == "Alex"
    assert engine.learner.total_stars == 0
    assert engine.learner.lumi_energy == 100
    assert engine.learner.current_letter_index == 0
    assert engine.learner.mastered_letters == []
    assert engine.learner.badges == []
    assert engine.state.completed_letter_target == ""
    assert engine.state.pending_letter_curriculum_advance is False
    assert engine.state.preserve_letter_island_task is False
    assert engine.state.current_task_target == "A"
    assert engine.state.gameplay_refresh_pending is True
    assert engine.state.settings_status_message == "Profile reset successfully"
    assert engine.settings.load_settings()["music_enabled"] is False


def test_settings_reset_progress_restarts_letter_island(engine: GameEngine) -> None:
    engine.learner.current_letter_index = 18
    engine.learner.save_profile()
    engine.set_screen("letter_island_game")
    assert engine.state.current_task_target != "A"

    engine.set_screen("settings")
    engine._handle_action("reset_progress")
    engine.set_screen("letter_island_game")

    assert engine.learner.current_letter_index == 0
    assert engine.state.current_task_target == "A"
    assert engine.state.gameplay_refresh_pending is False


def test_settings_reset_progress_ignored_off_settings(engine: GameEngine) -> None:
    engine.learner.total_stars = 5
    engine.learner.save_profile()
    engine.set_screen("main_menu")

    engine._handle_action("reset_progress")

    assert engine.learner.total_stars == 5


def test_settings_reset_progress_click_hitbox(engine: GameEngine) -> None:
    engine.learner.total_stars = 8
    engine.learner.save_profile()
    engine.set_screen("settings")
    hitboxes = engine.registry.get_hitboxes("settings")
    reset = next(box for box in hitboxes if box.name == "Reset")
    clicked = engine.current_screen.handle_click(reset.rect.center)
    assert clicked is not None
    assert clicked.action == "reset_progress"
    engine._handle_action(clicked.action)
    assert engine.learner.total_stars == 0


def test_settings_reset_progress_clicks_visual_button(engine: GameEngine) -> None:
    """Reset hitbox must cover the painted Reset button."""
    import pygame

    engine.learner.total_stars = 12
    engine.learner.save_profile()
    engine.set_screen("settings")
    reset = next(box for box in engine.registry.get_hitboxes("settings") if box.name == "Reset")
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": reset.rect.center, "button": 1})
    engine.handle_event(event)
    assert engine.learner.total_stars == 0
    assert engine.state.settings_status_message == "Profile reset successfully"


def test_settings_controls_align_with_png(engine: GameEngine) -> None:
    """Each settings control click should hit the intended action."""
    expected = {
        "Music": "toggle_music",
        "Voice": "toggle_voice",
        "Test Mic": "microphone_check",
        "Difficulty": "change_difficulty",
        "Reset": "reset_progress",
    }
    engine.set_screen("settings")
    for name, action in expected.items():
        hitbox = next(box for box in engine.registry.get_hitboxes("settings") if box.name == name)
        clicked = engine.current_screen.handle_click(hitbox.rect.center)
        assert clicked is not None, f"missed click for {name}"
        assert (clicked.action or clicked.target) == action, f"{name} got {clicked.action or clicked.target}"


def test_settings_test_mic_hitbox_target(engine: GameEngine) -> None:
    engine.set_screen("settings")
    hitboxes = engine.registry.get_hitboxes("settings")
    mic = next(box for box in hitboxes if box.name == "Test Mic")
    clicked = engine.current_screen.handle_click(mic.rect.center)
    assert clicked is not None
    assert (clicked.target or clicked.action) == "microphone_check"
