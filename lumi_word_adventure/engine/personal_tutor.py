"""Rule-based personal tutor: letter and word round building."""
from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

from engine.adaptive_ai import pick_letter_round_target, reset_review_spacing

ALPHABET = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
LETTER_SLOT_COUNT = 4
WORD_SLOT_COUNT = 4
VISIBLE_WORD_FALLBACK = ("cat", "dog", "sun", "ball")
# Four tap slots on 07_letter_island_gameplay.png — letters shown there change each round.
LETTER_ISLAND_SLOT_COUNT = 4


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return deepcopy(profile.get_profile())
    if isinstance(profile, dict):
        return deepcopy(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def _letter_entry(letter_bank: list[dict[str, Any]], letter: str) -> dict[str, Any]:
    target = letter.strip().upper()
    for entry in letter_bank:
        if str(entry.get("letter", "")).upper() == target:
            return entry
    return {"letter": target, "prompt": f"Find the letter {target}", "confusable_with": []}


def _next_curriculum_letter(profile: dict[str, Any]) -> str:
    index = int(profile.get("current_letter_index", 0) or 0)
    index = max(0, min(index, len(ALPHABET) - 1))
    return ALPHABET[index]


def build_letter_choices(target: str, letter_bank: list[dict[str, Any]], rng: random.Random | None = None) -> list[str]:
    randomizer = rng or random.Random()
    target = target.strip().upper()
    entry = _letter_entry(letter_bank, target)
    confusable = [str(item).upper() for item in entry.get("confusable_with", []) if str(item).strip()]
    pool = list(dict.fromkeys(confusable))
    try:
        target_idx = ALPHABET.index(target)
    except ValueError:
        target_idx = 0
    neighbors = [ALPHABET[max(0, target_idx - 1)], ALPHABET[min(len(ALPHABET) - 1, target_idx + 1)]]
    for neighbor in neighbors:
        if neighbor != target and neighbor not in pool:
            pool.append(neighbor)
    for letter in ALPHABET:
        if letter != target and letter not in pool:
            pool.append(letter)
        if len(pool) >= LETTER_SLOT_COUNT * 3:
            break
    randomizer.shuffle(pool)
    distractors = [letter for letter in pool if letter != target][: LETTER_SLOT_COUNT - 1]
    choices = distractors + [target]
    randomizer.shuffle(choices)
    return choices


def build_letter_round(
    profile: Any,
    letter_bank: list[dict[str, Any]],
) -> dict[str, Any]:
    profile_data = _profile_dict(profile)
    target, review_mode, reason = pick_letter_round_target(profile)
    if review_mode:
        reset_review_spacing(profile)
    entry = _letter_entry(letter_bank, target)
    choices = build_letter_choices(target, letter_bank)
    curriculum = _next_curriculum_letter(profile_data)
    example = str(entry.get("example_word") or "").strip()
    if example:
        prompt = f"Find the letter {target}. {target} is for {example}."
    else:
        prompt = f"Find the letter {target}."
    return {
        "target": target,
        "choices": choices,
        "prompt": prompt,
        "curriculum_letter": curriculum,
        "review_mode": review_mode,
        "reason": reason if review_mode else "letter_curriculum",
    }


def advance_letter_curriculum(profile: Any, *, mastered: bool, letter: str | None = None) -> str:
    if hasattr(profile, "get_profile"):
        data = profile.get_profile()
    else:
        data = _profile_dict(profile)
    index = int(data.get("current_letter_index", 0) or 0)
    if mastered:
        if letter:
            try:
                letter_index = ALPHABET.index(letter.strip().upper())
                index = max(index, min(len(ALPHABET) - 1, letter_index + 1))
            except ValueError:
                index = min(len(ALPHABET) - 1, index + 1)
        else:
            index = min(len(ALPHABET) - 1, index + 1)
    if hasattr(profile, "current_letter_index"):
        profile.current_letter_index = index
        if hasattr(profile, "save_profile"):
            profile.save_profile()
    return ALPHABET[min(index, len(ALPHABET) - 1)]


def _word_length(word: str) -> int:
    return len("".join(ch for ch in word.strip() if ch.isalpha()))


def _words_for_length(vocabulary: list[dict[str, Any]], length: int) -> list[dict[str, Any]]:
    words = []
    for entry in vocabulary:
        word = str(entry.get("word") or "").strip().lower()
        if not word:
            continue
        entry_length = int(entry.get("word_length") or _word_length(word))
        if entry_length == length:
            words.append(entry)
    return words


def build_word_round(profile: Any, vocabulary: list[dict[str, Any]], visible_words: tuple[str, ...] = VISIBLE_WORD_FALLBACK) -> dict[str, Any]:
    profile_data = _profile_dict(profile)
    length_level = int(profile_data.get("current_word_length", 3) or 3)
    length_level = max(2, min(length_level, 6))

    weak_words = profile_data.get("weak_words", {})
    review_word = None
    if isinstance(weak_words, dict):
        repeated = [(word.lower(), int(count)) for word, count in weak_words.items() if int(count or 0) >= 2]
        repeated.sort(key=lambda item: (-item[1], item[0]))
        if repeated:
            review_word = repeated[0][0]

    pool = _words_for_length(vocabulary, length_level)
    if not pool:
        pool = list(vocabulary)

    target_entry = None
    if review_word:
        target_entry = next((entry for entry in pool if str(entry.get("word", "")).lower() == review_word), None)
    if target_entry is None and pool:
        mastered = {str(word).lower() for word in profile_data.get("mastered_words", [])}
        unmastered = [entry for entry in pool if str(entry.get("word", "")).lower() not in mastered]
        target_entry = (unmastered or pool)[0]

    target_word = str((target_entry or {}).get("word") or "cat").lower()
    if target_word not in visible_words:
        visible_list = list(visible_words)
        fallback = next((word for word in visible_list if word != target_word), visible_list[0])
        distractor_pool = [entry for entry in pool if str(entry.get("word", "")).lower() in visible_words]
        if any(str(entry.get("word", "")).lower() == target_word for entry in pool):
            pass
        elif distractor_pool:
            target_word = str(distractor_pool[0].get("word")).lower()

    prompt = str((target_entry or {}).get("prompt") or f"Touch the {target_word}").strip()
    if not prompt.endswith((".", "!", "?")):
        prompt = f"{prompt}."

    choice_pool = [str(entry.get("word")).lower() for entry in pool if str(entry.get("word", "")).lower() in visible_words]
    choice_pool = list(dict.fromkeys(choice_pool))
    if target_word not in choice_pool:
        choice_pool.append(target_word)
    for word in visible_words:
        if word not in choice_pool:
            choice_pool.append(word)
        if len(choice_pool) >= WORD_SLOT_COUNT:
            break
    randomizer = random.Random(target_word + str(length_level))
    randomizer.shuffle(choice_pool)
    choices = choice_pool[:WORD_SLOT_COUNT]
    if target_word not in choices:
        choices[-1] = target_word
        randomizer.shuffle(choices)

    return {
        "target": target_word,
        "choices": choices,
        "prompt": prompt,
        "word_length": length_level,
        "reason": "word_review" if review_word else "word_curriculum",
    }


def advance_word_length(profile: Any, *, mastered: bool) -> int:
    current = int(getattr(profile, "current_word_length", 3) or 3)
    if mastered and current < 6:
        current += 1
    if hasattr(profile, "current_word_length"):
        profile.current_word_length = current
        if hasattr(profile, "save_profile"):
            profile.save_profile()
    return current


