"""Teacher and parent report helpers."""
from __future__ import annotations

from pathlib import Path
import json


def generate_report(profile: dict, output_path: str | Path | None = None) -> dict:
    report = {
        "child_name": profile.get("child_name", "Player 1"),
        "stars": profile.get("stars", 0),
        "difficulty": profile.get("difficulty", 1),
        "attempts": profile.get("attempts", 0),
        "correct_answers": profile.get("correct_answers", 0),
    }
    if output_path is not None:
        with Path(output_path).open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
    return report
