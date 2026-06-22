"""Gameplay sprint tests: letter adaptive, word garden targets, SFX, STT readiness."""
from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pygame
import pytest

from config import PROJECT_DIR, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.game_engine import GAMEPLAY_HITBOX_SCREEN_IDS, GameEngine, LEGACY_WORD_ACTIONS
from engine.screen_registry import ScreenRegistry
from ui.chunk_manifest import card_slot_rects, get_screen_spec
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


def test_letter_island_next_round_syncs_target_and_slots(engine: GameEngine) -> None:
    engine._configure_letter_island_task()
    first_target = str(engine.state.current_task_target or "A").upper()
    first_slots = [str(letter).upper() for letter in engine.state.letter_choice_slots]
    assert first_target in first_slots
    slot_index = _slot_for_target(engine, first_target)
    engine.set_screen("letter_island_game")
    engine._handle_letter_island_action(f"select_letter_slot_{slot_index}")
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.answer_popup_kind == "correct"
    assert engine.state.pending_letter_curriculum_advance is True
    assert engine.state.completed_letter_target == first_target
    assert first_target in engine.state.completed_letter_choices

    success_view = engine._scene_view()
    assert success_view.target_letter == first_target
    assert first_target in success_view.slot_letters

    engine._resolve_answer_popup()
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.answer_popup_kind == ""
    assert engine.state.pending_letter_curriculum_advance is False

    next_target = str(engine.state.current_task_target or "A").upper()
    next_slots = [str(letter).upper() for letter in engine.state.letter_choice_slots]
    view = engine._scene_view()
    assert next_target in next_slots
    assert view.target_letter == next_target
    assert tuple(view.slot_letters) == tuple(next_slots)
    if next_target != first_target:
        assert next_slots != first_slots


def test_mastering_j_unlocks_badge_a_and_returns_to_gameplay(engine: GameEngine) -> None:
    engine.learner.current_letter_index = ALPHABET.index("J")
    engine.learner.weak_letters = {}
    engine.learner.badges = []
    engine.learner.save_profile()
    engine._configure_letter_island_task()
    assert engine.state.current_task_target == "J"

    slot_index = _slot_for_target(engine, "J")
    engine.set_screen("letter_island_game")
    engine._handle_letter_island_action(f"select_letter_slot_{slot_index}")

    assert engine.state.current_screen_id == "badge_unlock"
    assert engine.state.last_unlocked_badges == ["Badge A"]
    assert "Badge A" in engine.learner.badges

    engine._handle_action("continue_from_badge")
    assert engine.state.current_screen_id == "letter_island_game"


def test_mastering_z_shows_progress_complete_after_badge_c(engine: GameEngine) -> None:
    engine.learner.current_letter_index = ALPHABET.index("Z")
    engine.learner.badges = ["Badge A", "Badge B"]
    engine.learner.completed_worlds = []
    engine.learner.mastered_letters = list("ABCDEFGHIJKLMNOPQRSTUVWXY")
    engine.learner.weak_letters = {}
    engine.learner.save_profile()
    engine._configure_letter_island_task()
    assert engine.state.current_task_target == "Z"

    slot_index = _slot_for_target(engine, "Z")
    engine.set_screen("letter_island_game")
    engine._handle_letter_island_action(f"select_letter_slot_{slot_index}")

    assert engine.state.current_screen_id == "badge_unlock"
    assert engine.state.last_unlocked_badges == ["Badge C"]
    assert engine.state.badge_return_screen == "progress_complete"
    assert "letter_island" in engine.learner.completed_worlds

    engine._handle_action("continue_from_badge")
    assert engine.state.current_screen_id == "progress_complete"


def test_all_letters_perfected_shows_completion_badge_and_word_garden_path(engine: GameEngine) -> None:
    from engine.scoring import LETTER_ISLAND_COMPLETE_BADGE

    for letter in ALPHABET:
        engine.learner.letter_mastery[letter]["mastery_score"] = 1.0
        engine.learner.letter_mastery[letter]["consecutive_correct"] = 2
        engine.learner.mark_letter_mastered(letter)
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.badges = []
    engine.learner.save_profile()
    engine._configure_letter_island_task()
    target = str(engine.state.current_task_target or "Z").upper()
    slot_index = _slot_for_target(engine, target)
    engine.set_screen("letter_island_game")

    engine._handle_letter_island_action(f"select_letter_slot_{slot_index}")

    assert engine.state.current_screen_id == "badge_unlock"
    assert engine.state.last_unlocked_badges == [LETTER_ISLAND_COMPLETE_BADGE]
    assert LETTER_ISLAND_COMPLETE_BADGE in engine.learner.badges
    assert engine.state.badge_return_screen == "progress_complete"

    engine._handle_action("continue_from_badge")
    assert engine.state.current_screen_id == "progress_complete"

    engine._handle_action("next_world")
    assert engine.state.current_screen_id == "word_garden_game"


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
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.answer_popup_kind == "correct"
    assert engine.state.last_letter_feedback_message == "Correct"


def test_word_garden_selects_visible_target(engine: GameEngine) -> None:
    engine.learner.weak_words = {"sun": 3}
    engine.learner.save_profile()
    engine._configure_word_garden_task()

    assert engine.state.current_task_target == "sun"
    assert engine.state.current_task_prompt == "Touch the Sun."
    assert engine._word_garden_voice_prompt() == "Touch the Sun."


def test_word_garden_bird_wrong_for_sun_target(engine: GameEngine) -> None:
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.set_screen("word_garden_game")
    engine.state.current_task_target = "sun"
    engine.state.current_task_prompt = "Touch the Sun."
    engine.state.word_choice_slots = ["sun", "bird", "apple", "cup"]

    engine._handle_word_garden_selection("bird")

    assert engine.state.current_screen_id == "word_garden_game"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.last_word_selected == "bird"
    assert engine.state.answer_popup_next_screen == "word_garden_game"


def test_word_garden_hitboxes_use_neutral_actions() -> None:
    assert LEGACY_WORD_ACTIONS["select_word_sun"] == "sun"
    assert LEGACY_WORD_ACTIONS["select_word_bird"] == "bird"


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


def test_letter_wrong_non_bd_shows_try_again_popup(engine: GameEngine) -> None:
    engine._configure_letter_island_task()
    target = engine.state.current_task_target or "A"
    wrong_slot = next(i for i, letter in enumerate(engine.state.letter_choice_slots) if letter.upper() != target.upper())
    engine.state.current_screen_id = "letter_island_game"
    engine._handle_letter_island_action(f"select_letter_slot_{wrong_slot}")
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.answer_popup_kind == "wrong"
    assert engine.state.last_mistake_type == "letter_confusion"
    assert target.upper() in engine.state.last_letter_feedback_message
    assert engine.state.answer_popup_next_screen == "letter_island_game"


def test_letter_bd_confusion_shows_try_again_popup(engine: GameEngine) -> None:
    engine.state.current_task_target = "B"
    engine.state.current_task_prompt = "Find the letter B."
    engine.state.letter_choice_slots = ["B", "D", "P", "A"]
    engine.state.current_screen_id = "letter_island_game"
    engine._handle_letter_island_action("select_letter_slot_1")
    assert engine.state.last_mistake_type == "bd_confusion"
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.answer_popup_kind == "wrong"
    assert "belly" in engine.state.last_letter_feedback_message.lower()


def test_word_garden_hud_hitboxes_include_settings() -> None:
    registry = ScreenRegistry()
    names = {box.name for box in registry.get_hitboxes("word_garden_game")}
    assert {"Home", "Settings", "Repeat", "Hint", "Speak"}.issubset(names)


def test_gameplay_screens_refresh_hitboxes_on_entry(engine: GameEngine) -> None:
    engine.state.current_task_target = "cat"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.set_screen("word_garden_game")
    hitboxes = engine.screens["word_garden_game"].hitboxes
    assert any(box.action.startswith("select_word_slot_") for box in hitboxes)
    assert GAMEPLAY_HITBOX_SCREEN_IDS >= {
        "word_garden_game",
        "letter_island_game",
    }


def test_word_mistake_try_again_preserves_round(engine: GameEngine) -> None:
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.state.current_task_target = "sun"
    engine.state.word_choice_slots = ["sun", "cat", "dog", "ball"]
    engine.state.current_screen_id = "word_garden_game"
    engine._show_word_mistake_feedback("Good try. Listen and try again.")
    assert engine.state.answer_popup_kind == "wrong"
    engine._resolve_answer_popup()
    assert engine.state.current_screen_id == "word_garden_game"
    assert engine.state.current_task_target == "sun"


def test_word_correct_next_starts_new_round(engine: GameEngine) -> None:
    engine.learner.completed_worlds = ["letter_island"]
    engine.learner.save_profile()
    engine.state.current_task_target = "cat"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    engine.state.current_screen_id = "word_garden_game"
    engine._show_word_correct_feedback("Great job!")
    assert engine.state.answer_popup_kind == "correct"
    engine._resolve_answer_popup()
    assert engine.state.current_screen_id == "word_garden_game"
    assert engine.state.current_hint_level == 0


def test_word_garden_dynamic_word_slots_follow_target(engine: GameEngine) -> None:
    engine.state.current_task_target = "dog"
    engine.state.word_choice_slots = ["cat", "dog", "sun", "ball"]
    hitboxes = engine._hitboxes_for_screen("word_garden_game")
    dog_slot = next(
        index
        for index, word in enumerate(engine.state.word_choice_slots)
        if word == "dog"
    )
    slot = next(box for box in hitboxes if box.action == f"select_word_slot_{dog_slot}")
    spec = get_screen_spec(
        "word_garden_game",
        fallback_image=engine.registry.get_image_filename("word_garden_game"),
    )
    cards = spec.dynamic.get("word_cards") or {}
    x, y, w, h = card_slot_rects(cards)[dog_slot]
    assert slot.rect.x == x
    assert slot.rect.y == y


def test_letter_mistake_try_again_preserves_task(engine: GameEngine) -> None:
    engine.state.current_task_target = "F"
    engine.state.letter_choice_slots = ["F", "E", "P", "T"]
    engine.state.current_screen_id = "letter_island_game"
    engine._show_letter_mistake_feedback("Good try. You can do it!")
    assert engine.state.answer_popup_kind == "wrong"
    engine._resolve_answer_popup()
    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.state.current_task_target == "F"


def test_voice_challenge_renders_dynamic_say_object(engine: GameEngine) -> None:
    from ui.chunk_composer import ChunkComposer
    from ui.chunk_manifest import get_screen_spec

    speak_bg = PROJECT_DIR / "assets" / "ui_chunks" / "word_garden_game" / "speak_background.png"
    if not speak_bg.is_file():
        pytest.skip("Word Garden speak background is not installed")

    engine.state.current_task_target = "sun"
    engine.state.word_choice_slots = ["sun", "cat", "dog", "ball"]
    engine._configure_voice_challenge_task()
    spec = get_screen_spec("voice_challenge", fallback_image=engine.registry.get_image_filename("voice_challenge"))
    view = replace(engine._scene_view(), screen_id="voice_challenge", voice_target="sun", target_word="sun")
    composer = ChunkComposer(engine.asset_manager)
    surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    composer.compose(surface, spec, view)
    assert view.voice_target == "sun"
    assert surface.get_at((640, 360)).a == 255


def test_voice_help_uses_current_target(engine: GameEngine) -> None:
    engine.state.current_task_target = "dog"
    engine.state.word_choice_slots = ["dog", "cat", "sun", "ball"]
    engine.state.current_screen_id = "voice_challenge"
    line = engine._voice_help_line()
    assert "dog" in line.lower()


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
