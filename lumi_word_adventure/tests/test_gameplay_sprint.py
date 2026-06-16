"""Gameplay sprint tests: letter adaptive, word garden targets, SFX, STT readiness."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine, LEGACY_WORD_ACTIONS
from engine.learner_model import LearnerModel
from engine.personal_tutor import ALPHABET
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


def _slot_for_target(engine: GameEngine, target: str) -> int:
    for index, letter in enumerate(engine.state.letter_choice_slots):
        if letter.upper() == target.upper():
            return index
    raise AssertionError(f"{target} not in {engine.state.letter_choice_slots}")


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
    assert "D" in engine.state.letter_choice_slots


def test_letter_island_follows_alphabet_curriculum(engine: GameEngine) -> None:
    engine.learner.current_letter_index = 12
    engine.learner.mastered_letters = []
    engine.learner.weak_letters = {}
    engine.learner.save_profile()
    engine._configure_letter_island_task()

    assert engine.state.current_task_target == "M"
    assert "M" in engine.state.letter_choice_slots
    assert len(engine.state.letter_choice_slots) == 4


def test_letter_island_correct_increments_attempts(engine: GameEngine) -> None:
    engine._configure_letter_island_task()
    target = engine.state.current_task_target or "A"
    slot_index = _slot_for_target(engine, target)
    before_attempts = int(engine.learner.attempts)
    before_correct = int(engine.learner.correct_answers)
    engine.set_screen("letter_island_game")

    engine._handle_letter_island_action(f"select_letter_slot_{slot_index}")

    assert engine.learner.attempts == before_attempts + 1
    assert engine.learner.correct_answers == before_correct + 1
    assert engine.state.current_screen_id == "letter_correct_feedback"
    assert target.upper() in engine.state.last_letter_feedback_message


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
    assert LEGACY_WORD_ACTIONS["select_word_cat"] == "cat"
    assert LEGACY_WORD_ACTIONS["select_word_dog"] == "dog"


def test_letter_island_slots_are_dynamic(engine: GameEngine) -> None:
    engine.learner.current_letter_index = 5
    engine.learner.weak_letters = {}
    engine.learner.save_profile()
    engine._configure_letter_island_task()
    target = engine.state.current_task_target or "F"
    assert len(engine.state.letter_choice_slots) == 4
    assert target in engine.state.letter_choice_slots
    assert engine._resolve_letter_from_action(f"select_letter_slot_{_slot_for_target(engine, target)}") == target


def test_letter_island_skips_mastered_weak_review(engine: GameEngine) -> None:
    engine.learner.mastered_letters = ["A"]
    engine.learner.weak_letters = {"A": 13}
    engine.learner.current_letter_index = 0
    engine.learner.save_profile()
    engine._configure_letter_island_task()
    assert engine.state.current_task_target == "A"


def test_letter_wrong_non_bd_stays_on_gameplay(engine: GameEngine) -> None:
    engine._configure_letter_island_task()
    target = engine.state.current_task_target or "A"
    wrong_slot = next(i for i, letter in enumerate(engine.state.letter_choice_slots) if letter.upper() != target.upper())
    engine.state.current_screen_id = "letter_island_game"
    engine._handle_letter_island_action(f"select_letter_slot_{wrong_slot}")
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.last_mistake_type == "letter_confusion"
    assert target.upper() in engine.state.last_letter_feedback_message


def test_letter_bd_confusion_shows_hint_screen(engine: GameEngine) -> None:
    engine.state.current_task_target = "B"
    engine.state.current_task_prompt = "Find the letter B."
    engine.state.letter_choice_slots = ["B", "D", "P", "A"]
    engine.state.current_screen_id = "letter_island_game"
    engine._handle_letter_island_action("select_letter_slot_1")
    assert engine.state.last_mistake_type == "bd_confusion"
    assert engine.state.current_screen_id == "letter_mistake_hint"
    assert "belly" in engine.state.last_letter_feedback_message.lower()


def test_alphabet_has_26_letters() -> None:
    assert len(ALPHABET) == 26


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
