"""World map unlock rules: Letter Island → Word Garden → Sentence Castle."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from engine.personal_tutor import ALPHABET

WORLD_LETTER_ISLAND = "letter_island"
WORLD_WORD_GARDEN = "word_garden"
WORLD_SENTENCE_CASTLE = "sentence_castle"

WORLD_PRACTICE_ENTRY: dict[str, str] = {
    WORLD_LETTER_ISLAND: "letter_island_game",
    WORLD_WORD_GARDEN: "word_garden_game",
    WORLD_SENTENCE_CASTLE: "sentence_castle_game",
}

WORD_GARDEN_REQUIRED_WORDS = ("cat", "dog", "sun", "ball")

SCREEN_TO_WORLD = {
    "word_garden_game": WORLD_WORD_GARDEN,
    "word_correct_feedback": WORLD_WORD_GARDEN,
    "word_mistake_hint": WORLD_WORD_GARDEN,
    "sentence_castle_game": WORLD_SENTENCE_CASTLE,
    "sentence_dragging": WORLD_SENTENCE_CASTLE,
    "sentence_mistake_hint": WORLD_SENTENCE_CASTLE,
    "sentence_correct_feedback": WORLD_SENTENCE_CASTLE,
}


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return deepcopy(profile.get_profile())
    if isinstance(profile, dict):
        return deepcopy(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def _completed_worlds(profile: Any) -> set[str]:
    data = _profile_dict(profile)
    raw = data.get("completed_worlds", [])
    return {str(item).strip() for item in raw if str(item).strip()}


def _persist_profile(profile: Any) -> None:
    if hasattr(profile, "save_profile") and callable(profile.save_profile):
        profile.save_profile()


def mark_world_complete(profile: Any, world_id: str) -> bool:
    """Record a world as completed; returns True if newly marked."""
    key = str(world_id or "").strip()
    if not key:
        return False
    if hasattr(profile, "completed_worlds"):
        worlds = list(profile.completed_worlds or [])
        if key in worlds:
            return False
        worlds.append(key)
        profile.completed_worlds = worlds
        _persist_profile(profile)
        return True
    if isinstance(profile, dict):
        worlds = list(profile.get("completed_worlds", []))
        if key in worlds:
            return False
        worlds.append(key)
        profile["completed_worlds"] = worlds
        return True
    return False


def letter_island_complete(profile: Any) -> bool:
    if WORLD_LETTER_ISLAND in _completed_worlds(profile):
        return True
    data = _profile_dict(profile)
    mastered = {str(item).upper() for item in data.get("mastered_letters", [])}
    index = int(data.get("current_letter_index", 0) or 0)
    if "Z" in mastered and index >= len(ALPHABET) - 1:
        return True
    return len(mastered) >= len(ALPHABET)


def word_garden_complete(profile: Any) -> bool:
    if WORLD_WORD_GARDEN in _completed_worlds(profile):
        return True
    data = _profile_dict(profile)
    mastered = {str(item).lower() for item in data.get("mastered_words", [])}
    return all(word in mastered for word in WORD_GARDEN_REQUIRED_WORDS)


def word_garden_unlocked(profile: Any) -> bool:
    return letter_island_complete(profile)


def sentence_castle_unlocked(profile: Any) -> bool:
    return word_garden_complete(profile)


def world_unlocked(profile: Any, world_id: str) -> bool:
    key = str(world_id or "").strip()
    if key == WORLD_LETTER_ISLAND:
        return True
    if key == WORLD_WORD_GARDEN:
        return word_garden_unlocked(profile)
    if key == WORLD_SENTENCE_CASTLE:
        return sentence_castle_unlocked(profile)
    return True


def screen_accessible(profile: Any, screen_id: str) -> bool:
    world_id = SCREEN_TO_WORLD.get(str(screen_id or "").strip())
    if world_id is None:
        return True
    return world_unlocked(profile, world_id)


def locked_world_message(screen_id: str) -> str:
    world_id = SCREEN_TO_WORLD.get(str(screen_id or "").strip(), "")
    if world_id == WORLD_WORD_GARDEN:
        return "Complete Letter Island before unlocking Word Garden!"
    if world_id == WORLD_SENTENCE_CASTLE:
        return "Complete Word Garden before unlocking Sentence Castle!"
    return "Complete the previous level to unlock this area."


def sync_world_completion(profile: Any) -> list[str]:
    """Backfill completed_worlds from existing letter/word progress."""
    newly_completed: list[str] = []
    if letter_island_complete(profile) and mark_world_complete(profile, WORLD_LETTER_ISLAND):
        newly_completed.append(WORLD_LETTER_ISLAND)
    if word_garden_complete(profile) and mark_world_complete(profile, WORLD_WORD_GARDEN):
        newly_completed.append(WORLD_WORD_GARDEN)
    return newly_completed


def maybe_complete_letter_island(profile: Any, *, letter: str, curriculum: bool = True) -> bool:
    if not curriculum or str(letter or "").upper() != "Z":
        return False
    if not letter_island_complete(profile):
        return False
    return mark_world_complete(profile, WORLD_LETTER_ISLAND)


def maybe_complete_word_garden(profile: Any) -> bool:
    if not word_garden_complete(profile):
        return False
    return mark_world_complete(profile, WORLD_WORD_GARDEN)


def latest_completed_world(profile: Any) -> str:
    """Most recently finished world on the map path (for Practice Again)."""
    worlds = _completed_worlds(profile)
    if WORLD_WORD_GARDEN in worlds:
        return WORLD_WORD_GARDEN
    if WORLD_LETTER_ISLAND in worlds:
        return WORLD_LETTER_ISLAND
    return WORLD_LETTER_ISLAND


def prepare_world_practice(profile: Any, world_id: str) -> str:
    """Reset a world's play cursor for replay; keeps completed_worlds and unlocks."""
    key = str(world_id or "").strip() or WORLD_LETTER_ISLAND
    if key == WORLD_LETTER_ISLAND and hasattr(profile, "current_letter_index"):
        profile.current_letter_index = 0
    elif key == WORLD_WORD_GARDEN and hasattr(profile, "current_word_length"):
        profile.current_word_length = 3
    elif key == WORLD_SENTENCE_CASTLE and hasattr(profile, "sentence_level"):
        profile.sentence_level = 0
    _persist_profile(profile)
    return WORLD_PRACTICE_ENTRY.get(key, "letter_island_game")


def world_map_progress_text(profile: Any) -> str:
    if not word_garden_unlocked(profile):
        return "Complete Letter Island (A–Z) to unlock Word Garden"
    if not sentence_castle_unlocked(profile):
        return "Master cat, dog, sun, and ball to unlock Sentence Castle"
    return "All worlds unlocked — great journey!"
