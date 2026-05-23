"""Feedback text helpers."""
from __future__ import annotations


def build_feedback_message(is_correct: bool, skill_name: str = "skill") -> str:
    if is_correct:
        return f"Great job with {skill_name}!"
    return f"Let's try {skill_name} again."


def build_hint_message(skill_name: str) -> str:
    return f"Look carefully at {skill_name}."
