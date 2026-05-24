"""Teacher and parent report helpers."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from typing import Any


REPORTS_DIR = Path(__file__).resolve().parent
SESSION_REPORTS_DIR = REPORTS_DIR / "session_reports"


def _profile_dict(profile: dict[str, Any] | Any) -> dict[str, Any]:
    if hasattr(profile, "get_profile") and callable(profile.get_profile):
        return dict(profile.get_profile())
    if isinstance(profile, dict):
        return dict(profile)
    raise TypeError("profile must be a mapping or expose get_profile()")


def _normalize_list(values: Any, *, lower: bool = False) -> list[str]:
    if not values:
        return []
    items = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        items.append(text.lower() if lower else text)
    return items


def _accuracy(profile: dict[str, Any]) -> float:
    attempts = int(profile.get("attempts", 0) or 0)
    correct_answers = int(profile.get("correct_answers", 0) or 0)
    if attempts <= 0:
        return float(profile.get("accuracy", 0.0) or 0.0)
    return round((max(0, correct_answers) / attempts) * 100, 2)


def get_strong_skill(profile: dict[str, Any] | Any) -> str:
    data = _profile_dict(profile)
    mastery_counts = [
        ("Letter recognition", len(_normalize_list(data.get("mastered_letters")))),
        ("Word reading", len(_normalize_list(data.get("mastered_words"), lower=True))),
        ("Sentence building", max(0, 3 - len(_normalize_list(data.get("sentence_errors"), lower=True)))),
    ]
    strongest = max(mastery_counts, key=lambda item: item[1])
    if strongest[1] <= 0:
        return "Practice in progress"
    return strongest[0]


def get_weak_area(profile: dict[str, Any] | Any) -> str:
    data = _profile_dict(profile)
    weak_letters = _normalize_list(data.get("weak_letters"))
    weak_words = _normalize_list(data.get("weak_words"), lower=True)
    sentence_errors = _normalize_list(data.get("sentence_errors"), lower=True)

    if any(letter in {"B", "D"} for letter in weak_letters):
        return "Letters B and D"
    if weak_words:
        return f"Words: {weak_words[0].capitalize()}"
    if sentence_errors:
        return "Sentence order"
    if weak_letters:
        return f"Letter {weak_letters[0]}"
    return "General practice"


def get_recommendation(profile: dict[str, Any] | Any) -> str:
    data = _profile_dict(profile)
    weak_letters = _normalize_list(data.get("weak_letters"))
    weak_words = _normalize_list(data.get("weak_words"), lower=True)
    sentence_errors = _normalize_list(data.get("sentence_errors"), lower=True)

    if any(letter in {"B", "D"} for letter in weak_letters):
        return "Practice B/D"
    if weak_words:
        return f"Practice word: {weak_words[0].capitalize()}"
    if sentence_errors:
        return "Practice sentence order"
    return "Practice weak skills"


def _save_session_report(report: dict[str, Any], output_path: str | Path | None = None) -> Path | None:
    try:
        if output_path is not None:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            SESSION_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            child_name = str(report.get("child_name", "player")).strip().replace(" ", "_") or "player"
            path = SESSION_REPORTS_DIR / f"session_report_{child_name}_{timestamp}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        return path
    except Exception:
        return None


def generate_report(profile: dict[str, Any] | Any, output_path: str | Path | None = None) -> dict:
    data = _profile_dict(profile)
    report = {
        "child_name": data.get("child_name", "Player 1"),
        "stars": int(data.get("total_stars", data.get("stars", 0)) or 0),
        "accuracy": _accuracy(data),
        "strongest_skill": get_strong_skill(data),
        "weak_letters": _normalize_list(data.get("weak_letters")),
        "weak_words": _normalize_list(data.get("weak_words"), lower=True),
        "sentence_issue": "word order" if _normalize_list(data.get("sentence_errors"), lower=True) else "none",
        "recommended_next_activity": get_recommendation(data),
        "difficulty": int(data.get("difficulty", 1) or 1),
        "attempts": int(data.get("attempts", 0) or 0),
        "correct_answers": int(data.get("correct_answers", 0) or 0),
    }
    saved_path = _save_session_report(report, output_path)
    if saved_path is not None:
        report["session_report_path"] = str(saved_path)
    return report
