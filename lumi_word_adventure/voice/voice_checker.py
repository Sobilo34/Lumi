"""Answer matching helpers for spoken and typed responses."""
from __future__ import annotations

from difflib import SequenceMatcher

try:
    from rapidfuzz.fuzz import ratio as fuzz_ratio
except Exception:  # pragma: no cover - dependency may be absent in headless checks
    fuzz_ratio = None


def normalize_answer(text: str) -> str:
    return " ".join(text.strip().lower().split())


def check_answer(expected: str, actual: str, threshold: int = 85) -> bool:
    normalized_expected = normalize_answer(expected)
    normalized_actual = normalize_answer(actual)
    if not normalized_expected or not normalized_actual:
        return False
    if normalized_expected == normalized_actual:
        return True
    if fuzz_ratio is not None:
        return fuzz_ratio(normalized_expected, normalized_actual) >= threshold
    return SequenceMatcher(None, normalized_expected, normalized_actual).ratio() * 100 >= threshold
