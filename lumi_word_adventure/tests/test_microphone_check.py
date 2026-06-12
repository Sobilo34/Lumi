"""D1 microphone check safety and navigation tests."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.microphone_check import run_microphone_check
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


def test_run_microphone_check_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: False)
    monkeypatch.setattr(
        "engine.microphone_check.speech_to_text.get_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    result = run_microphone_check()

    assert result["available"] is False
    assert result["next_screen_id"] == "offline_continue"
    assert "tap answers" in str(result["status_message"]).lower()


def test_run_microphone_check_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: True)
    monkeypatch.setattr("engine.microphone_check.speech_to_text.listen_once", lambda timeout=2: "hello")

    result = run_microphone_check()

    assert result["available"] is True
    assert result["next_screen_id"] == "listening_state"
    assert result["heard_text"] == "hello"
    assert "ready" in str(result["status_message"]).lower()


def test_run_microphone_check_listen_failure_routes_offline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: True)

    def _boom(timeout: int = 2):
        raise RuntimeError("mic failure")

    monkeypatch.setattr("engine.microphone_check.speech_to_text.listen_once", _boom)

    result = run_microphone_check()

    assert result["available"] is False
    assert result["next_screen_id"] == "offline_continue"


def test_microphone_check_test_mic_success_flow(engine: GameEngine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: True)
    monkeypatch.setattr("engine.microphone_check.speech_to_text.listen_once", lambda timeout=2: "hi")

    engine.set_screen("microphone_check")
    engine.set_screen("listening_state")

    assert engine.state.current_screen_id == "listening_state"
    assert engine.state.microphone_test_mode is True
    assert "ready" in engine.state.microphone_status_message.lower()

    engine._handle_action("stop_listening")
    assert engine.state.current_screen_id == "settings"
    assert engine.state.microphone_test_mode is False


def test_microphone_check_unavailable_routes_offline(engine: GameEngine, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.microphone_check.speech_to_text.is_available", lambda: False)
    monkeypatch.setattr(
        "engine.microphone_check.speech_to_text.get_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    engine.set_screen("microphone_check")
    engine.set_screen("listening_state")

    assert engine.state.current_screen_id == "offline_continue"
    assert engine.state.microphone_test_mode is False


def test_microphone_check_skip_and_home(engine: GameEngine) -> None:
    engine.set_screen("microphone_check")

    engine._handle_action("skip_mic")
    assert engine.state.current_screen_id == "settings"

    engine.set_screen("microphone_check")
    engine._handle_action("home")
    assert engine.state.current_screen_id == "main_menu"


def test_microphone_check_hitboxes(engine: GameEngine) -> None:
    registry = ScreenRegistry()
    actions = {box.name: (box.target, box.action) for box in registry.get_hitboxes("microphone_check")}

    assert actions["Home"] == ("main_menu", "")
    assert actions["Test Mic"] == ("listening_state", "test_microphone")
    assert actions["Skip"] == ("settings", "skip_mic")

    engine.set_screen("microphone_check")
    skip = next(box for box in registry.get_hitboxes("microphone_check") if box.name == "Skip")
    clicked = engine.current_screen.handle_click(skip.rect.center)
    assert clicked is not None
    assert clicked.target == "settings"
