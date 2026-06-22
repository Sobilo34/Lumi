"""Vendored real-time handwriting recognition (letters + words)."""
from __future__ import annotations

from writing_recognition.matcher import letter_answer_matches, word_answer_matches
from writing_recognition.runner import recognition_available, recognition_error_message, recognize_snapshot

__all__ = [
    "letter_answer_matches",
    "recognition_available",
    "recognition_error_message",
    "recognize_snapshot",
    "word_answer_matches",
]
