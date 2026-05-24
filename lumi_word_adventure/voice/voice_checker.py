"""Answer matching helpers for spoken and typed responses."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Optional

try:
    from rapidfuzz import fuzz  # type: ignore

    _HAS_RAPIDFUZZ = True
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    _HAS_RAPIDFUZZ = False


_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def normalize_answer(text: str) -> str:
    lowered = text.strip().lower()
    cleaned = _NORMALIZE_RE.sub(" ", lowered)
    return " ".join(cleaned.split())


def _similarity(expected: str, actual: str) -> float:
    normalized_expected = normalize_answer(expected)
    normalized_actual = normalize_answer(actual)
    if not normalized_expected and not normalized_actual:
        return 100.0
    if _HAS_RAPIDFUZZ:
        return float(fuzz.ratio(normalized_expected, normalized_actual))
    return float(SequenceMatcher(None, normalized_expected, normalized_actual).ratio() * 100.0)


def check_spoken_answer(spoken_text: Optional[str], target_word: Optional[str]) -> str:
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
