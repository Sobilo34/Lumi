"""Rule-based adaptive tutoring helpers."""
from __future__ import annotations

import time
from copy import deepcopy
from typing import Any

from config import MAX_DIFFICULTY, MIN_DIFFICULTY

ALPHABET = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# --- Letter mastery & spaced-review tuning ---------------------------------
MASTERY_THRESHOLD = 0.80
CONSECUTIVE_CORRECT_FOR_MASTERY = 2
REVIEW_INTERVAL_LETTERS = 3
MASTERY_GAIN_CORRECT = 0.15
MASTERY_GAIN_FIRST_TRY_BONUS = 0.10
MASTERY_PENALTY_WRONG = 0.12
MASTERY_PENALTY_HINT = 0.05
REVIEW_WEAK_MASTERY_CUTOFF = 0.55

# Visual confusion groups used by the mistake-diagnosis AI.
_CONFUSION_GROUP_SPECS: tuple[tuple[str, str], ...] = (
    ("B", "DPR"),
    ("M", "WN"),
    ("C", "GO"),
    ("E", "F"),
    ("I", "LT"),
    ("O", "QCD"),
)


def _build_confusable_map() -> dict[str, frozenset[str]]:
    mapping: dict[str, set[str]] = {}
    for anchor, others in _CONFUSION_GROUP_SPECS:
        group = {anchor, *others}
        for letter in group:
            mapping.setdefault(letter, set()).update(group - {letter})
    return {letter: frozenset(partners) for letter, partners in mapping.items()}


CONFUSABLE_LETTERS = _build_confusable_map()


def log_ai_decision(category: str, message: str) -> None:
    """Console trace for demos and debugging."""
    print(f"[Lumi AI:{category}] {message}")


def empty_letter_mastery_record() -> dict[str, Any]:
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


def default_letter_mastery_map() -> dict[str, dict[str, Any]]:
    return {letter: empty_letter_mastery_record() for letter in ALPHABET}


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 3)))


def ensure_letter_mastery(profile: Any) -> dict[str, dict[str, Any]]:
    if hasattr(profile, "letter_mastery"):
        mastery = profile.letter_mastery
    elif isinstance(profile, dict):
        mastery = profile.setdefault("letter_mastery", default_letter_mastery_map())
    else:
        raise TypeError("profile must expose letter_mastery or be a mapping")

    if not isinstance(mastery, dict):
        mastery = default_letter_mastery_map()
    for letter in ALPHABET:
        record = mastery.get(letter)
        if not isinstance(record, dict):
            mastery[letter] = empty_letter_mastery_record()
            continue
        merged = empty_letter_mastery_record()
        merged.update(record)
        if not isinstance(merged.get("confused_with"), dict):
            merged["confused_with"] = {}
        mastery[letter] = merged

    if hasattr(profile, "letter_mastery"):
        profile.letter_mastery = mastery
    return mastery


def get_letter_mastery_record(profile: Any, letter: str) -> dict[str, Any]:
    key = _upper_text(letter)
    mastery = ensure_letter_mastery(profile)
    return mastery[key]


def is_letter_mastered_record(record: dict[str, Any]) -> bool:
    score = float(record.get("mastery_score", 0.0) or 0.0)
    streak = int(record.get("consecutive_correct", 0) or 0)
    return score >= MASTERY_THRESHOLD or streak >= CONSECUTIVE_CORRECT_FOR_MASTERY


def is_letter_mastered(profile: Any, letter: str) -> bool:
    return is_letter_mastered_record(get_letter_mastery_record(profile, letter))


def all_letters_mastered(profile: Any) -> bool:
    """True when every A–Z letter is perfected in the mastery model or mastered list."""
    profile_dict = _profile_dict(profile)
    mastered = {str(item).upper() for item in profile_dict.get("mastered_letters", [])}
    if mastered >= set(ALPHABET):
        return True
    return all(is_letter_mastered(profile, letter) for letter in ALPHABET)


def record_letter_confusion(profile: Any, target: str, selected: str) -> None:
    target_letter = _upper_text(target)
    selected_letter = _upper_text(selected)
    if not target_letter or not selected_letter or target_letter == selected_letter:
        return

    record = get_letter_mastery_record(profile, target_letter)
    confused_with = record.setdefault("confused_with", {})
    confused_with[selected_letter] = int(confused_with.get(selected_letter, 0)) + 1
    log_ai_decision(
        "confusion",
        f"{target_letter} confused with {selected_letter} "
        f"(count={confused_with[selected_letter]})",
    )
    if hasattr(profile, "save_profile"):
        profile.save_profile()


def update_letter_mastery(
    profile: Any,
    letter: str,
    *,
    correct: bool,
    first_try: bool = False,
    hints_used: int = 0,
) -> dict[str, Any]:
    """Update per-letter mastery stats and score."""
    key = _upper_text(letter)
    record = get_letter_mastery_record(profile, key)
    record["attempts"] = int(record.get("attempts", 0)) + 1
    record["last_seen"] = int(time.time())
    record["hints_used"] = int(record.get("hints_used", 0)) + max(0, int(hints_used))

    score = float(record.get("mastery_score", 0.0) or 0.0)
    if correct:
        record["correct"] = int(record.get("correct", 0)) + 1
        record["consecutive_correct"] = int(record.get("consecutive_correct", 0)) + 1
        score += MASTERY_GAIN_CORRECT
        if first_try:
            record["first_try_correct"] = int(record.get("first_try_correct", 0)) + 1
            score += MASTERY_GAIN_FIRST_TRY_BONUS
        log_ai_decision(
            "mastery",
            f"{key} correct (first_try={first_try}, hints={hints_used}) "
            f"-> score {score:.2f}",
        )
    else:
        record["wrong"] = int(record.get("wrong", 0)) + 1
        record["consecutive_correct"] = 0
        score -= MASTERY_PENALTY_WRONG
        log_ai_decision("mastery", f"{key} wrong -> score {score:.2f}")

    if hints_used > 0:
        score -= MASTERY_PENALTY_HINT * hints_used
        log_ai_decision("mastery", f"{key} hint penalty ({hints_used}) -> score {score:.2f}")

    record["mastery_score"] = _clamp_score(score)
    mastered_now = is_letter_mastered_record(record)
    if mastered_now:
        log_ai_decision(
            "mastery",
            f"{key} mastered (score={record['mastery_score']:.2f}, "
            f"streak={record['consecutive_correct']})",
        )
        graduate_mastered_letter(profile, key)

    if hasattr(profile, "save_profile"):
        profile.save_profile()
    return record


def graduate_mastered_letter(profile: Any, letter: str) -> None:
    """Remove a mastered letter from review queues so curriculum can move on."""
    key = _upper_text(letter)
    if not key or not is_letter_mastered(profile, key):
        return

    if hasattr(profile, "weak_letters"):
        profile.weak_letters.pop(key, None)
    elif isinstance(profile, dict):
        weak = profile.get("weak_letters", {})
        if isinstance(weak, dict):
            weak.pop(key, None)

    if hasattr(profile, "mark_letter_mastered"):
        profile.mark_letter_mastered(key)
    elif isinstance(profile, dict):
        mastered = list(profile.get("mastered_letters", []))
        if key not in mastered:
            mastered.append(key)
            profile["mastered_letters"] = mastered

    log_ai_decision("review", f"{key} graduated — no more spaced review for this letter")


def sync_mastered_letters_from_mastery(profile: Any) -> list[str]:
    """Promote letters into mastered_letters when the AI model says they are mastered."""
    newly_mastered: list[str] = []
    for letter in ALPHABET:
        if not is_letter_mastered(profile, letter):
            continue
        if hasattr(profile, "mark_letter_mastered"):
            before = set(getattr(profile, "mastered_letters", []) or [])
            profile.mark_letter_mastered(letter)
            after = set(getattr(profile, "mastered_letters", []) or [])
            if letter in after and letter not in before:
                newly_mastered.append(letter)
        elif isinstance(profile, dict):
            mastered = list(profile.get("mastered_letters", []))
            if letter not in mastered:
                mastered.append(letter)
                profile["mastered_letters"] = mastered
                newly_mastered.append(letter)
    return newly_mastered


def _review_priority(profile: Any, letter: str) -> float:
    if is_letter_mastered(profile, letter):
        return 0.0
    profile_dict = _profile_dict(profile)
    record = profile_dict.get("letter_mastery", {}).get(letter, {})
    if not isinstance(record, dict):
        return 0.0
    attempts = int(record.get("attempts", 0) or 0)
    if attempts <= 0:
        return 0.0

    mastery_gap = 1.0 - float(record.get("mastery_score", 0.0) or 0.0)
    wrong = int(record.get("wrong", 0) or 0)
    confused = sum(int(count) for count in (record.get("confused_with") or {}).values())
    return mastery_gap * 2.0 + wrong * 0.35 + confused * 0.5


def should_insert_spaced_review(profile: Any) -> bool:
    profile_dict = _profile_dict(profile)
    since_review = int(profile_dict.get("curriculum_letters_since_review", 0) or 0)
    if since_review >= REVIEW_INTERVAL_LETTERS:
        log_ai_decision(
            "review",
            f"Spaced review due after {since_review} curriculum letters",
        )
        return True

    weak_letters = profile_dict.get("weak_letters", {})
    if isinstance(weak_letters, dict):
        for letter, count in weak_letters.items():
            key = str(letter).upper()
            if int(count or 0) >= 2 and not is_letter_mastered(profile, key):
                log_ai_decision(
                    "review",
                    f"Weak letter {key} needs review (count={count})",
                )
                return True

    mastery = profile_dict.get("letter_mastery", {})
    if isinstance(mastery, dict):
        for letter, record in mastery.items():
            if not isinstance(record, dict):
                continue
            if is_letter_mastered(profile, str(letter).upper()):
                continue
            if int(record.get("wrong", 0) or 0) >= 2 and float(record.get("mastery_score", 0.0) or 0.0) < REVIEW_WEAK_MASTERY_CUTOFF:
                log_ai_decision(
                    "review",
                    f"Weak letter {letter} needs review "
                    f"(wrong={record.get('wrong')}, score={record.get('mastery_score')})",
                )
                return True
    return False


def select_review_letter(profile: Any) -> tuple[str | None, str]:
    """Pick a weak previously-seen letter for spaced review."""
    profile_dict = _profile_dict(profile)
    curriculum_index = int(profile_dict.get("current_letter_index", 0) or 0)
    curriculum_index = max(0, min(curriculum_index, len(ALPHABET) - 1))

    candidates: list[tuple[float, int, str]] = []

    weak_letters = profile_dict.get("weak_letters", {})
    if isinstance(weak_letters, dict):
        for letter, count in weak_letters.items():
            key = str(letter).upper()
            if key not in ALPHABET or int(count or 0) < 2:
                continue
            if is_letter_mastered(profile, key):
                continue
            letter_index = ALPHABET.index(key)
            candidates.append((int(count) * 1.5, -letter_index, key))

    for index, letter in enumerate(ALPHABET):
        if index >= curriculum_index:
            break
        if is_letter_mastered(profile, letter):
            continue
        priority = _review_priority(profile, letter)
        if priority > 0:
            candidates.append((priority, -index, letter))

    if not candidates:
        log_ai_decision("review", "No unmastered review candidates — continuing curriculum")
        return None, "no_review_candidates"

    candidates.sort(reverse=True)
    chosen = candidates[0][2]
    reason = "low_mastery_score"
    record = profile_dict.get("letter_mastery", {}).get(chosen, {})
    if isinstance(record, dict):
        if int(record.get("wrong", 0) or 0) >= 2:
            reason = "repeated_wrong_attempts"
        confused = record.get("confused_with") or {}
        if isinstance(confused, dict) and sum(int(v) for v in confused.values()) >= 2:
            reason = "high_confusion_count"

    log_ai_decision("review", f"Selected review letter {chosen} ({reason})")
    return chosen, reason


def pick_letter_round_target(profile: Any) -> tuple[str, bool, str]:
    """Choose curriculum or spaced-review target for the next letter round."""
    profile_dict = _profile_dict(profile)
    if should_insert_spaced_review(profile):
        review_letter, reason = select_review_letter(profile)
        if review_letter:
            return review_letter, True, reason

    index = int(profile_dict.get("current_letter_index", 0) or 0)
    index = max(0, min(index, len(ALPHABET) - 1))
    letter = ALPHABET[index]
    log_ai_decision("curriculum", f"Continuing A–Z at letter {letter}")
    return letter, False, "letter_curriculum"


def note_curriculum_letter_completed(profile: Any) -> None:
    """Track spacing between spaced-review insertions."""
    if hasattr(profile, "curriculum_letters_since_review"):
        profile.curriculum_letters_since_review = int(profile.curriculum_letters_since_review or 0) + 1
        if hasattr(profile, "save_profile"):
            profile.save_profile()
        log_ai_decision(
            "review",
            f"Curriculum letters since last review: {profile.curriculum_letters_since_review}",
        )
    elif isinstance(profile, dict):
        profile["curriculum_letters_since_review"] = int(profile.get("curriculum_letters_since_review", 0)) + 1


def reset_review_spacing(profile: Any) -> None:
    if hasattr(profile, "curriculum_letters_since_review"):
        profile.curriculum_letters_since_review = 0
        if hasattr(profile, "save_profile"):
            profile.save_profile()
    elif isinstance(profile, dict):
        profile["curriculum_letters_since_review"] = 0


class LetterMasteryPredictor:
    """Placeholder for a future neural-network mastery predictor."""

    def predict_mastery(self, features: dict[str, Any]) -> float:
        return float(features.get("mastery_score", 0.0) or 0.0)

    def predict_review_priority(self, features: dict[str, Any]) -> float:
        mastery_gap = 1.0 - float(features.get("mastery_score", 0.0) or 0.0)
        wrong = float(features.get("wrong", 0) or 0)
        confused = float(features.get("confusion_total", 0) or 0)
        return mastery_gap * 2.0 + wrong * 0.35 + confused * 0.5


# --- Existing adaptive helpers ------------------------------------------------


def _profile_dict(profile: Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return deepcopy(profile.get_profile())
    if isinstance(profile, dict):
        return profile
    raise TypeError("profile must be a mapping or expose get_profile()")


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _upper_text(value: Any) -> str:
    return _normalize_text(value).upper()


def _lower_text(value: Any) -> str:
    return _normalize_text(value).lower()


def _hint_usage_total(profile: dict[str, Any]) -> int:
    hint_usage = profile.get("hint_usage", {})
    if not isinstance(hint_usage, dict):
        return 0
    return sum(max(0, int(count)) for count in hint_usage.values())


def _profile_difficulty(profile: dict[str, Any]) -> int:
    return int(profile.get("difficulty", MIN_DIFFICULTY))


def _iter_questions(question_bank: Any) -> list[dict[str, Any]]:
    if isinstance(question_bank, dict):
        return [item for item in question_bank.values() if isinstance(item, dict)]
    if isinstance(question_bank, list):
        return [item for item in question_bank if isinstance(item, dict)]
    return []


def _question_type(question: dict[str, Any]) -> str:
    if "letter" in question:
        return "letter"
    if "word" in question or "speech_prompt" in question:
        return "word"
    if "sentence" in question or "words" in question:
        return "sentence"
    return "unknown"


def _question_difficulty(question: dict[str, Any]) -> int:
    try:
        return int(question.get("difficulty", 0))
    except (TypeError, ValueError):
        return 0


def _pick_closest_question(questions: list[dict[str, Any]], difficulty: int) -> dict[str, Any]:
    if not questions:
        return {}

    return min(
        enumerate(questions),
        key=lambda item: (
            abs(_question_difficulty(item[1]) - difficulty),
            _question_difficulty(item[1]),
            item[0],
        ),
    )[1]


def _pick_easiest_question(questions: list[dict[str, Any]]) -> dict[str, Any]:
    if not questions:
        return {}

    return min(
        enumerate(questions),
        key=lambda item: (
            _question_difficulty(item[1]),
            item[0],
        ),
    )[1]


def diagnose_letter_mistake(target: str, selected: str) -> str:
    target_letter = _upper_text(target)
    selected_letter = _upper_text(selected)

    if not target_letter or not selected_letter:
        return "letter_confusion"
    if target_letter == selected_letter:
        return "correct"
    if {target_letter, selected_letter} == {"B", "D"}:
        log_ai_decision("diagnosis", f"Visual B/D confusion: wanted {target_letter}, tapped {selected_letter}")
        return "bd_confusion"
    if selected_letter in CONFUSABLE_LETTERS.get(target_letter, frozenset()):
        log_ai_decision(
            "diagnosis",
            f"Visual confusion group: wanted {target_letter}, tapped {selected_letter}",
        )
        return "visual_confusion"
    log_ai_decision(
        "diagnosis",
        f"General letter confusion: wanted {target_letter}, tapped {selected_letter}",
    )
    return "letter_confusion"


def diagnose_word_mistake(target: str, selected: str, vocabulary_data: Any) -> str:
    target_word = _lower_text(target)
    selected_word = _lower_text(selected)
    if not target_word or not selected_word:
        return "word_confusion"
    if target_word == selected_word:
        return "correct"
    if {target_word, selected_word} == {"cat", "dog"}:
        return "same_category_vocabulary_confusion"

    vocabulary = _iter_questions(vocabulary_data)
    confusable_map: dict[str, set[str]] = {}
    for entry in vocabulary:
        word = _lower_text(entry.get("word"))
        if not word:
            continue
        confusable_map[word] = {_lower_text(item) for item in entry.get("confusable_with", [])}

    if selected_word in confusable_map.get(target_word, set()) or target_word in confusable_map.get(selected_word, set()):
        return "word_confusion"

    return "word_confusion"


def diagnose_sentence_mistake(target_words: list[str], submitted_words: list[str]) -> str:
    normalized_target = [_normalize_text(word) for word in target_words if _normalize_text(word)]
    normalized_submitted = [_normalize_text(word) for word in submitted_words if _normalize_text(word)]

    if not normalized_target or not normalized_submitted:
        return "sentence_order"
    if normalized_target == normalized_submitted:
        return "correct"
    if sorted(word.lower() for word in normalized_target) == sorted(word.lower() for word in normalized_submitted):
        return "word_order"
    return "sentence_order"


def should_increase_difficulty(profile: Any) -> bool:
    profile_dict = _profile_dict(profile)
    if _hint_usage_total(profile_dict) >= 3:
        return False
    return int(profile_dict.get("correct_streak", 0)) >= 3


def should_decrease_difficulty(profile: Any) -> bool:
    profile_dict = _profile_dict(profile)
    return int(profile_dict.get("wrong_streak", 0)) >= 2


def has_repeated_weak_letter(profile: Any) -> str:
    profile_dict = _profile_dict(profile)
    weak_letters = profile_dict.get("weak_letters", {})
    if not isinstance(weak_letters, dict):
        return ""

    repeated_letters = [
        (letter.upper(), int(count))
        for letter, count in weak_letters.items()
        if int(count) >= 2
    ]
    if not repeated_letters:
        return ""

    repeated_letters.sort(key=lambda item: (-item[1], item[0]))
    return repeated_letters[0][0]


def has_repeated_weak_word(profile: Any) -> str:
    profile_dict = _profile_dict(profile)
    weak_words = profile_dict.get("weak_words", {})
    if not isinstance(weak_words, dict):
        return ""

    repeated_words = [
        (_lower_text(word), int(count))
        for word, count in weak_words.items()
        if int(count) >= 2
    ]
    if not repeated_words:
        return ""

    repeated_words.sort(key=lambda item: (-item[1], item[0]))
    return repeated_words[0][0]


def _letter_focus_recommendation(profile: dict[str, Any], question_bank: Any) -> dict[str, Any]:
    questions = [question for question in _iter_questions(question_bank) if _question_type(question) == "letter"]
    focus_letter = has_repeated_weak_letter(profile)

    if focus_letter:
        if focus_letter in {"B", "D"}:
            return {
                "activity": "bd_practice",
                "focus": "B/D",
                "reason": "repeated_b_d_confusion",
                "question": None,
            }

        matching_questions = [question for question in questions if _upper_text(question.get("letter")) == focus_letter]
        if matching_questions:
            chosen = _pick_easiest_question(matching_questions)
            return {
                "activity": "letter_island_game",
                "focus": focus_letter,
                "reason": "repeated_weak_letter",
                "question": chosen,
            }

    if should_decrease_difficulty(profile):
        chosen = _pick_easiest_question(questions)
    elif should_increase_difficulty(profile):
        chosen = _pick_closest_question(questions, min(MAX_DIFFICULTY, _profile_difficulty(profile) + 1))
    else:
        chosen = _pick_closest_question(questions, _profile_difficulty(profile))

    return {
        "activity": "letter_island_game",
        "focus": _upper_text(chosen.get("letter")) if chosen else "",
        "reason": "adaptive_letter_selection",
        "question": chosen,
    }


def _word_focus_recommendation(profile: dict[str, Any], question_bank: Any) -> dict[str, Any]:
    questions = [question for question in _iter_questions(question_bank) if _question_type(question) == "word"]
    focus_word = has_repeated_weak_word(profile)

    if focus_word:
        matching_questions = [question for question in questions if _lower_text(question.get("word")) == focus_word]
        if matching_questions:
            chosen = _pick_easiest_question(matching_questions)
            if focus_word in {"cat", "dog"}:
                return {
                    "activity": "word_garden_game",
                    "focus": focus_word,
                    "reason": "cat_dog_confusion",
                    "support": "simplified_word_garden",
                    "option_count": 2,
                    "option_pool": ["cat", "dog"],
                    "question": chosen,
                }
            return {
                "activity": "word_garden_game",
                "focus": focus_word,
                "reason": "repeated_weak_word",
                "question": chosen,
            }

    if should_decrease_difficulty(profile):
        chosen = _pick_easiest_question(questions)
    elif should_increase_difficulty(profile):
        chosen = _pick_closest_question(questions, min(MAX_DIFFICULTY, _profile_difficulty(profile) + 1))
    else:
        chosen = _pick_closest_question(questions, _profile_difficulty(profile))

    support = "simplified_word_garden" if _lower_text(chosen.get("word")) in {"cat", "dog"} else ""
    reason = "adaptive_word_selection"
    if _lower_text(chosen.get("word")) in {"cat", "dog"}:
        reason = "cat_dog_confusion"

    return {
        "activity": "word_garden_game",
        "focus": _lower_text(chosen.get("word")) if chosen else "",
        "reason": reason,
        "support": support,
        "option_count": 2 if support else 4,
        "option_pool": ["cat", "dog"] if support else [],
        "question": chosen,
    }


def _sentence_focus_recommendation(profile: dict[str, Any], question_bank: Any) -> dict[str, Any]:
    questions = [question for question in _iter_questions(question_bank) if _question_type(question) == "sentence"]
    word_order_errors = int(profile.get("sentence_errors", {}).get("word_order", 0)) if isinstance(profile.get("sentence_errors", {}), dict) else 0

    chosen = _pick_closest_question(questions, _profile_difficulty(profile))
    support = ""
    reason = "adaptive_sentence_selection"

    if word_order_errors >= 2:
        chosen = _pick_easiest_question(questions)
        support = "ghost_hints"
        reason = "word_order_support"

    if should_decrease_difficulty(profile):
        chosen = _pick_easiest_question(questions)
        support = support or "ghost_hints"
        reason = reason if reason == "word_order_support" else "reduced_sentence_difficulty"
    elif should_increase_difficulty(profile):
        chosen = _pick_closest_question(questions, min(MAX_DIFFICULTY, _profile_difficulty(profile) + 1))

    return {
        "activity": "sentence_castle_game",
        "focus": _normalize_text(chosen.get("sentence")) if chosen else "",
        "reason": reason,
        "support": support,
        "question": chosen,
    }


def recommend_practice(profile: Any) -> dict[str, Any]:
    profile_dict = _profile_dict(profile)

    repeated_letter = has_repeated_weak_letter(profile_dict)
    if repeated_letter:
        if repeated_letter in {"B", "D"}:
            return {
                "activity": "bd_practice",
                "focus": "B/D",
                "reason": "repeated_b_d_confusion",
                "question": None,
            }
        return {
            "activity": "letter_island_game",
            "focus": repeated_letter,
            "reason": "repeated_weak_letter",
            "question": None,
        }

    repeated_word = has_repeated_weak_word(profile_dict)
    if repeated_word:
        return {
            "activity": "word_garden_game",
            "focus": repeated_word,
            "reason": "cat_dog_confusion" if repeated_word in {"cat", "dog"} else "repeated_weak_word",
            "support": "simplified_word_garden" if repeated_word in {"cat", "dog"} else "",
            "option_count": 2 if repeated_word in {"cat", "dog"} else 4,
            "option_pool": ["cat", "dog"] if repeated_word in {"cat", "dog"} else [],
            "question": None,
        }

    sentence_errors = profile_dict.get("sentence_errors", {})
    if isinstance(sentence_errors, dict) and int(sentence_errors.get("word_order", 0)) >= 2:
        return {
            "activity": "sentence_castle_game",
            "focus": "word_order",
            "reason": "word_order_support",
            "support": "ghost_hints",
            "question": None,
        }

    if should_decrease_difficulty(profile_dict):
        return {
            "activity": "review",
            "focus": "easier",
            "reason": "wrong_streak",
            "question": None,
        }

    if should_increase_difficulty(profile_dict):
        return {
            "activity": "advance",
            "focus": "harder",
            "reason": "correct_streak",
            "question": None,
        }

    return {
        "activity": "continue",
        "focus": "current",
        "reason": "balanced_progress",
        "question": None,
    }


def choose_hint(profile: Any, activity_type: str, mistake_type: str, *, target: str = "", selected: str = "") -> str:
    profile_dict = _profile_dict(profile)
    activity = _lower_text(activity_type)
    mistake = _lower_text(mistake_type)

    if activity == "letter":
        from engine.feedback import get_letter_mistake_hint

        hint = get_letter_mistake_hint(
            mistake,
            target=target,
            selected=selected,
            hint_level=1,
        )
        if hint:
            return hint
        focus_letter = has_repeated_weak_letter(profile_dict)
        if focus_letter:
            return f"Look closely for {focus_letter}."
        return "Look for the letter again."

    if activity == "word":
        focus_word = has_repeated_weak_word(profile_dict)
        if mistake in {"cat_dog_confusion", "same_category_vocabulary_confusion"} or focus_word in {"cat", "dog"}:
            return "Cat says meow. Dog says woof."
        if focus_word:
            return f"Look for the word {focus_word}."
        return "Look for the word again."

    if activity == "sentence":
        if mistake == "word_order":
            return "Start with the first word and put the sentence in order."
        return "Put the words in order."

    return "Try again with a careful look."


def choose_next_question(profile: Any, question_bank: Any, activity_type: str) -> dict[str, Any]:
    profile_dict = _profile_dict(profile)
    activity = _lower_text(activity_type)

    if activity == "letter":
        recommendation = _letter_focus_recommendation(profile_dict, question_bank)
        if recommendation.get("question") is None and recommendation["activity"] != "bd_practice":
            questions = [question for question in _iter_questions(question_bank) if _question_type(question) == "letter"]
            recommendation["question"] = _pick_closest_question(questions, _profile_difficulty(profile_dict))
        return recommendation

    if activity == "word":
        return _word_focus_recommendation(profile_dict, question_bank)

    if activity == "sentence":
        return _sentence_focus_recommendation(profile_dict, question_bank)

    return {
        "activity": activity_type,
        "focus": "",
        "reason": "unsupported_activity",
        "question": None,
    }


class AdaptiveAI:
    def choose_next_activity(self, learner: Any) -> str:
        recommendation = recommend_practice(learner)
        return str(recommendation.get("activity", "continue"))

    def update_after_attempt(
        self,
        learner: Any,
        is_correct: bool,
        skill_key: str | None = None,
    ) -> Any:
        if hasattr(learner, "attempts"):
            learner.attempts = int(learner.attempts) + 1

        if is_correct:
            if hasattr(learner, "correct_answers"):
                learner.correct_answers = int(learner.correct_answers) + 1
            learner.update_correct_streak()
            if skill_key and hasattr(learner, "weak_letters"):
                learner.weak_letters.pop(_upper_text(skill_key), None)
            if should_increase_difficulty(learner):
                learner.difficulty = min(MAX_DIFFICULTY, int(learner.difficulty) + 1)
        else:
            learner.update_wrong_streak()
            if skill_key and hasattr(learner, "record_weak_letter"):
                learner.record_weak_letter(skill_key)
            if should_decrease_difficulty(learner):
                learner.difficulty = max(MIN_DIFFICULTY, int(learner.difficulty) - 1)

        if hasattr(learner, "save_profile"):
            learner.save_profile()
        return learner