"""Tests for when the click-mic prompt should appear."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine, VOICE_MIC_IDLE_SCREENS
from engine.learner_model import LearnerModel
from engine.settings_manager import SettingsManager


@pytest.fixture()
def engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))

    game = GameEngine(screen)
    game.settings = SettingsManager(settings_path=tmp_path / "settings.json")
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    game._apply_loaded_settings(game.settings.load_settings())
    return game


def test_mic_prompt_shows_on_idle_speak_screen(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: True)
    engine.set_screen("letter_voice_challenge")
    assert engine._should_show_voice_mic_prompt() is True


def test_mic_prompt_hides_while_listening(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: True)
    engine.set_screen("letter_listening_state")
    assert engine._should_show_voice_mic_prompt() is False


def test_mic_prompt_hides_during_pronunciation_feedback(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: True)
    engine.set_screen("letter_voice_challenge")
    engine.state.voice_pronunciation_feedback = "try_again"
    assert engine._should_show_voice_mic_prompt() is False


def test_idle_screens_constant() -> None:
    assert "letter_voice_challenge" in VOICE_MIC_IDLE_SCREENS
    assert "voice_challenge" in VOICE_MIC_IDLE_SCREENS
    assert "letter_listening_state" not in VOICE_MIC_IDLE_SCREENS
