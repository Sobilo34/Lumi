"""Word Garden adaptive selection and mastery tests."""
from __future__ import annotations

import random
from pathlib import Path

import pytest

from engine.learner_model import LearnerModel
from engine.word_garden import WORD_SLOT_COUNT, build_word_garden_round, build_word_garden_round_for_target, get_word_garden_pool
from engine.word_mastery import (
    WORD_GARDEN_WORDS_DEFAULT,
    discover_installed_word_garden_words,
    pick_word_garden_target,
    update_word_mastery,
)


@pytest.fixture()
def learner(tmp_path: Path) -> LearnerModel:
    return LearnerModel(profile_path=tmp_path / "player_1.json")


def test_discover_installed_words_from_assets() -> None:
    pool = discover_installed_word_garden_words()
    assert len(pool) >= 13
    assert "dog" in pool
    assert "cat" in pool
    assert pool == get_word_garden_pool()


def test_build_word_garden_round_for_target_builds_four_object_choices(learner: LearnerModel) -> None:
    pool = get_word_garden_pool()
    round_data = build_word_garden_round_for_target(learner, "tree", pool=pool)
    assert round_data["target"] == "tree"
    assert round_data["prompt"] == "Touch the tree."
    assert len(round_data["choices"]) == WORD_SLOT_COUNT
    assert "tree" in round_data["choices"]
    assert all(choice in pool for choice in round_data["choices"])


def test_build_word_garden_round_returns_four_choices(learner: LearnerModel) -> None:
    pool = get_word_garden_pool()
    round_data = build_word_garden_round(learner, pool=pool)
    assert len(round_data["choices"]) == WORD_SLOT_COUNT
    assert round_data["target"] in round_data["choices"]
    assert round_data["target"] in pool
    assert round_data["prompt"] == f"Touch the {round_data['target']}."


def test_build_word_garden_round_avoids_immediate_repeat(learner: LearnerModel) -> None:
    pool = get_word_garden_pool()
    learner.weak_words = {"dog": 8}
    learner.mastered_words = ["cat", "dog"]
    learner.save_profile()
    round_data = build_word_garden_round(learner, pool=pool, last_target="dog")
    assert round_data["target"] != "dog"


def test_pick_word_garden_target_rotates_with_weighted_randomness(learner: LearnerModel) -> None:
    pool = ("dog", "sun", "ball", "fish")
    learner.weak_words = {"dog": 8}
    learner.save_profile()
    picks = {
        pick_word_garden_target(learner, pool, last_target="dog", rng=random.Random(seed))[0]
        for seed in range(40)
    }
    assert "dog" not in picks
    assert len(picks) >= 2


def test_word_mastery_tracks_attempts(learner: LearnerModel) -> None:
    record = update_word_mastery(learner, "sun", correct=True, first_try=True)
    assert record["attempts"] == 1
    assert record["correct"] == 1
    assert record["mastery_score"] > 0


def test_word_mastery_records_confusion(learner: LearnerModel) -> None:
    learner.record_word_mastery_attempt("cat", correct=False, confused_with="dog")
    record = learner.get_word_mastery_record("cat")
    assert record["wrong"] == 1
    assert record["confused_with"].get("dog") == 1


def test_default_pool_has_thirteen_words() -> None:
    assert len(WORD_GARDEN_WORDS_DEFAULT) == 13
