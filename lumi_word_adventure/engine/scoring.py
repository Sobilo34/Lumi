"""Non-punitive scoring helpers."""
from __future__ import annotations

from config import MAX_STARS, MIN_DIFFICULTY


def calculate_stars(correct: bool, attempts: int = 1, hints_used: int = 0) -> int:
    if not correct:
        return 0

    stars = MAX_STARS
    if attempts > 1:
        stars -= 1
    if hints_used > 0:
        stars -= min(hints_used, 2)
    return max(MIN_DIFFICULTY, min(MAX_STARS, stars))


def award_stars(current_stars: int, earned_stars: int) -> int:
    return max(0, current_stars + max(0, earned_stars))
