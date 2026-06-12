"""Teacher and parent report helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any

REPORTS_DIR = Path(__file__).resolve().parent
SESSION_REPORTS_DIR = REPORTS_DIR / "session_reports"

SCREEN_BD_PRACTICE = "10_letter_bd_practice"
SCREEN_WORD_GARDEN = "11_word_garden_gameplay"
SCREEN_SENTENCE_CASTLE = "17_sentence_castle_gameplay"
SCREEN_WORLD_MAP = "06_world_map"

ENGINE_SCREEN_MAP: dict[str, str] = {
    SCREEN_BD_PRACTICE: "bd_practice",
    SCREEN_WORD_GARDEN: "word_garden_game",
    SCREEN_SENTENCE_CASTLE: "sentence_castle_game",
    SCREEN_WORLD_MAP: "world_map",
}


def _profile_dict(profile: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return dict(profile.get_profile())
    if isinstance(profile, dict):
        return dict(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def _count_map(values: Any) -> dict[str, int]:
    """Normalize weak-skill counters from dict, list, or missing values."""
    if not values:
        return {}
    if isinstance(values, dict):
        counts: dict[str, int] = {}
        for key, count in values.items():
            name = str(key).strip()
            if not name:
                continue
            try:
                counts[name] = max(0, int(count or 0))
            except (TypeError, ValueError):
                counts[name] = 0
        return counts
    if isinstance(values, list):
        counts = {}
        for item in values:
            name = str(item).strip()
            if name:
                counts[name] = counts.get(name, 0) + 1
        return counts
    return {}


def _letter_count(counts: dict[str, int], letter: str) -> int:
    target = letter.upper()
    total = 0
    for key, count in counts.items():
        if str(key).strip().upper() == target:
            total += max(0, int(count))
    return total


def calculate_accuracy(profile: dict[str, Any] | Any) -> int:
    data = _profile_dict(profile)
    attempts = int(data.get("attempts", 0) or 0)
    correct_answers = int(data.get("correct_answers", 0) or 0)
    if attempts <= 0:
        stored = data.get("accuracy", 0)
        try:
            return int(round(float(stored or 0)))
        except (TypeError, ValueError):
            return 0
    return int(round((max(0, correct_answers) / attempts) * 100))


def get_strong_skill(profile: dict[str, Any] | Any) -> str:
    data = _profile_dict(profile)
    mastered_letters = _count_map(data.get("mastered_letters"))
    mastered_words = _count_map(data.get("mastered_words"))
    sentence_errors = _count_map(data.get("sentence_errors"))

    if isinstance(data.get("mastered_letters"), list):
        letter_score = len(data.get("mastered_letters") or [])
    else:
        letter_score = len(mastered_letters)

    if isinstance(data.get("mastered_words"), list):
        word_score = len(data.get("mastered_words") or [])
    else:
        word_score = len(mastered_words)

    sentence_score = max(0, 3 - len(sentence_errors))
    mastery_counts = [
        ("Letter recognition", letter_score),
        ("Word reading", word_score),
        ("Sentence building", sentence_score),
    ]
    strongest = max(mastery_counts, key=lambda item: item[1])
    if strongest[1] <= 0:
        return "Practice in progress"
    return strongest[0]


def get_weak_area(profile: dict[str, Any] | Any) -> str:
    recommendation = get_recommendation(profile)
    activity = str(recommendation.get("activity", "")).strip()
    if activity == "World Map":
        return "None"
    if activity == "B/D Practice":
        return "Letters B and D"
    if activity.startswith("Word Garden"):
        return "Word: Cat"
    if activity == "Sentence Castle":
        return "Sentence order"
    return "General practice"


def get_recommendation(profile: dict[str, Any] | Any) -> dict[str, str]:
    data = _profile_dict(profile)
    weak_letters = _count_map(data.get("weak_letters"))
    weak_words = _count_map(data.get("weak_words"))
    sentence_errors = _count_map(data.get("sentence_errors"))

    if _letter_count(weak_letters, "B") >= 2 or _letter_count(weak_letters, "D") >= 2:
        return {
            "activity": "B/D Practice",
            "screen_id": SCREEN_BD_PRACTICE,
        }

    cat_count = 0
    for key, count in weak_words.items():
        if str(key).strip().lower() == "cat":
            cat_count += max(0, int(count))
    if cat_count >= 2:
        return {
            "activity": "Word Garden: Cat",
            "screen_id": SCREEN_WORD_GARDEN,
        }

    word_order_count = 0
    for key, count in sentence_errors.items():
        if str(key).strip().lower() in {"word_order", "sentence_order", "order"}:
            word_order_count += max(0, int(count))
    if word_order_count >= 1:
        return {
            "activity": "Sentence Castle",
            "screen_id": SCREEN_SENTENCE_CASTLE,
        }

    return {
        "activity": "World Map",
        "screen_id": SCREEN_WORLD_MAP,
    }


def resolve_engine_screen_id(screen_id: str) -> str:
    """Map MCP screen ids to in-game registry screen ids."""
    return ENGINE_SCREEN_MAP.get(screen_id, screen_id)


def save_session_report(report: dict[str, Any], output_path: str | Path | None = None) -> str:
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    else:
        SESSION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SESSION_REPORTS_DIR / f"session_report_{timestamp}.json"

    with path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return str(path)


def generate_report(profile: dict[str, Any] | Any, output_path: str | Path | None = None) -> dict[str, Any]:
    data = _profile_dict(profile)
    weak_letters = _count_map(data.get("weak_letters"))
    weak_words = _count_map(data.get("weak_words"))
    sentence_errors = _count_map(data.get("sentence_errors"))
    recommendation = get_recommendation(data)

    report: dict[str, Any] = {
        "child_name": str(data.get("child_name", "Player 1") or "Player 1"),
        "stars_earned": int(data.get("total_stars", data.get("stars", 0)) or 0),
        "accuracy_percent": calculate_accuracy(data),
        "strong_skill": get_strong_skill(data),
        "needs_practice": get_weak_area(data),
        "weak_letters": weak_letters,
        "weak_words": weak_words,
        "sentence_errors": sentence_errors,
        "recommended_next_activity": recommendation["activity"],
        "recommended_screen_id": recommendation["screen_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "attempts": int(data.get("attempts", 0) or 0),
        "correct_answers": int(data.get("correct_answers", 0) or 0),
        "difficulty": int(data.get("difficulty", 1) or 1),
    }

    saved_path = save_session_report(report, output_path=output_path)
    report["session_report_path"] = saved_path
    return report
