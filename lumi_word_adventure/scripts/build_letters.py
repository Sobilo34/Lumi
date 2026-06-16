"""Build data/letters.json with A–Z kindergarten letter entries."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXAMPLE_WORDS = {
    "A": "apple", "B": "ball", "C": "cat", "D": "dog", "E": "egg", "F": "fish",
    "G": "goat", "H": "hat", "I": "ink", "J": "jam", "K": "kite", "L": "lion",
    "M": "moon", "N": "nest", "O": "owl", "P": "pig", "Q": "queen", "R": "rain",
    "S": "sun", "T": "top", "U": "up", "V": "van", "W": "web", "X": "box",
    "Y": "yarn", "Z": "zoo",
}

CONFUSABLE = {
    "A": ["E", "O"], "B": ["D", "P"], "C": ["G", "O"], "D": ["B", "P"],
    "E": ["A", "F"], "F": ["E", "T"], "G": ["C", "Q"], "H": ["N", "M"],
    "I": ["L", "J"], "J": ["I", "G"], "K": ["X", "H"], "L": ["I", "T"],
    "M": ["N", "W"], "N": ["M", "H"], "O": ["A", "Q"], "P": ["B", "R"],
    "Q": ["O", "G"], "R": ["P", "N"], "S": ["Z", "C"], "T": ["F", "L"],
    "U": ["V", "W"], "V": ["U", "Y"], "W": ["M", "V"], "X": ["K", "Y"],
    "Y": ["V", "X"], "Z": ["S", "N"],
}


def build_letters() -> list[dict]:
    letters = []
    for index, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        letters.append({
            "id": f"letter_{letter}",
            "letter": letter,
            "alphabet_index": index,
            "sound": f"/{letter.lower()}/",
            "example_word": EXAMPLE_WORDS[letter],
            "difficulty": 1 + (index // 9),
            "confusable_with": CONFUSABLE.get(letter, []),
            "prompt": f"Find the letter {letter}",
        })
    return letters


if __name__ == "__main__":
    path = ROOT / "data" / "letters.json"
    path.write_text(json.dumps(build_letters(), indent=2), encoding="utf-8")
    print(f"Wrote {len(build_letters())} letters to {path}")
