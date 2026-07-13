"""World map unlock progression tests."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from engine.game_engine import GameEngine
from engine.learner_model import LearnerModel
from engine.personal_tutor import ALPHABET
from engine.world_progression import (
    WORLD_LETTER_ISLAND,
    WORLD_WORD_GARDEN,
    letter_island_complete,
    letter_island_curriculum_complete,
    maybe_complete_letter_island,
    maybe_complete_word_garden,
    prepare_world_practice,
    screen_accessible,
    sync_world_completion,
    word_garden_unlocked,
)
from engine.word_mastery import WORD_MASTERY_THRESHOLD, empty_word_mastery_record


def _mastered_word_mastery(words: list[str]) -> dict:
    record = empty_word_mastery_record()
    record["mastery_score"] = WORD_MASTERY_THRESHOLD
    record["consecutive_correct"] = 2
    return {word: dict(record) for word in words}


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


def test_new_profile_locks_word_garden(engine: GameEngine) -> None:
    assert not word_garden_unlocked(engine.learner)
    assert screen_accessible(engine.learner, "letter_island_game")
    assert not screen_accessible(engine.learner, "word_garden_game")


def test_badge_c_curriculum_complete_unlocks_word_garden_without_full_mastery(engine: GameEngine) -> None:
    """Players who finish A–Z (Badge C) unlock Word Garden even if review letters remain."""
    engine.learner.mastered_letters = ["A", "B", "C", "D", "E", "G", "M", "R", "F", "Z", "H", "I"]
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.badges = ["Badge A", "Badge B", "Badge C"]
    engine.learner.completed_worlds = []
    engine.learner.save_profile()

    assert letter_island_curriculum_complete(engine.learner)
    assert letter_island_complete(engine.learner)
    assert word_garden_unlocked(engine.learner)
    assert screen_accessible(engine.learner, "word_garden_game")

    sync_world_completion(engine.learner)
    assert WORLD_LETTER_ISLAND in engine.learner.completed_worlds


def test_progress_complete_word_garden_click_after_badge_c(engine: GameEngine) -> None:
    engine.learner.mastered_letters = ["A", "B", "C", "D", "E", "G", "M", "R", "F", "Z", "H", "I"]
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.badges = ["Badge A", "Badge B", "Badge C"]
    engine.learner.completed_worlds = []
    engine.learner.save_profile()
    engine.set_screen("progress_complete")

    engine._handle_action("word_garden_game")

    assert engine.state.current_screen_id == "word_garden_game"


def test_next_world_after_badge_c_goes_to_word_garden(engine: GameEngine) -> None:
    engine.learner.mastered_letters = ["A", "B", "C", "D", "E", "G", "M", "R", "F", "Z", "H", "I"]
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.badges = ["Badge A", "Badge B", "Badge C"]
    engine.learner.completed_worlds = []
    engine.learner.save_profile()
    engine.set_screen("progress_complete")

    engine._handle_action("next_world")

    assert engine.state.current_screen_id == "word_garden_game"


def test_continue_from_badge_unlocks_word_garden_navigation(engine: GameEngine) -> None:
    engine.learner.mastered_letters = ["A", "B", "C", "D", "E", "G", "M", "R", "F", "Z", "H", "I"]
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.badges = ["Badge A", "Badge B", "Badge C"]
    engine.learner.completed_worlds = []
    engine.learner.save_profile()
    engine.state.badge_return_screen = "progress_complete"
    engine.set_screen("badge_unlock")

    engine._handle_action("continue_from_badge")
    assert engine.state.current_screen_id == "progress_complete"

    engine._handle_action("word_garden_game")
    assert engine.state.current_screen_id == "word_garden_game"


def test_mastering_z_unlocks_word_garden(engine: GameEngine) -> None:
    engine.learner.mastered_letters = list(ALPHABET)
    engine.learner.current_letter_index = len(ALPHABET) - 1
    for letter in ALPHABET:
        engine.learner.letter_mastery[letter]["mastery_score"] = 1.0
        engine.learner.letter_mastery[letter]["consecutive_correct"] = 2
    engine.learner.save_profile()

    assert maybe_complete_letter_island(engine.learner, letter="Z", curriculum=True)
    assert WORLD_LETTER_ISLAND in engine.learner.completed_worlds
    assert word_garden_unlocked(engine.learner)
    assert screen_accessible(engine.learner, "word_garden_game")


def test_all_letters_mastered_unlocks_completion_badge(engine: GameEngine) -> None:
    from engine.scoring import LETTER_ISLAND_COMPLETE_BADGE, check_letter_island_complete_badge

    engine.learner.mastered_letters = list(ALPHABET)
    for letter in ALPHABET:
        engine.learner.letter_mastery[letter]["mastery_score"] = 1.0
        engine.learner.letter_mastery[letter]["consecutive_correct"] = 2
    engine.learner.badges = []
    engine.learner.save_profile()

    unlocked = check_letter_island_complete_badge(engine.learner)
    assert unlocked == [LETTER_ISLAND_COMPLETE_BADGE]
    assert LETTER_ISLAND_COMPLETE_BADGE in engine.learner.badges


def test_mastering_all_word_garden_words_completes_world(engine: GameEngine) -> None:
    engine.learner.completed_worlds = [WORLD_LETTER_ISLAND]
    engine.learner.mastered_words = ["sun", "apple", "fish", "bird"]
    engine.learner.word_mastery = _mastered_word_mastery(["sun", "apple", "fish", "bird"])
    engine.learner.save_profile()

    assert maybe_complete_word_garden(engine.learner)
    assert WORLD_WORD_GARDEN in engine.learner.completed_worlds


def test_world_map_blocks_locked_navigation(engine: GameEngine) -> None:
    engine.set_screen("world_map")
    engine._handle_action("word_garden_game")
    assert engine.state.current_screen_id == "world_map"
    assert "Letter Island" in engine.state.world_map_status_message


def test_sync_backfills_completed_worlds_from_progress(engine: GameEngine) -> None:
    engine.learner.mastered_letters = list(ALPHABET)
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.mastered_words = ["sun", "apple", "fish", "bird"]
    engine.learner.word_mastery = _mastered_word_mastery(["sun", "apple", "fish", "bird"])
    engine.learner.completed_worlds = []
    engine.learner.save_profile()

    completed = sync_world_completion(engine.learner)
    assert WORLD_LETTER_ISLAND in completed
    assert WORLD_WORD_GARDEN in completed
    assert letter_island_complete(engine.learner)


def test_prepare_world_practice_resets_cursor_keeps_unlocks(engine: GameEngine) -> None:
    engine.learner.completed_worlds = [WORLD_LETTER_ISLAND]
    engine.learner.mastered_letters = list(ALPHABET)
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.save_profile()

    screen_id = prepare_world_practice(engine.learner, WORLD_LETTER_ISLAND)

    assert screen_id == "letter_island_game"
    assert engine.learner.current_letter_index == 0
    assert WORLD_LETTER_ISLAND in engine.learner.completed_worlds
    assert word_garden_unlocked(engine.learner)


def test_practice_again_replays_letter_island_keeps_word_garden_unlocked(engine: GameEngine) -> None:
    engine.learner.completed_worlds = [WORLD_LETTER_ISLAND]
    engine.learner.mastered_letters = list(ALPHABET)
    engine.learner.current_letter_index = len(ALPHABET) - 1
    engine.learner.save_profile()
    engine.state.last_completed_world_id = WORLD_LETTER_ISLAND
    engine.set_screen("progress_complete")

    engine._handle_action("practice_again")

    assert engine.state.current_screen_id == "letter_island_game"
    assert engine.learner.current_letter_index == 0
    assert screen_accessible(engine.learner, "word_garden_game")
    assert engine.state.current_task_target == "A"


def test_practice_again_after_word_garden_replays_word_garden(engine: GameEngine) -> None:
    engine.learner.completed_worlds = [WORLD_LETTER_ISLAND, WORLD_WORD_GARDEN]
    engine.learner.mastered_letters = list(ALPHABET)
    engine.learner.mastered_words = ["sun", "apple", "fish", "bird"]
    engine.learner.current_word_length = 5
    engine.learner.save_profile()
    engine.state.last_completed_world_id = WORLD_WORD_GARDEN
    engine.set_screen("progress_complete")

    engine._handle_action("practice_again")

    assert engine.state.current_screen_id == "word_garden_game"
    assert engine.learner.current_word_length == 3
