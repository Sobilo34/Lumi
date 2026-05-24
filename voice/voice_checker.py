"""Spoken answer checker using RapidFuzz (with difflib fallback).

Functions:
- check_spoken_answer(spoken_text, target_word) -> "correct"|"close"|"incorrect"
- normalize_answer(text) -> normalized text
- check_answer(expected, actual, threshold=85) -> bool

Thresholds: >=80 -> correct, >=60 -> close, else incorrect.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher
from typing import Optional

try:
    from rapidfuzz import fuzz  # type: ignore
    _HAS_RAPIDFUZZ = True
except Exception:
    _HAS_RAPIDFUZZ = False
    from difflib import SequenceMatcher  # type: ignore


_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def _normalize(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = _NORMALIZE_RE.sub(" ", s)
    s = " ".join(s.split())
    return s


def normalize_answer(text: str) -> str:
    return _normalize(text)


def _similarity(a: str, b: str) -> float:
    a_n = _normalize(a)
    b_n = _normalize(b)
    if not a_n and not b_n:
        return 100.0
    if _HAS_RAPIDFUZZ:
        try:
            return float(fuzz.ratio(a_n, b_n))
        except Exception:
            pass
    # fallback to difflib ratio scaled to 0-100
    return float(SequenceMatcher(None, a_n, b_n).ratio() * 100.0)


def check_spoken_answer(spoken_text: Optional[str], target_word: Optional[str]) -> str:
    """Return 'correct', 'close', or 'incorrect' based on similarity.

    Uses RapidFuzz when available; otherwise a difflib fallback is used.
    """
    score = _similarity(spoken_text or "", target_word or "")
    if score >= 80.0:
        return "correct"
    if score >= 60.0:
        return "close"
    return "incorrect"


def check_answer(expected: str, actual: str, threshold: int = 85) -> bool:
    """Backward-compatible boolean checker used by older tests/callers."""
    if not expected or not actual:
        return False
    return _similarity(expected, actual) >= float(threshold)
