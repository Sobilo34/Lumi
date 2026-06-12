"""D2 offline continue screen tests."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.offline_fallback import offline_prompt_text, resolve_offline_message
from engine.screen_registry import ScreenRegistry


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


def test_resolve_offline_message_uses_reason() -> None:
    assert resolve_offline_message("Mic missing") == "Mic missing"


def test_offline_prompt_includes_reassurance() -> None:
    text = offline_prompt_text("Voice is not ready.")
    assert "Voice is not ready." in text
    assert "tap" in text.lower()


def test_offline_continue_button_returns_main_menu(engine: GameEngine) -> None:
    engine._show_offline_fallback("Voice is not ready.")
    assert engine.state.current_screen_id == "offline_continue"

    engine._handle_action("continue_offline")
    assert engine.state.current_screen_id == "main_menu"
    assert engine.state.offline_status_message == ""


def test_offline_hitbox_target_main_menu(engine: GameEngine) -> None:
    registry = ScreenRegistry()
    button = next(box for box in registry.get_hitboxes("offline_continue") if box.name == "Continue Offline")
    assert button.action == "continue_offline"
    assert button.target == "main_menu"

    engine._show_offline_fallback()
    clicked = engine.current_screen.handle_click(button.rect.center)
    assert clicked is not None
    assert clicked.target == "main_menu"


def test_voice_challenge_stt_failure_routes_offline(engine: GameEngine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.game_engine.speech_to_text.is_available", lambda: False)
    monkeypatch.setattr(
        "engine.game_engine.speech_to_text.get_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    engine.set_screen("voice_challenge")
    engine._handle_action("start_listening")

    assert engine.state.current_screen_id == "offline_continue"
    assert "tap" in engine.state.offline_status_message.lower()


def test_microphone_check_still_routes_offline(engine: GameEngine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: False)
    monkeypatch.setattr(
        "engine.microphone_check.speech_to_text.get_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    engine.set_screen("microphone_check")
    engine.set_screen("listening_state")

    assert engine.state.current_screen_id == "offline_continue"
