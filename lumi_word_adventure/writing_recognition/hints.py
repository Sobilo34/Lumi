"""Hint helpers and shape-based disambiguation for similar letters."""

from __future__ import annotations

import os
from difflib import get_close_matches

import cv2
import numpy as np

LETTER_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CONFIDENCE_HINT_THRESHOLD = 0.55
WORD_CLOSE_DISTANCE = 2

MIRROR_PAIRS = [
    frozenset({"A", "V"}),
    frozenset({"W", "M"}),
    frozenset({"U", "N"}),
    frozenset({"P", "D"}),
    frozenset({"B", "D"}),
    frozenset({"C", "G"}),
]

CONFUSABLE_LETTERS = {
    "A": ["V", "H", "R"],
    "B": ["D", "P", "R"],
    "C": ["G", "O", "E"],
    "D": ["O", "P", "B"],
    "E": ["F", "L", "C"],
    "F": ["E", "P", "T"],
    "G": ["C", "Q", "S"],
    "H": ["A", "N", "M"],
    "I": ["J", "L", "T"],
    "J": ["I", "G", "Y"],
    "K": ["R", "X", "H"],
    "L": ["I", "T", "F"],
    "M": ["W", "N", "H"],
    "N": ["M", "H", "U"],
    "O": ["Q", "D", "C"],
    "P": ["R", "B", "D"],
    "Q": ["O", "G", "D"],
    "R": ["P", "B", "K"],
    "S": ["G", "Z", "C"],
    "T": ["I", "L", "F"],
    "U": ["V", "Y", "N"],
    "V": ["A", "U", "Y"],
    "W": ["M", "V", "U"],
    "X": ["K", "Y", "Z"],
    "Y": ["V", "U", "J"],
    "Z": ["S", "X", "Y"],
}

_DICTIONARY: set[str] | None = None


def _dictionary_path() -> str:
    return os.path.join(os.path.dirname(__file__), "data", "english_words.txt")


def load_dictionary() -> set[str]:
    global _DICTIONARY
    if _DICTIONARY is not None:
        return _DICTIONARY

    words: set[str] = set()
    path = _dictionary_path()
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                word = line.strip().lower()
                if word.isalpha():
                    words.add(word)

    if not words:
        words = {
            "hello",
            "world",
            "python",
            "letter",
            "word",
            "write",
            "read",
            "learn",
            "train",
            "model",
            "draw",
            "hint",
            "close",
            "answer",
            "english",
            "alphabet",
            "cat",
            "dog",
            "sun",
            "ball",
        }

    _DICTIONARY = words
    return words


def index_to_letter(index: int) -> str:
    return LETTER_LABELS[index]


def _binary_roi(roi: np.ndarray) -> np.ndarray:
    if roi.ndim == 3:
        roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY)
    return binary


def _ink_density(region: np.ndarray) -> float:
    if region.size == 0:
        return 0.0
    return float(np.mean(region > 127))


def has_crossbar(roi: np.ndarray) -> bool:
    binary = _binary_roi(roi)
    height, width = binary.shape
    row_start = int(height * 0.35)
    row_end = int(height * 0.58)
    col_start = int(width * 0.2)
    col_end = int(width * 0.8)
    band = binary[row_start:row_end, col_start:col_end]
    return _ink_density(band) > 0.07


def has_top_center_dip(roi: np.ndarray) -> bool:
    binary = _binary_roi(roi)
    height, width = binary.shape
    top_rows = []
    for col in range(width):
        column = binary[:, col]
        ink = np.where(column > 127)[0]
        top_rows.append(int(ink[0]) if len(ink) else height)

    left = top_rows[int(width * 0.2)]
    center = top_rows[int(width * 0.5)]
    right = top_rows[int(width * 0.8)]
    return center > (left + right) / 2 + height * 0.06


def has_bottom_center_peak(roi: np.ndarray) -> bool:
    binary = _binary_roi(roi)
    height, width = binary.shape
    bottom_rows = []
    for col in range(width):
        column = binary[:, col]
        ink = np.where(column > 127)[0]
        bottom_rows.append(int(ink[-1]) if len(ink) else 0)

    left = bottom_rows[int(width * 0.2)]
    center = bottom_rows[int(width * 0.5)]
    right = bottom_rows[int(width * 0.8)]
    return center > (left + right) / 2 + height * 0.06


def is_mirror_pair(a: str, b: str) -> bool:
    pair = frozenset({a, b})
    return pair in MIRROR_PAIRS


def disambiguate_letter(
    roi: np.ndarray,
    letter: str,
    confidence: float,
    top_predictions: list[tuple[str, float]],
) -> tuple[str, float, list[tuple[str, float]], str | None]:
    if not top_predictions:
        return letter, confidence, top_predictions, None

    alternatives = {alt for alt, _ in top_predictions[1:4]}
    note = None
    corrected = letter

    if letter == "V" and ("A" in alternatives or has_crossbar(roi)):
        if has_crossbar(roi):
            corrected = "A"
            note = "Crossbar detected: A instead of V"
    elif letter == "A" and "V" in alternatives and not has_crossbar(roi):
        corrected = "V"
        note = "No crossbar detected: V instead of A"

    if letter == "M" and ("W" in alternatives or has_bottom_center_peak(roi)):
        if has_bottom_center_peak(roi) and not has_top_center_dip(roi):
            corrected = "W"
            note = "Bottom peak detected: W instead of M"
    elif letter == "W" and "M" in alternatives and not has_bottom_center_peak(roi):
        if has_top_center_dip(roi):
            corrected = "M"
            note = "Top dip detected: M instead of W"

    if corrected != letter:
        updated = list(top_predictions)
        for index, (label, score) in enumerate(updated):
            if label == corrected:
                updated[index] = (label, max(score, confidence))
                break
        else:
            updated.insert(0, (corrected, confidence + 0.05))
        updated.sort(key=lambda item: item[1], reverse=True)
        return corrected, updated[0][1], updated, note

    if is_mirror_pair(letter, next(iter(alternatives), "")):
        if confidence < 0.72:
            note = f"{letter} can look like its mirror pair. Draw carefully."

    return letter, confidence, top_predictions, note


def _confusable_hint(letter: str, alternatives: list[str]) -> str | None:
    similar = CONFUSABLE_LETTERS.get(letter, [])
    close = [alt for alt in alternatives if alt in similar]
    if close:
        mirror = [alt for alt in close if is_mirror_pair(letter, alt)]
        if mirror:
            return f"{letter} is often confused with mirror letters: {', '.join(mirror)}"
        return f"{letter} is often confused with {', '.join(close)}"
    return None


def letter_hints(
    top_predictions: list[tuple[str, float]], shape_note: str | None = None
) -> str | None:
    if not top_predictions:
        return None

    best_letter, best_confidence = top_predictions[0]
    alternatives = [letter for letter, _ in top_predictions[1:4]]
    confusable = _confusable_hint(best_letter, alternatives)

    if shape_note:
        return shape_note

    if best_confidence >= CONFIDENCE_HINT_THRESHOLD:
        if alternatives and top_predictions[1][1] >= best_confidence - 0.15:
            alt_text = ", ".join(alternatives)
            if confusable:
                return f"Close call: also looks like {alt_text}. {confusable}."
            return f"Close call: also looks like {alt_text}"
        if confusable and best_confidence < 0.75:
            return confusable
        return None

    alt_text = ", ".join(letter for letter, _ in top_predictions[:3])
    if confusable:
        return f"Low confidence. Did you mean {alt_text}? {confusable}."
    return f"Low confidence. Did you mean: {alt_text}?"


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        return levenshtein(b, a)
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (char_a != char_b)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def word_hints(word: str) -> str | None:
    cleaned = word.lower().strip()
    if not cleaned or not cleaned.isalpha():
        return "Use only English letters for words."

    dictionary = load_dictionary()
    if cleaned in dictionary:
        return None

    candidates = [
        candidate
        for candidate in dictionary
        if abs(len(candidate) - len(cleaned)) <= WORD_CLOSE_DISTANCE
        and candidate[0] == cleaned[0]
    ]
    close = get_close_matches(cleaned, candidates, n=5, cutoff=0.72)
    if close:
        return f"Not in dictionary. Did you mean: {', '.join(close)}?"

    scored: list[tuple[int, str]] = []
    for candidate in candidates:
        distance = levenshtein(cleaned, candidate)
        if distance <= WORD_CLOSE_DISTANCE:
            scored.append((distance, candidate))

    scored.sort(key=lambda item: (item[0], len(item[1])))
    if scored:
        suggestions = [candidate for _, candidate in scored[:5]]
        return f"Close match: {', '.join(suggestions)}"

    return "Word not recognized. Try clearer spacing between letters."


def close_word_matches(target: str, recognized: str) -> bool:
    """True when recognized text is a fuzzy match for the writing target word."""
    cleaned_target = str(target or "").lower().strip()
    cleaned = str(recognized or "").lower().strip()
    if not cleaned_target or not cleaned:
        return False
    if cleaned == cleaned_target:
        return True
    if levenshtein(cleaned, cleaned_target) <= WORD_CLOSE_DISTANCE:
        return True
    candidates = [
        candidate
        for candidate in load_dictionary()
        if abs(len(candidate) - len(cleaned)) <= WORD_CLOSE_DISTANCE
        and candidate[0] == cleaned[0]
    ]
    close = get_close_matches(cleaned, candidates, n=5, cutoff=0.72)
    return cleaned_target in close
