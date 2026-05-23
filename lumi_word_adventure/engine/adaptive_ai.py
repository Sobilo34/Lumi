"""Rule-based adaptive tutoring helpers."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from config import MAX_DIFFICULTY, MIN_DIFFICULTY


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
        return "bd_confusion"
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


def choose_hint(profile: Any, activity_type: str, mistake_type: str) -> str:
    profile_dict = _profile_dict(profile)
    activity = _lower_text(activity_type)
    mistake = _lower_text(mistake_type)

    if activity == "letter":
        focus_letter = has_repeated_weak_letter(profile_dict)
        if mistake in {"bd_confusion", "visual_letter_confusion"} or focus_letter in {"B", "D"}:
            return "B has a belly. D has a drum."
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