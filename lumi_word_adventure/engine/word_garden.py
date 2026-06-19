"""Word Garden vocabulary pool and round building."""
from __future__ import annotations

import random
from typing import Any

# Object + prompt PNGs installed under assets/ui_chunks/word_garden_game/.
WORD_GARDEN_WORDS: tuple[str, ...] = (
    "cat",
    "dog",
    "sun",
    "ball",
    "hat",
    "fish",
    "tree",
    "apple",
    "bird",
    "cup",
    "frog",
    "star",
    "duck",
)

WORD_SLOT_COUNT = 4


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return dict(profile.get_profile())
    if isinstance(profile, dict):
        return dict(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def build_word_garden_round_for_target(
    profile: Any,
    target_word: str,
    *,
    pool: tuple[str, ...] = WORD_GARDEN_WORDS,
) -> dict[str, Any]:
    """Build a four-card round with a specific target word."""
    words = tuple(str(word).strip().lower() for word in pool if str(word).strip())
    target = str(target_word or "").strip().lower()
    if target not in words:
        target = words[0] if words else "cat"
    distractors = [word for word in words if word != target]
    randomizer = random.Random(target)
    randomizer.shuffle(distractors)
    choices = [target, *distractors[: WORD_SLOT_COUNT - 1]]
    randomizer.shuffle(choices)
    return {
        "target": target,
        "choices": choices,
        "prompt": f"Touch the {target}.",
        "reason": "word_practice",
    }


def build_word_garden_round(profile: Any, *, pool: tuple[str, ...] = WORD_GARDEN_WORDS) -> dict[str, Any]:
    """Pick a target word and four object-card choices from the Word Garden pool."""
    words = tuple(str(word).strip().lower() for word in pool if str(word).strip())
    if not words:
        words = ("cat", "dog", "sun", "ball")

    data = _profile_dict(profile)
    mastered = {str(item).lower() for item in data.get("mastered_words", [])}
    weak_words = data.get("weak_words", {})

    target_word: str | None = None
    if isinstance(weak_words, dict):
        repeated = [(word.lower(), int(count)) for word, count in weak_words.items() if int(count or 0) >= 2]
        repeated.sort(key=lambda item: (-item[1], item[0]))
        for candidate, _count in repeated:
            if candidate in words:
                target_word = candidate
                break

    if target_word is None:
        unmastered = [word for word in words if word not in mastered]
        target_word = (unmastered or list(words))[0]

    distractors = [word for word in words if word != target_word]
    randomizer = random.Random(f"{target_word}:{len(mastered)}")
    randomizer.shuffle(distractors)
    choices = [target_word, *distractors[: WORD_SLOT_COUNT - 1]]
    randomizer.shuffle(choices)

    reason = "word_review" if isinstance(weak_words, dict) and int(weak_words.get(target_word, 0) or 0) >= 2 else "word_curriculum"
    prompt = f"Touch the {target_word}."
    return {
        "target": target_word,
        "choices": choices,
        "prompt": prompt,
        "reason": reason,
    }
