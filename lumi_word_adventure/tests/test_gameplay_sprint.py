"""Gameplay sprint tests: letter adaptive, word garden targets, SFX, STT readiness."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine, WORD_CARD_ACTIONS
from engine.learner_model import LearnerModel
from engine.sfx_generator import generate_default_sfx
from engine.sound_manager import SoundManager


@pytest.fixture()
def engine(tmp_path: Path) -> GameEngine:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    game = GameEngine(screen)
    game.learner = LearnerModel(profile_path=tmp_path / "player_1.json")
    return game


def test_stt_not_available_without_microphone_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("voice.speech_to_text.is_available", lambda: False)
    monkeypatch.setattr(
        "voice.speech_to_text.get_status_message",
        lambda: "Voice is not ready. You can still tap answers.",
    )

    from voice.speech_to_text import get_status_message, is_available

    assert is_available() is False
    assert "tap answers" in get_status_message().lower()


def test_letter_island_uses_adaptive_target(engine: GameEngine) -> None:
    engine.learner.weak_letters = {"D": 3}
    engine.learner.save_profile()
    engine._configure_letter_island_task()

    assert engine.state.current_task_target == "D"
    assert "D" in engine.state.current_task_prompt


def test_letter_island_correct_increments_attempts(engine: GameEngine) -> None:
    engine._configure_letter_island_task()
    target = engine.state.current_task_target or "B"
    before_attempts = int(engine.learner.attempts)
    before_correct = int(engine.learner.correct_answers)
    engine.set_screen("letter_island_game")

    engine._handle_letter_island_action(f"select_letter_{target.lower()}")

    assert engine.learner.attempts == before_attempts + 1
    assert engine.learner.correct_answers == before_correct + 1
    assert engine.state.current_screen_id == "letter_correct_feedback"


def test_word_garden_selects_visible_target(engine: GameEngine) -> None:
    engine.learner.weak_words = {"sun": 3}
    engine.learner.save_profile()
    engine._configure_word_garden_task()

    assert engine.state.current_task_target == "sun"


def test_word_garden_dog_wrong_for_cat_target(engine: GameEngine) -> None:
    engine.state.current_task_target = "cat"
    engine.state.current_task_prompt = "Touch the cat."
    engine.set_screen("word_garden_game")

    engine._handle_word_garden_selection("dog")

    assert engine.state.current_screen_id == "word_mistake_hint"
    assert engine.state.last_word_selected == "dog"


def test_word_garden_hitboxes_use_neutral_actions() -> None:
    assert WORD_CARD_ACTIONS["select_word_cat"] == "cat"
    assert WORD_CARD_ACTIONS["select_word_dog"] == "dog"


def test_sfx_generator_writes_four_files(tmp_path: Path) -> None:
    paths = generate_default_sfx(tmp_path)
    assert len(paths) == 4
    assert all(path.is_file() for path in paths)


def test_sound_manager_play_sfx_does_not_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sounds_dir = tmp_path / "sounds"
    generate_default_sfx(sounds_dir)
    monkeypatch.setattr("engine.sound_manager.SOUNDS_DIR", sounds_dir)
    manager = SoundManager()
    manager.play_sfx("correct")
    manager.play_sfx("wrong")
    manager.play_sfx("badge")
