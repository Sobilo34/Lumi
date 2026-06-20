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
_LETTER_PREFIX_RE = re.compile(r"^(?:the\s+)?letter\s+")

LETTER_PHONETIC_ALIASES: dict[str, tuple[str, ...]] = {
    "a": ("a", "ay", "eh", "aye"),
    "b": ("b", "bee", "be"),
    "c": ("c", "see", "cee", "sea"),
    "d": ("d", "dee"),
    "e": ("e", "ee", "eh"),
    "f": ("f", "ef", "eff"),
    "g": ("g", "gee", "jee"),
    "h": ("h", "aitch", "haitch", "ache"),
    "i": ("i", "eye", "aye"),
    "j": ("j", "jay"),
    "k": ("k", "kay"),
    "l": ("l", "el", "ell"),
    "m": ("m", "em"),
    "n": ("n", "en"),
    "o": ("o", "oh", "owe"),
    "p": ("p", "pee"),
    "q": ("q", "cue", "queue"),
    "r": ("r", "ar", "are"),
    "s": ("s", "ess", "es"),
    "t": ("t", "tee"),
    "u": ("u", "you", "yew"),
    "v": ("v", "vee"),
    "w": ("w", "double u", "doubleyou", "dubya"),
    "x": ("x", "ex"),
    "y": ("y", "why", "wye"),
    "z": ("z", "zee", "zed"),
}


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


def _is_single_letter_target(target: str) -> bool:
    cleaned = str(target or "").strip()
    return len(cleaned) == 1 and cleaned.isalpha()


def guess_spoken_letter(spoken_text: Optional[str]) -> str:
    """Best-effort letter extraction from spoken text (e.g. 'gee' -> 'g')."""
    normalized = normalize_answer(spoken_text or "")
    if not normalized:
        return ""

    normalized = _LETTER_PREFIX_RE.sub("", normalized).strip()
    if not normalized:
        return ""

    tokens = normalized.split()
    for token in reversed(tokens):
        if len(token) == 1 and token.isalpha():
            return token
        for letter, aliases in LETTER_PHONETIC_ALIASES.items():
            if token in aliases:
                return letter

    if len(tokens) == 1:
        token = tokens[0]
        if len(token) == 1 and token.isalpha():
            return token
        for letter, aliases in LETTER_PHONETIC_ALIASES.items():
            if token in aliases:
                return letter

    for letter, aliases in LETTER_PHONETIC_ALIASES.items():
        if normalized in aliases:
            return letter

    if len(tokens) >= 2 and tokens[0] in {"its", "it", "is", "that's", "thats", "the", "a", "an"}:
        tail = tokens[-1]
        if len(tail) == 1 and tail.isalpha():
            return tail
        for letter, aliases in LETTER_PHONETIC_ALIASES.items():
            if tail in aliases:
                return letter

    return ""


def _check_spoken_letter(spoken_text: Optional[str], target_letter: str) -> str:
    target = str(target_letter or "").strip().lower()
    if not target:
        return "incorrect"

    spoken_letter = guess_spoken_letter(spoken_text)
    if spoken_letter and spoken_letter == target:
        return "correct"

    if spoken_letter:
        score = _similarity(target, spoken_letter)
        if score >= 80.0:
            return "correct"
        if score >= 60.0:
            return "close"

    normalized = normalize_answer(spoken_text or "")
    normalized = _LETTER_PREFIX_RE.sub("", normalized).strip()
    if len(normalized) == 1 and normalized.isalpha():
        if normalized == target:
            return "correct"
        score = _similarity(target, normalized)
        if score >= 60.0:
            return "close"

    return "incorrect"


def check_spoken_answer(spoken_text: Optional[str], target_word: Optional[str]) -> str:
    target = str(target_word or "").strip()
    if _is_single_letter_target(target):
        return _check_spoken_letter(spoken_text, target)

    score = _similarity(spoken_text or "", target)
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
