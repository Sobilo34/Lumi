"""Local learner profile model backed by JSON files."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import json

from config import PROFILES_DIR
from data_loader import load_default_profile, load_json_file


class LearnerModel:
    PROFILE_FILENAME = "player_1.json"
    _PROFILE_FIELDS = (
        "child_name",
        "total_stars",
        "lumi_energy",
        "current_world",
        "difficulty",
        "correct_streak",
        "wrong_streak",
        "weak_letters",
        "weak_words",
        "sentence_errors",
        "hint_usage",
        "mastered_letters",
        "mastered_words",
        "completed_worlds",
        "badges",
        "attempts",
        "correct_answers",
        "accuracy",
    )

    def __init__(
        self,
        profile_path: str | Path | None = None,
        profile_data: dict[str, Any] | None = None,
        **overrides: Any,
    ) -> None:
        resolved_profile_path = Path(profile_path).resolve() if profile_path is not None else (PROFILES_DIR / self.PROFILE_FILENAME).resolve()
        object.__setattr__(self, "profile_path", resolved_profile_path)
        object.__setattr__(self, "_profile", {})

        if profile_data is not None:
            raw_profile = deepcopy(profile_data)
            needs_persist = False
        else:
            raw_profile, needs_persist = self._load_or_create_profile()

        normalized_profile = self._normalize_profile(raw_profile)
        if overrides:
            normalized_profile.update(overrides)

        object.__setattr__(self, "_profile", normalized_profile)
        if needs_persist:
            self.save_profile()

    @classmethod
    def _default_profile(cls) -> dict[str, Any]:
        profile = load_default_profile()
        profile.setdefault("attempts", 0)
        profile.setdefault("correct_answers", 0)
        profile.setdefault("accuracy", 0.0)
        return profile

    def _load_or_create_profile(self) -> tuple[dict[str, Any], bool]:
        if self.profile_path.exists():
            return load_json_file(self.profile_path), False

        default_profile = self._default_profile()
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_profile(default_profile)
        return default_profile, True

    @classmethod
    def _normalize_profile(cls, profile: dict[str, Any]) -> dict[str, Any]:
        legacy_profile = deepcopy(profile)
        if "stars" in legacy_profile and "total_stars" not in legacy_profile:
            legacy_profile["total_stars"] = legacy_profile.pop("stars")
        if "letters_mastered" in legacy_profile and "mastered_letters" not in legacy_profile:
            legacy_profile["mastered_letters"] = legacy_profile.pop("letters_mastered")
        if "accuracy" not in legacy_profile:
            legacy_profile["accuracy"] = 0.0

        defaults = cls._default_profile()
        normalized: dict[str, Any] = {}
        for field_name in cls._PROFILE_FIELDS:
            value = legacy_profile.get(field_name, defaults.get(field_name))
            normalized[field_name] = deepcopy(value)
        return normalized

    def _write_profile(self, profile: dict[str, Any]) -> None:
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        with self.profile_path.open("w", encoding="utf-8") as handle:
            json.dump(profile, handle, indent=2, ensure_ascii=False)

    def get_profile(self) -> dict[str, Any]:
        return deepcopy(self._profile)

    def save_profile(self) -> None:
        self._write_profile(self._profile)

    def reset_profile(self) -> dict[str, Any]:
        self._profile = self._normalize_profile(self._default_profile())
        self.save_profile()
        return self.get_profile()

    def add_stars(self, amount: int) -> int:
        self.total_stars = max(0, self.total_stars + max(0, amount))
        self.save_profile()
        return self.total_stars

    def update_accuracy(self) -> float:
        attempts = int(self.attempts)
        correct_answers = int(self.correct_answers)
        accuracy = 0.0 if attempts <= 0 else round((max(0, correct_answers) / attempts) * 100, 2)
        self.accuracy = accuracy
        self.save_profile()
        return accuracy

    def update_correct_streak(self) -> int:
        self.correct_streak = self.correct_streak + 1
        self.wrong_streak = 0
        self.save_profile()
        return self.correct_streak

    def update_wrong_streak(self) -> int:
        self.wrong_streak = self.wrong_streak + 1
        self.correct_streak = 0
        self.save_profile()
        return self.wrong_streak

    def record_weak_letter(self, letter: str) -> int:
        key = letter.strip().upper()
        if key:
            self.weak_letters[key] = int(self.weak_letters.get(key, 0)) + 1
            self.save_profile()
        return int(self.weak_letters.get(key, 0))

    def record_weak_word(self, word: str) -> int:
        key = word.strip().lower()
        if key:
            self.weak_words[key] = int(self.weak_words.get(key, 0)) + 1
            self.save_profile()
        return int(self.weak_words.get(key, 0))

    def record_sentence_error(self, error_type: str) -> int:
        key = error_type.strip().lower()
        if key:
            self.sentence_errors[key] = int(self.sentence_errors.get(key, 0)) + 1
            self.save_profile()
        return int(self.sentence_errors.get(key, 0))

    def record_hint_usage(self, level: int | str) -> int:
        if isinstance(level, str) and level.startswith("level_"):
            key = level
        else:
            key = f"level_{int(level)}"
        self.hint_usage[key] = int(self.hint_usage.get(key, 0)) + 1
        self.save_profile()
        return int(self.hint_usage[key])

    def mark_letter_mastered(self, letter: str) -> list[str]:
        key = letter.strip().upper()
        if key and key not in self.mastered_letters:
            self.mastered_letters.append(key)
            self.save_profile()
        return list(self.mastered_letters)

    def mark_word_mastered(self, word: str) -> list[str]:
        key = word.strip().lower()
        if key and key not in self.mastered_words:
            self.mastered_words.append(key)
            self.save_profile()
        return list(self.mastered_words)

    def add_badge(self, badge_name: str) -> list[str]:
        key = badge_name.strip()
        if key and key not in self.badges:
            self.badges.append(key)
            self.save_profile()
        return list(self.badges)

    def __getattr__(self, name: str) -> Any:
        if name == "stars":
            return self.total_stars
        if name == "letters_mastered":
            return self.mastered_letters
        if name in self._profile:
            return self._profile[name]
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"profile_path", "_profile"}:
            object.__setattr__(self, name, value)
            return
        if name == "stars":
            self._profile["total_stars"] = int(value)
            return
        if name == "letters_mastered":
            self._profile["mastered_letters"] = list(value)
            return
        if name in self._PROFILE_FIELDS:
            self._profile[name] = value
            return
        object.__setattr__(self, name, value)

    @property
    def profile(self) -> dict[str, Any]:
        return self._profile
