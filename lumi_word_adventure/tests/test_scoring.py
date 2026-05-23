from engine.scoring import calculate_accuracy, calculate_stars, check_badge_unlocks, update_score


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
    profile = {
        "total_stars": 20,
        "mastered_letters": ["A", "B", "C", "D", "E", "F"],
        "mastered_words": ["cat", "dog", "sun", "ball", "apple"],
        "completed_worlds": ["voice_challenge", "sentence_castle"],
        "badges": [],
    }

    unlocked = check_badge_unlocks(profile)

    assert "Letter Hero" in unlocked
    assert "Word Explorer" in unlocked
    assert "Brave Speaker" in unlocked
    assert "Sentence Builder" in unlocked
    assert "B and D Master" in unlocked
    assert "Great Learner" in unlocked
