"""Writing Castle progression and answer matching tests."""
from __future__ import annotations

from engine.learner_model import LearnerModel
from engine.world_progression import screen_accessible, word_garden_unlocked
from engine.writing_progression import (
    advance_writing_curriculum,
    build_writing_round,
    writing_castle_unlocked,
)
from writing_recognition.matcher import letter_answer_matches, word_answer_matches


def test_letter_answer_matches_case_insensitive() -> None:
    assert letter_answer_matches("B", "b")
    assert letter_answer_matches("B", "B")
    assert not letter_answer_matches("B", "D")


def test_word_answer_matches_fuzzy() -> None:
    assert word_answer_matches("cat", "cat")
    assert word_answer_matches("cat", "CAT")
    assert word_answer_matches("cat", "dog") is False


def test_writing_castle_unlocks_with_letter_island() -> None:
    learner = LearnerModel(
        profile_data={
            "mastered_letters": list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "current_letter_index": 25,
        }
    )
    assert writing_castle_unlocked(learner)
    assert word_garden_unlocked(learner)
    assert screen_accessible(learner, "writing_castle_game")


def test_writing_castle_locked_before_letter_island() -> None:
    learner = LearnerModel(profile_data={"mastered_letters": ["A"], "current_letter_index": 1})
    assert not screen_accessible(learner, "writing_castle_game")


def test_writing_curriculum_advances_letters_then_words() -> None:
    learner = LearnerModel(
        profile_data={
            "writing_letter_index": 0,
            "writing_word_index": 0,
            "mastered_writing_letters": [],
            "mastered_writing_words": [],
        }
    )
    round_data = build_writing_round(learner)
    assert round_data["mode"] == "letters"
    assert round_data["target"] == "A"
    advance_writing_curriculum(learner)
    assert learner.writing_letter_index == 1
    assert "A" in learner.mastered_writing_letters
