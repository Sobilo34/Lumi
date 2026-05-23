from engine.scoring import award_stars, calculate_stars


def test_calculate_stars_for_perfect_first_try_answer() -> None:
    assert calculate_stars(True, attempts=1, hints_used=0) == 3


def test_calculate_stars_reduces_for_hints_and_attempts() -> None:
    assert calculate_stars(True, attempts=2, hints_used=1) == 1


def test_award_stars_adds_non_negative_values() -> None:
    assert award_stars(2, 1) == 3
    assert award_stars(2, -4) == 2
