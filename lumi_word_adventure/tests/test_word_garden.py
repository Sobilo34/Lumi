"""Word Garden round selection tests."""
from __future__ import annotations

from pathlib import Path

import pytest

from engine.learner_model import LearnerModel
from engine.word_garden import WORD_GARDEN_WORDS, WORD_SLOT_COUNT, build_word_garden_round, build_word_garden_round_for_target


@pytest.fixture()
def learner(tmp_path: Path) -> LearnerModel:
    model = LearnerModel(profile_path=tmp_path / "player_1.json")
    return model


def test_word_garden_pool_has_thirteen_words() -> None:
    assert len(WORD_GARDEN_WORDS) == 13
    assert "cup" in WORD_GARDEN_WORDS
    assert "duck" in WORD_GARDEN_WORDS


def test_build_word_garden_round_for_target_builds_four_object_choices(learner: LearnerModel) -> None:
    round_data = build_word_garden_round_for_target(learner, "tree")
    assert round_data["target"] == "tree"
    assert round_data["prompt"] == "Touch the tree."
    assert len(round_data["choices"]) == WORD_SLOT_COUNT
    assert "tree" in round_data["choices"]
    assert all(choice in WORD_GARDEN_WORDS for choice in round_data["choices"])


def test_build_word_garden_round_returns_four_choices(learner: LearnerModel) -> None:
    round_data = build_word_garden_round(learner)
    assert len(round_data["choices"]) == WORD_SLOT_COUNT
    assert round_data["target"] in round_data["choices"]
    assert round_data["target"] in WORD_GARDEN_WORDS
    assert round_data["prompt"] == f"Touch the {round_data['target']}."


def test_build_word_garden_round_prioritizes_weak_words(learner: LearnerModel) -> None:
    learner.weak_words = {"frog": 3}
    learner.save_profile()
    round_data = build_word_garden_round(learner)
    assert round_data["target"] == "frog"
    assert round_data["reason"] == "word_review"
