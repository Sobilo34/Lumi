from engine.scoring import (
    badge_unlock_speech_message,
    calculate_accuracy,
    calculate_stars,
    check_badge_unlocks,
    check_bd_master_badge,
    check_letter_milestone_badges,
    update_score,
)
from engine.learner_model import LearnerModel
from engine.word_mastery import WORD_MASTERY_THRESHOLD, empty_word_mastery_record


def _mastered_word_record() -> dict:
    record = empty_word_mastery_record()
    record["mastery_score"] = WORD_MASTERY_THRESHOLD
    record["consecutive_correct"] = 2
    return record


def test_correct_without_hint_gives_three_stars() -> None:
    assert calculate_stars(True, hints_used=0) == 3


def test_correct_with_one_hint_gives_two_stars() -> None:
    assert calculate_stars(True, hints_used=1) == 2


def test_correct_with_two_hints_gives_one_star() -> None:
    assert calculate_stars(True, hints_used=2) == 1


def test_wrong_answer_gives_zero_stars() -> None:
    assert calculate_stars(False, hints_used=0) == 0


def test_stars_are_never_subtracted() -> None:
    profile = {"total_stars": 5, "badges": []}

    assert update_score(profile, 3) == 8
    assert update_score(profile, -10) == 8
    assert profile["total_stars"] == 8


def test_calculate_accuracy_returns_percentage() -> None:
    assert calculate_accuracy(8, 10) == 80.0


def test_check_badge_unlocks_finds_expected_badges() -> None:
    mastered_pool_words = ("sun", "fish", "apple", "bird", "cup")
    profile = {
        "total_stars": 30,
        "mastered_letters": ["A", "B", "C", "D", "E", "F"],
        "mastered_words": list(mastered_pool_words),
        "voice_word_successes": 3,
        "word_mastery": {
            word: _mastered_word_record()
            for word in mastered_pool_words
        },
        "badges": [],
    }

    unlocked = check_badge_unlocks(profile)

    assert "Letter Hero" not in unlocked
    assert "Word Explorer" in unlocked
    assert "Brave Speaker" in unlocked
    assert "B and D Master" not in unlocked
    assert "Great Learner" in unlocked


def test_bd_master_badge_only_after_practice_flow() -> None:
    learner = LearnerModel(
        profile_data={
            "badges": [],
            "mastered_letters": ["B", "D"],
            "child_name": "Test",
        }
    )
    assert "B and D Master" not in check_badge_unlocks(learner)

    learner.bd_practice_completed = True
    learner.save_profile()
    assert check_bd_master_badge(learner) == ["B and D Master"]
    assert check_bd_master_badge(learner) == []


def test_letter_milestone_badges_unlock_at_j_t_and_z() -> None:
    learner = LearnerModel(profile_data={"badges": [], "child_name": "Test"})

    assert check_letter_milestone_badges(learner, "J") == ["Badge A"]
    assert "Badge A" in learner.badges

    assert check_letter_milestone_badges(learner, "J") == []
    assert check_letter_milestone_badges(learner, "T") == ["Badge B"]
    assert check_letter_milestone_badges(learner, "Z") == ["Badge C"]
    assert learner.badges == ["Badge A", "Badge B", "Badge C"]


def test_letter_milestone_badges_ignore_review_rounds() -> None:
    learner = LearnerModel(profile_data={"badges": [], "child_name": "Test"})
    assert check_letter_milestone_badges(learner, "J", curriculum=False) == []
    assert learner.badges == []


def test_letter_hero_badge_not_awarded_at_five_letters() -> None:
    learner = LearnerModel(
        profile_data={
            "badges": [],
            "child_name": "Test",
            "mastered_letters": ["A", "B", "C", "D", "E"],
        }
    )
    unlocked = check_badge_unlocks(learner)
    assert "Letter Hero" not in unlocked


def test_badge_unlock_speech_message_names_badge() -> None:
    message = badge_unlock_speech_message(["Badge A"])
    assert "Badge A" in message
    assert "Letters A" in message


def test_badge_unlock_speech_message_without_names() -> None:
    message = badge_unlock_speech_message([])
    assert "new badge" in message.lower()
