"""Local learner profile model."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json

from config import DEFAULT_DIFFICULTY


@dataclass
class LearnerModel:
    child_name: str = "Player 1"
    stars: int = 0
    difficulty: int = DEFAULT_DIFFICULTY
    correct_streak: int = 0
    wrong_streak: int = 0
    letters_mastered: list[str] = field(default_factory=list)
    weak_letters: dict[str, int] = field(default_factory=dict)
    weak_words: dict[str, int] = field(default_factory=dict)
    sentence_errors: dict[str, int] = field(default_factory=dict)
    hint_usage: dict[str, int] = field(
        default_factory=lambda: {"level_1": 0, "level_2": 0, "level_3": 0}
    )
    attempts: int = 0
    correct_answers: int = 0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearnerModel":
        return cls(**payload)

    @classmethod
    def load(cls, path: str | Path) -> "LearnerModel":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)
