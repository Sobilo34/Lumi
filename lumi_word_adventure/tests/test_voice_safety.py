"""D3 voice failure safety tests."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.voice_guard import is_stt_ready, safe_listen_once, stt_status_message
from voice.speech_to_text import get_status_message, is_available, listen_once
from voice.text_to_speech import TextToSpeech


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


def test_stt_helpers_never_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> bool:
        raise RuntimeError("stt broken")

    monkeypatch.setattr("engine.voice_guard.speech_to_text.is_available", _boom)
    assert is_stt_ready() is False
    assert safe_listen_once() is None


def test_listen_once_returns_none_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("voice.speech_to_text.is_available", lambda: False)
    assert listen_once() is None


def test_stt_status_message_has_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("voice.speech_to_text.VOSK_AVAILABLE", False)
    monkeypatch.setattr("voice.speech_to_text.SR_AVAILABLE", False)
    message = get_status_message()
    assert "tap answers" in message.lower()
    assert "tap answers" in stt_status_message().lower()


def test_tts_missing_engine_does_not_crash() -> None:
    tts = TextToSpeech(enabled=True)
    assert tts.speak("Hello Lumi") in {True, False}
    tts.stop()
    tts.set_rate(130)


def test_tts_clear_pending_drops_queued_lines() -> None:
    tts = TextToSpeech(enabled=True)
    tts._available = True
    tts._queue.put("queued line")
    tts.clear_pending()
    assert tts._queue.empty()


def test_letter_island_speak_shows_page_when_stt_unavailable(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: False)
    monkeypatch.setattr("engine.game_engine.stt_status_message", lambda: "Voice is not ready. You can still tap answers.")

    engine.set_screen("letter_island_game")
    engine.state.current_task_target = "B"
    engine._handle_letter_island_action("voice_or_speak_mode")

    assert engine.state.current_screen_id == "letter_voice_challenge"
    assert engine.state.current_task_target == "B"


def test_letter_island_mic_routes_to_settings_when_stt_unavailable(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: False)
    monkeypatch.setattr(
        "engine.game_engine.stt_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    engine.set_screen("letter_voice_challenge")
    engine.state.current_task_target = "B"
    engine._handle_action("start_letter_listening")

    assert engine.state.current_screen_id == "settings"
    assert "test mic" in engine.state.settings_status_message.lower()


def test_word_garden_speak_routes_offline_when_stt_unavailable(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: False)
    monkeypatch.setattr("engine.game_engine.stt_status_message", lambda: "Voice is not ready. You can still tap answers.")

    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.set_screen("word_garden_game")
    engine._handle_action("voice_mode")

    assert engine.state.current_screen_id == "offline_continue"


def test_safe_listen_once_catches_listen_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("engine.voice_guard.is_stt_ready", lambda: True)

    def _boom(timeout: int = 5):
        raise OSError("microphone missing")

    monkeypatch.setattr("engine.voice_guard.speech_to_text.listen_once", _boom)
    assert safe_listen_once() is None


def test_voice_listening_uses_safe_listen(
    engine: GameEngine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("engine.game_engine.is_stt_ready", lambda: True)
    monkeypatch.setattr("engine.game_engine.safe_listen_once", lambda timeout=5: "apple")
    called = {"processed": False}

    def _process(spoken: str | None) -> None:
        called["processed"] = True
        assert spoken == "apple"

    monkeypatch.setattr(engine, "_process_voice_capture_result", _process)

    engine.set_screen("voice_challenge")
    engine._start_voice_listening()

    assert engine.state.current_screen_id == "listening_state"
    for _ in range(200):
        if called["processed"]:
            break
        engine.update()
    assert called["processed"] is True
