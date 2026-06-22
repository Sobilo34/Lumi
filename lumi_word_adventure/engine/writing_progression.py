"""Writing Castle curriculum: letters A–Z, then Word Garden vocabulary."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from engine.adaptive_ai import ALPHABET
from engine.word_mastery import discover_installed_word_garden_words

WORLD_WRITING_CASTLE = "writing_castle"


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return deepcopy(profile.get_profile())
    if isinstance(profile, dict):
        return deepcopy(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def writing_castle_unlocked(profile: Any) -> bool:
    from engine.world_progression import letter_island_complete

    return letter_island_complete(profile)


def writing_word_pool() -> tuple[str, ...]:
    return discover_installed_word_garden_words()


def writing_mode_for_profile(profile: Any) -> str:
    data = _profile_dict(profile)
    letter_index = int(data.get("writing_letter_index", 0) or 0)
    if letter_index < len(ALPHABET):
        return "letters"
    return "words"


def build_writing_round(profile: Any) -> dict[str, str]:
    return build_writing_round_for_mode(profile, writing_mode_for_profile(profile))


def build_writing_round_for_mode(profile: Any, mode: str) -> dict[str, str]:
    data = _profile_dict(profile)
    mode_key = "words" if str(mode).strip().lower() == "words" else "letters"
    if mode_key == "letters":
        letter_index = int(data.get("writing_letter_index", 0) or 0)
        letter_index = max(0, min(letter_index, len(ALPHABET) - 1))
        letter = ALPHABET[letter_index]
        return {
            "mode": "letters",
            "target": letter,
            "prompt": f"Write the letter {letter}.",
            "speech": f"Write the letter {letter}.",
        }

    words = writing_word_pool()
    word_index = int(data.get("writing_word_index", 0) or 0)
    if not words:
        return {
            "mode": "words",
            "target": "cat",
            "prompt": "Write the word cat.",
            "speech": "Write the word cat.",
        }
    word_index = max(0, min(word_index, len(words) - 1))
    word = words[word_index]
    return {
        "mode": "words",
        "target": word,
        "prompt": f"Write the word {word}.",
        "speech": f"Write the word {word}.",
    }


def advance_writing_curriculum(profile: Any) -> None:
    data = _profile_dict(profile)
    mode = writing_mode_for_profile(profile)
    if mode == "letters":
        letter_index = int(data.get("writing_letter_index", 0) or 0)
        letter = ALPHABET[letter_index] if letter_index < len(ALPHABET) else "Z"
        mastered = {str(item).upper() for item in data.get("mastered_writing_letters", [])}
        mastered.add(letter)
        if hasattr(profile, "writing_letter_index"):
            profile.writing_letter_index = letter_index + 1
            profile.mastered_writing_letters = sorted(mastered)
        elif isinstance(profile, dict):
            profile["writing_letter_index"] = letter_index + 1
            profile["mastered_writing_letters"] = sorted(mastered)
        return

    words = writing_word_pool()
    word_index = int(data.get("writing_word_index", 0) or 0)
    if not words:
        return
    word = words[max(0, min(word_index, len(words) - 1))]
    mastered = {str(item).lower() for item in data.get("mastered_writing_words", [])}
    mastered.add(word.lower())
    next_index = word_index + 1
    if hasattr(profile, "writing_word_index"):
        profile.writing_word_index = next_index
        profile.mastered_writing_words = sorted(mastered)
    elif isinstance(profile, dict):
        profile["writing_word_index"] = next_index
        profile["mastered_writing_words"] = sorted(mastered)


def writing_castle_complete(profile: Any) -> bool:
    from engine.world_progression import _completed_worlds

    if WORLD_WRITING_CASTLE in _completed_worlds(profile):
        return True
    data = _profile_dict(profile)
    letter_index = int(data.get("writing_letter_index", 0) or 0)
    if letter_index < len(ALPHABET):
        return False
    words = writing_word_pool()
    if not words:
        return letter_index >= len(ALPHABET)
    word_index = int(data.get("writing_word_index", 0) or 0)
    mastered = {str(item).lower() for item in data.get("mastered_writing_words", [])}
    return word_index >= len(words) and all(word in mastered for word in words)


def maybe_complete_writing_castle(profile: Any) -> bool:
    from engine.world_progression import mark_world_complete

    if not writing_castle_complete(profile):
        return False
    return mark_world_complete(profile, WORLD_WRITING_CASTLE)


def writing_castle_progress_text(profile: Any) -> str:
    data = _profile_dict(profile)
    letter_index = int(data.get("writing_letter_index", 0) or 0)
    if letter_index < len(ALPHABET):
        letter = ALPHABET[min(letter_index, len(ALPHABET) - 1)]
        return f"Writing Castle — practice letter {letter}"
    words = writing_word_pool()
    word_index = int(data.get("writing_word_index", 0) or 0)
    if words and word_index < len(words):
        return f"Writing Castle — practice word {words[word_index]}"
    return "Writing Castle complete — amazing handwriting!"
