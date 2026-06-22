"""Answer matching for Writing Castle handwriting rounds."""
from __future__ import annotations

from writing_recognition.hints import close_word_matches


def letter_answer_matches(target: str, recognized: str) -> bool:
    expected = str(target or "").strip().upper()
    actual = str(recognized or "").strip().upper()
    if not expected or not actual:
        return False
    return actual == expected or actual[0] == expected


def word_answer_matches(target: str, recognized: str) -> bool:
    return close_word_matches(str(target or ""), str(recognized or ""))
