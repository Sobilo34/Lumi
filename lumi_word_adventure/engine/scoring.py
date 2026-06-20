"""Non-punitive scoring helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from engine.adaptive_ai import all_letters_mastered

# Letter Island curriculum milestones shown on 21_badge_unlock.png.
LETTER_MILESTONE_BADGES: dict[str, str] = {
    "Badge A": "J",
    "Badge B": "T",
    "Badge C": "Z",
}

LETTER_ISLAND_COMPLETE_BADGE = "Letter Island Complete"

BADGE_DISPLAY_SUBTITLES: dict[str, str] = {
    "Badge A": "Letters A–J Complete!",
    "Badge B": "Letter T Mastered!",
    "Badge C": "Letters U–Z Complete!",
    "Letter Island Complete": "All letters A–Z mastered! Word Garden unlocked!",
    "B and D Master": "You mastered B and D!",
    "Word Explorer": "You mastered 5 words!",
    "Brave Speaker": "You finished the voice challenge!",
    "Sentence Builder": "You built sentences in the castle!",
    "Great Learner": "You earned 20 stars!",
}

BADGE_ICON_FILES: dict[str, str] = {
    "Badge A": "badge_a.png",
    "Badge B": "badge_b.png",
    "Badge C": "badge_c.png",
    "Letter Island Complete": "letter_island_complete.png",
    "B and D Master": "b_and_d_master.png",
    "Word Explorer": "word_explorer.png",
    "Brave Speaker": "brave_speaker.png",
    "Sentence Builder": "sentence_builder.png",
    "Great Learner": "great_learner.png",
}


BADGE_DEFINITIONS: dict[str, Callable[[dict[str, Any]], bool]] = {
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


def check_letter_milestone_badges(
    profile: Any,
    mastered_letter: str,
    *,
    curriculum: bool = True,
) -> list[str]:
    """Unlock Badge A/B/C when the learner completes J, T, or Z in curriculum mode."""
    if not curriculum:
        return []
    letter = str(mastered_letter or "").strip().upper()
    badge_name = next(
        (name for name, milestone in LETTER_MILESTONE_BADGES.items() if milestone == letter),
        None,
    )
    if badge_name is None:
        return []

    profile_dict = _profile_dict(profile)
    if badge_name in profile_dict.get("badges", []):
        return []

    if hasattr(profile, "add_badge") and callable(profile.add_badge):
        profile.add_badge(badge_name)
    elif isinstance(profile, dict):
        badges = list(profile.get("badges", []))
        if badge_name not in badges:
            badges.append(badge_name)
            profile["badges"] = badges

    _persist_profile(profile)
    return [badge_name]


def check_letter_island_complete_badge(profile: Any) -> list[str]:
    """Award the finale badge when every letter A–Z has been perfected."""
    profile_dict = _profile_dict(profile)
    if LETTER_ISLAND_COMPLETE_BADGE in profile_dict.get("badges", []):
        return []
    if not all_letters_mastered(profile):
        return []

    if hasattr(profile, "add_badge") and callable(profile.add_badge):
        profile.add_badge(LETTER_ISLAND_COMPLETE_BADGE)
    elif isinstance(profile, dict):
        badges = list(profile.get("badges", []))
        if LETTER_ISLAND_COMPLETE_BADGE not in badges:
            badges.append(LETTER_ISLAND_COMPLETE_BADGE)
            profile["badges"] = badges

    _persist_profile(profile)
    return [LETTER_ISLAND_COMPLETE_BADGE]


def badge_subtitle(badge_name: str) -> str:
    return BADGE_DISPLAY_SUBTITLES.get(badge_name.strip(), "Great work!")


def badge_unlock_speech_message(badge_names: list[str] | tuple[str, ...] | None) -> str:
    """Voice line for badge unlock (plays after the badge SFX)."""
    msg = "Hooray! You unlocked a new badge!"
    names = [str(name).strip() for name in (badge_names or []) if str(name).strip()]
    if not names:
        return msg
    if len(names) == 1:
        badge_name = names[0]
        return f"You unlocked {badge_name}. {badge_subtitle(badge_name)}"
    joined = ", ".join(names)
    return f"You unlocked {joined}. {badge_subtitle(names[-1])}"


def badge_icon_filename(badge_name: str) -> str:
    return BADGE_ICON_FILES.get(badge_name.strip(), "great_learner.png")


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
