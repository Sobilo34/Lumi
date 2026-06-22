"""Per-word recognition tracking and adaptive Word Garden target selection."""
from __future__ import annotations

import random
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from config import PROJECT_DIR
from engine.word_object_tiles import BOXED_WORD_GARDEN_WORDS, is_boxed_object_tile_path, word_garden_objects_dir
from engine.adaptive_ai import log_ai_decision

WORD_MASTERY_THRESHOLD = 0.80
WORD_CONSECUTIVE_CORRECT_FOR_MASTERY = 2
WORD_MASTERY_GAIN_CORRECT = 0.18
WORD_MASTERY_GAIN_FIRST_TRY_BONUS = 0.12
WORD_MASTERY_PENALTY_WRONG = 0.14
WORD_MASTERY_PENALTY_HINT = 0.05
WORD_RECENTLY_SEEN_SECONDS = 90

# Fallback when no boxed object tiles are installed yet.
WORD_GARDEN_WORDS_DEFAULT: tuple[str, ...] = BOXED_WORD_GARDEN_WORDS


def empty_word_mastery_record() -> dict[str, Any]:
    return {
        "attempts": 0,
        "correct": 0,
        "wrong": 0,
        "first_try_correct": 0,
        "hints_used": 0,
        "mastery_score": 0.0,
        "last_seen": 0,
        "consecutive_correct": 0,
        "confused_with": {},
    }


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return dict(profile.get_profile())
    if isinstance(profile, dict):
        return profile
    raise TypeError("profile must be a mapping or expose get_profile()")


def _lower_word(word: str) -> str:
    return str(word or "").strip().lower()


def discover_installed_word_garden_words(chunks_root: Path | str | None = None) -> tuple[str, ...]:
    """Words with a shipped boxed object tile (1024² card frame, transparent corners)."""
    objects_dir = word_garden_objects_dir(chunks_root)
    if not objects_dir.is_dir():
        return WORD_GARDEN_WORDS_DEFAULT

    words: list[str] = []
    for object_path in sorted(objects_dir.glob("*.png")):
        word = object_path.stem.strip().lower()
        if not word:
            continue
        if is_boxed_object_tile_path(object_path):
            words.append(word)
    return tuple(words) if words else WORD_GARDEN_WORDS_DEFAULT


def ensure_word_mastery(profile: Any) -> dict[str, dict[str, Any]]:
    if hasattr(profile, "word_mastery"):
        mastery = profile.word_mastery
    elif isinstance(profile, dict):
        mastery = profile.setdefault("word_mastery", {})
    else:
        raise TypeError("profile must expose word_mastery or be a mapping")

    if not isinstance(mastery, dict):
        mastery = {}
    for word in discover_installed_word_garden_words():
        record = mastery.get(word)
        if not isinstance(record, dict):
            mastery[word] = empty_word_mastery_record()
            continue
        merged = empty_word_mastery_record()
        merged.update(record)
        if not isinstance(merged.get("confused_with"), dict):
            merged["confused_with"] = {}
        mastery[word] = merged

    if hasattr(profile, "word_mastery"):
        profile.word_mastery = mastery
    return mastery


def get_word_mastery_record(profile: Any, word: str) -> dict[str, Any]:
    key = _lower_word(word)
    mastery = ensure_word_mastery(profile)
    if key not in mastery:
        mastery[key] = empty_word_mastery_record()
    return mastery[key]


def is_word_mastered_record(record: dict[str, Any]) -> bool:
    score = float(record.get("mastery_score", 0.0) or 0.0)
    streak = int(record.get("consecutive_correct", 0) or 0)
    return score >= WORD_MASTERY_THRESHOLD or streak >= WORD_CONSECUTIVE_CORRECT_FOR_MASTERY


def is_word_mastered(profile: Any, word: str) -> bool:
    return is_word_mastered_record(get_word_mastery_record(profile, word))


def record_word_confusion(profile: Any, target: str, selected: str) -> None:
    target_word = _lower_word(target)
    selected_word = _lower_word(selected)
    if not target_word or not selected_word or target_word == selected_word:
        return
    record = get_word_mastery_record(profile, target_word)
    confused_with = record.setdefault("confused_with", {})
    confused_with[selected_word] = int(confused_with.get(selected_word, 0)) + 1
    log_ai_decision(
        "word_confusion",
        f"{target_word} confused with {selected_word} (count={confused_with[selected_word]})",
    )
    if hasattr(profile, "save_profile"):
        profile.save_profile()


def graduate_mastered_word(profile: Any, word: str) -> None:
    key = _lower_word(word)
    if not key or not is_word_mastered(profile, key):
        return
    if hasattr(profile, "weak_words"):
        profile.weak_words.pop(key, None)
    elif isinstance(profile, dict):
        weak = profile.get("weak_words", {})
        if isinstance(weak, dict):
            weak.pop(key, None)
    if hasattr(profile, "mark_word_mastered"):
        mastered = list(getattr(profile, "mastered_words", []) or [])
        if key not in mastered:
            profile.mark_word_mastered(key)
    elif isinstance(profile, dict):
        mastered = list(profile.get("mastered_words", []))
        if key not in mastered:
            mastered.append(key)
            profile["mastered_words"] = mastered
    log_ai_decision("word_review", f"{key} graduated — rotating to new vocabulary")


def update_word_mastery(
    profile: Any,
    word: str,
    *,
    correct: bool,
    first_try: bool = False,
    hints_used: int = 0,
) -> dict[str, Any]:
    key = _lower_word(word)
    record = get_word_mastery_record(profile, key)
    record["attempts"] = int(record.get("attempts", 0)) + 1
    record["last_seen"] = int(time.time())
    record["hints_used"] = int(record.get("hints_used", 0)) + max(0, int(hints_used))

    score = float(record.get("mastery_score", 0.0) or 0.0)
    if correct:
        record["correct"] = int(record.get("correct", 0)) + 1
        record["consecutive_correct"] = int(record.get("consecutive_correct", 0)) + 1
        score += WORD_MASTERY_GAIN_CORRECT
        if first_try:
            record["first_try_correct"] = int(record.get("first_try_correct", 0)) + 1
            score += WORD_MASTERY_GAIN_FIRST_TRY_BONUS
        log_ai_decision(
            "word_mastery",
            f"{key} correct (first_try={first_try}, hints={hints_used}) -> score {score:.2f}",
        )
    else:
        record["wrong"] = int(record.get("wrong", 0)) + 1
        record["consecutive_correct"] = 0
        score -= WORD_MASTERY_PENALTY_WRONG
        log_ai_decision("word_mastery", f"{key} wrong -> score {score:.2f}")

    if hints_used > 0:
        score -= WORD_MASTERY_PENALTY_HINT * hints_used

    record["mastery_score"] = _clamp_score(score)
    if is_word_mastered_record(record):
        graduate_mastered_word(profile, key)

    if hasattr(profile, "save_profile"):
        profile.save_profile()
    return record


def _selection_weight(
    word: str,
    profile: Any,
    *,
    last_target: str,
    now: int,
) -> float:
    data = _profile_dict(profile)
    mastered = {_lower_word(item) for item in data.get("mastered_words", [])}
    weak_words = data.get("weak_words", {})
    weak_count = int(weak_words.get(word, 0) or 0) if isinstance(weak_words, dict) else 0
    record = get_word_mastery_record(profile, word)
    mastery_score = float(record.get("mastery_score", 0.0) or 0.0)
    attempts = int(record.get("attempts", 0) or 0)
    last_seen = int(record.get("last_seen", 0) or 0)

    weight = 1.0
    if attempts == 0:
        weight += 3.0
    if word not in mastered:
        weight += 2.0
    weight += max(0.0, 1.0 - mastery_score) * 2.5
    if weak_count > 0:
        weight += min(weak_count * 0.35, 1.75)
    if last_seen and now - last_seen < WORD_RECENTLY_SEEN_SECONDS:
        weight *= 0.12
    if word == last_target:
        weight *= 0.02
    if word in mastered and mastery_score >= WORD_MASTERY_THRESHOLD:
        weight *= 0.35
    return max(weight, 0.05)


def _strongest_review_word(profile: Any, candidates: list[str]) -> str:
    """Return the most-missed, not-yet-mastered word in ``candidates`` (or "")."""
    weak_words = _profile_dict(profile).get("weak_words", {})
    if not isinstance(weak_words, dict):
        return ""
    scored: list[tuple[int, str]] = []
    for word in candidates:
        key = _lower_word(word)
        weak_count = int(weak_words.get(key, 0) or 0)
        if weak_count < 2:
            continue
        record = get_word_mastery_record(profile, key)
        if float(record.get("mastery_score", 0.0) or 0.0) >= WORD_MASTERY_THRESHOLD:
            continue
        scored.append((weak_count, key))
    if not scored:
        return ""
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1]


def pick_word_garden_target(
    profile: Any,
    pool: tuple[str, ...],
    *,
    last_target: str = "",
    rng: random.Random | None = None,
) -> tuple[str, str]:
    """Weighted random target selection. Returns (word, reason)."""
    words = tuple(_lower_word(word) for word in pool if _lower_word(word))
    if not words:
        words = WORD_GARDEN_WORDS_DEFAULT

    randomizer = rng or random.Random()
    now = int(time.time())
    last = _lower_word(last_target)
    candidates = [word for word in words if word != last] or list(words)

    # Always review a word the child keeps missing before exploring new ones.
    review_word = _strongest_review_word(profile, candidates)
    if review_word:
        log_ai_decision(
            "word_pick",
            f"target={review_word} reason=word_review pool={len(words)} last={last or '-'}",
        )
        return review_word, "word_review"

    weights = [_selection_weight(word, profile, last_target=last, now=now) for word in candidates]
    target = randomizer.choices(candidates, weights=weights, k=1)[0]

    record = get_word_mastery_record(profile, target)
    weak_words = _profile_dict(profile).get("weak_words", {})
    weak_count = int(weak_words.get(target, 0) or 0) if isinstance(weak_words, dict) else 0
    attempts = int(record.get("attempts", 0) or 0)

    if weak_count >= 2 and float(record.get("mastery_score", 0.0) or 0.0) < WORD_MASTERY_THRESHOLD:
        reason = "word_review"
    elif attempts == 0:
        reason = "word_new"
    elif is_word_mastered(profile, target):
        reason = "word_refresh"
    else:
        reason = "word_curriculum"

    log_ai_decision(
        "word_pick",
        f"target={target} reason={reason} pool={len(words)} last={last or '-'}",
    )
    return target, reason


def pick_word_distractors(
    target: str,
    pool: tuple[str, ...],
    *,
    count: int,
    confusable_words: tuple[str, ...] = (),
    rng: random.Random | None = None,
) -> list[str]:
    """Pick distractor cards, preferring confusable vocabulary when available."""
    randomizer = rng or random.Random()
    target_word = _lower_word(target)
    available = [_lower_word(word) for word in pool if _lower_word(word) and _lower_word(word) != target_word]
    if not available:
        available = [_lower_word(word) for word in WORD_GARDEN_WORDS_DEFAULT if _lower_word(word) != target_word]

    chosen: list[str] = []
    for word in confusable_words:
        key = _lower_word(word)
        if key and key != target_word and key in available and key not in chosen:
            chosen.append(key)
    shuffled = list(available)
    randomizer.shuffle(shuffled)
    for word in shuffled:
        if len(chosen) >= count:
            break
        if word not in chosen:
            chosen.append(word)
    return chosen[:count]
