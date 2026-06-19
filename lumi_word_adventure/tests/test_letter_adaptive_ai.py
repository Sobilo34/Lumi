"""Letter Island adaptive AI: mastery, diagnosis, spaced review."""
from __future__ import annotations

from engine.adaptive_ai import (
    CONSECUTIVE_CORRECT_FOR_MASTERY,
    MASTERY_THRESHOLD,
    REVIEW_INTERVAL_LETTERS,
    diagnose_letter_mistake,
    is_letter_mastered,
    pick_letter_round_target,
    select_review_letter,
    should_insert_spaced_review,
    update_letter_mastery,
)
from engine.feedback import get_feedback, get_letter_mistake_hint
from engine.learner_model import LearnerModel
from data_loader import load_default_profile


def _learner(**overrides: object) -> LearnerModel:
    profile = load_default_profile()
    profile.update(overrides)
    return LearnerModel(profile_data=profile)


def test_mastery_increases_on_correct_first_try() -> None:
    learner = _learner()
    record = update_letter_mastery(learner, "B", correct=True, first_try=True, hints_used=0)
    assert record["correct"] == 1
    assert record["first_try_correct"] == 1
    assert record["mastery_score"] > 0.0


def test_mastery_decreases_on_wrong_and_hints() -> None:
    learner = _learner()
    update_letter_mastery(learner, "B", correct=True, first_try=True, hints_used=0)
    before = learner.get_letter_mastery_record("B")["mastery_score"]
    update_letter_mastery(learner, "B", correct=False, hints_used=2)
    after = learner.get_letter_mastery_record("B")["mastery_score"]
    assert after < before
    assert learner.get_letter_mastery_record("B")["wrong"] == 1
    assert learner.get_letter_mastery_record("B")["hints_used"] == 2


def test_letter_marked_mastered_at_score_threshold() -> None:
    learner = _learner()
    learner.letter_mastery["B"]["mastery_score"] = MASTERY_THRESHOLD
    learner.save_profile()
    assert is_letter_mastered(learner, "B")
    learner.record_letter_mastery_attempt("B", correct=True, first_try=True)
    assert "B" in learner.mastered_letters


def test_letter_marked_mastered_after_consecutive_correct() -> None:
    learner = _learner()
    for _ in range(CONSECUTIVE_CORRECT_FOR_MASTERY):
        learner.record_letter_mastery_attempt("C", correct=True, first_try=True)
    assert is_letter_mastered(learner, "C")
    assert "C" in learner.mastered_letters


def test_diagnose_visual_confusion_groups() -> None:
    assert diagnose_letter_mistake("B", "D") == "bd_confusion"
    assert diagnose_letter_mistake("M", "W") == "visual_confusion"
    assert diagnose_letter_mistake("C", "G") == "visual_confusion"
    assert diagnose_letter_mistake("E", "F") == "visual_confusion"
    assert diagnose_letter_mistake("I", "L") == "visual_confusion"
    assert diagnose_letter_mistake("O", "Q") == "visual_confusion"
    assert diagnose_letter_mistake("A", "Z") == "letter_confusion"


def test_confusion_counts_stored_in_profile() -> None:
    learner = _learner()
    learner.record_letter_mastery_attempt("B", correct=False, confused_with="D")
    confused = learner.get_letter_mastery_record("B")["confused_with"]
    assert confused.get("D") == 1


def test_targeted_visual_confusion_feedback_and_hint() -> None:
    feedback = get_feedback(False, mistake_type="visual_confusion", target="M", selected="W")
    assert "hills" in feedback["message"].lower() or "mmm" in feedback["message"].lower()
    hint = get_letter_mistake_hint("visual_confusion", target="M", selected="W")
    assert "M" in hint or "W" in hint


def test_select_review_letter_prefers_low_mastery() -> None:
    learner = _learner(current_letter_index=5)
    learner.letter_mastery["A"]["attempts"] = 4
    learner.letter_mastery["A"]["mastery_score"] = 0.2
    learner.letter_mastery["A"]["wrong"] = 3
    learner.letter_mastery["B"]["attempts"] = 2
    learner.letter_mastery["B"]["mastery_score"] = 0.9
    learner.save_profile()

    review, reason = select_review_letter(learner)
    assert review == "A"
    assert reason in {"low_mastery_score", "repeated_wrong_attempts", "high_confusion_count"}


def test_spaced_review_inserts_after_curriculum_interval() -> None:
    learner = _learner(
        current_letter_index=4,
        curriculum_letters_since_review=REVIEW_INTERVAL_LETTERS,
    )
    learner.letter_mastery["A"]["attempts"] = 2
    learner.letter_mastery["A"]["mastery_score"] = 0.4
    learner.save_profile()

    assert should_insert_spaced_review(learner)
    target, review_mode, reason = pick_letter_round_target(learner)
    assert review_mode is True
    assert target == "A"
    assert reason in {"low_mastery_score", "repeated_wrong_attempts", "high_confusion_count"}


def test_curriculum_continues_when_review_not_due() -> None:
    learner = _learner(current_letter_index=2, curriculum_letters_since_review=0)
    learner.save_profile()
    target, review_mode, reason = pick_letter_round_target(learner)
    assert review_mode is False
    assert target == "C"
    assert reason == "letter_curriculum"


def test_mastered_letter_not_selected_for_review() -> None:
    learner = _learner(current_letter_index=4)
    learner.letter_mastery["B"]["mastery_score"] = 1.0
    learner.letter_mastery["B"]["consecutive_correct"] = 3
    learner.letter_mastery["B"]["attempts"] = 8
    learner.mastered_letters = ["B"]
    learner.weak_letters = {"B": 4, "D": 2}
    learner.letter_mastery["D"]["attempts"] = 3
    learner.letter_mastery["D"]["mastery_score"] = 0.2
    learner.letter_mastery["D"]["wrong"] = 2
    learner.save_profile()

    review, reason = select_review_letter(learner)
    assert review == "D"
    assert review != "B"
    assert reason in {"low_mastery_score", "repeated_wrong_attempts", "high_confusion_count"}
