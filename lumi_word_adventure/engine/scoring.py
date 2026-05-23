"""Non-punitive scoring helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


BADGE_DEFINITIONS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "Letter Hero": lambda profile: len(profile.get("mastered_letters", [])) >= 5,
    "Word Explorer": lambda profile: len(profile.get("mastered_words", [])) >= 5,
    "Brave Speaker": lambda profile: "voice_challenge" in profile.get("completed_worlds", []),
    "Sentence Builder": lambda profile: "sentence_castle" in profile.get("completed_worlds", []),
    "B and D Master": lambda profile: {"B", "D"}.issubset(set(profile.get("mastered_letters", []))),
    "Great Learner": lambda profile: int(profile.get("total_stars", 0)) >= 20,
}


def calculate_stars(is_correct: bool, hints_used: int) -> int:
    if not is_correct:
        return 0
    if hints_used <= 0:
        return 3
    if hints_used == 1:
        return 2
    return 1


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return deepcopy(profile.get_profile())
    if isinstance(profile, dict):
        return profile
    raise TypeError("profile must be a mapping or expose get_profile()")


def _persist_profile(profile: Any) -> None:
    if hasattr(profile, "save_profile") and callable(profile.save_profile):
        profile.save_profile()


def update_score(profile: Any, stars_earned: int) -> int:
    stars_to_add = max(0, int(stars_earned))

    if hasattr(profile, "add_stars") and callable(profile.add_stars):
        return int(profile.add_stars(stars_to_add))

    profile_dict = _profile_dict(profile)
    current_stars = int(profile_dict.get("total_stars", profile_dict.get("stars", 0)))
    profile_dict["total_stars"] = current_stars + stars_to_add
    profile_dict["stars"] = profile_dict["total_stars"]
    _persist_profile(profile)
    return profile_dict["total_stars"]


def calculate_accuracy(correct_count: int, total_attempts: int) -> float:
    if total_attempts <= 0:
        return 0.0
    return round((max(0, correct_count) / total_attempts) * 100, 2)


def check_badge_unlocks(profile: Any) -> list[str]:
    profile_dict = _profile_dict(profile)
    badges = list(profile_dict.get("badges", []))
    unlocked: list[str] = []

    for badge_name, condition in BADGE_DEFINITIONS.items():
        if condition(profile_dict) and badge_name not in badges:
            badges.append(badge_name)
            unlocked.append(badge_name)
            if hasattr(profile, "add_badge") and callable(profile.add_badge):
                profile.add_badge(badge_name)

    if isinstance(profile, dict):
        profile["badges"] = badges
    _persist_profile(profile)
    return unlocked


def award_stars(current_stars: int, earned_stars: int) -> int:
    return max(0, current_stars + max(0, earned_stars))
