"""Word Garden vocabulary pool and round building."""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from engine.word_mastery import (
    WORD_GARDEN_WORDS_DEFAULT,
    discover_installed_word_garden_words,
    pick_word_distractors,
    pick_word_garden_target,
)

# Back-compat alias — prefer discover_installed_word_garden_words() at runtime.
WORD_GARDEN_WORDS = WORD_GARDEN_WORDS_DEFAULT

WORD_SLOT_COUNT = 4


def get_word_garden_pool(chunks_root: Path | str | None = None) -> tuple[str, ...]:
    return discover_installed_word_garden_words(chunks_root)


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return dict(profile.get_profile())
    if isinstance(profile, dict):
        return dict(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def _confusable_for_target(target: str, vocabulary_data: Any) -> tuple[str, ...]:
    target_word = str(target or "").strip().lower()
    if not target_word or vocabulary_data is None:
        return ()
    entries = vocabulary_data if isinstance(vocabulary_data, list) else []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("word") or "").strip().lower() != target_word:
            continue
        confusable = entry.get("confusable_with") or []
        if isinstance(confusable, list):
            return tuple(str(item).strip().lower() for item in confusable if str(item).strip())
    return ()


def build_word_garden_round_for_target(
    profile: Any,
    target_word: str,
    *,
    pool: tuple[str, ...] | None = None,
    vocabulary_data: Any = None,
    last_target: str = "",
) -> dict[str, Any]:
    """Build a four-card round with a specific target word."""
    words = tuple(str(word).strip().lower() for word in (pool or get_word_garden_pool()) if str(word).strip())
    target = str(target_word or "").strip().lower()
    if target not in words:
        target = words[0] if words else "sun"
    randomizer = random.Random()
    distractors = pick_word_distractors(
        target,
        words,
        count=WORD_SLOT_COUNT - 1,
        confusable_words=_confusable_for_target(target, vocabulary_data),
        rng=randomizer,
    )
    choices = [target, *distractors]
    randomizer.shuffle(choices)
    return {
        "target": target,
        "choices": choices,
        "prompt": f"Touch the {target.capitalize()}.",
        "reason": "word_practice",
    }


def build_word_garden_round(
    profile: Any,
    *,
    pool: tuple[str, ...] | None = None,
    vocabulary_data: Any = None,
    last_target: str = "",
) -> dict[str, Any]:
    """Pick an adaptive target word and four object-card choices."""
    words = tuple(str(word).strip().lower() for word in (pool or get_word_garden_pool()) if str(word).strip())
    if not words:
        words = WORD_GARDEN_WORDS_DEFAULT

    randomizer = random.Random()
    target_word, reason = pick_word_garden_target(
        profile,
        words,
        last_target=last_target,
        rng=randomizer,
    )
    distractors = pick_word_distractors(
        target_word,
        words,
        count=WORD_SLOT_COUNT - 1,
        confusable_words=_confusable_for_target(target_word, vocabulary_data),
        rng=randomizer,
    )
    choices = [target_word, *distractors]
    randomizer.shuffle(choices)
    return {
        "target": target_word,
        "choices": choices,
        "prompt": f"Touch the {target_word.capitalize()}.",
        "reason": reason,
    }
