"""Offline, adaptive hint engine for every Lumi challenge.

This is an "AI-powered" hint system in the sense that it reasons about the
child's context — the exact target, the mistake they just made, how many hints
they've already needed this round, and their longer-term weak skills — and then
composes a short, warm, age-appropriate cue (for 2-4 year olds).

It is fully offline and deterministic (no network / LLM dependency) so it always
works in a classroom or on a tablet with no connectivity. It draws on real
phonics, letter-shape mnemonics, and mouth-shape cues for speaking practice.

Covered challenges:
- Letter Island tap (A-Z)
- Word Garden tap (every word)
- Letter speaking
- Word speaking

Each hint escalates across `level` (1 -> gentle nudge, 2 -> concrete strategy,
3+ -> near-direct help) and grows more supportive when the child has a repeated
weakness on the target.
"""
from __future__ import annotations

from typing import Any

from data_loader import load_letters, load_vocabulary

# How each letter "sounds" when said aloud to a toddler (kid-friendly, not IPA).
LETTER_SOUND: dict[str, str] = {
    "A": "ah", "B": "buh", "C": "kuh", "D": "duh", "E": "eh", "F": "fff",
    "G": "guh", "H": "huh", "I": "ih", "J": "juh", "K": "kuh", "L": "lll",
    "M": "mmm", "N": "nnn", "O": "oh", "P": "puh", "Q": "kwuh", "R": "rrr",
    "S": "sss", "T": "tuh", "U": "uh", "V": "vvv", "W": "wuh", "X": "kss",
    "Y": "yuh", "Z": "zzz",
}

# A picture of each letter's shape a young child can hunt for.
LETTER_SHAPE: dict[str, str] = {
    "A": "a pointy roof with a belt", "B": "a tall line with two round bellies",
    "C": "an open curve like a cup", "D": "a straight back with one big belly",
    "E": "a line with three little arms", "F": "a flag with two arms",
    "G": "a curve with a little shelf", "H": "two posts and a bridge",
    "I": "one straight little stick", "J": "a hook that swings down",
    "K": "a line with two kicking legs", "L": "a tall line with a foot",
    "M": "two mountains in a row", "N": "a line with a slide",
    "O": "a round full circle", "P": "a line with one round head",
    "Q": "a circle with a little tail", "R": "a head and one kicking leg",
    "S": "a wiggly snake", "T": "a tall line wearing a hat",
    "U": "a smiling cup", "V": "a deep pointy valley",
    "W": "two valleys side by side", "X": "two sticks crossing",
    "Y": "a cup on a stick", "Z": "a zig-zag with two lines",
}

# Where to put lips/tongue to make the sound (for speaking practice).
LETTER_MOUTH: dict[str, str] = {
    "A": "open your mouth wide and say ah", "B": "press your lips, then pop: buh",
    "C": "open your throat: kuh", "D": "tap your tongue up top: duh",
    "E": "smile a little and say eh", "F": "bite your lip softly: fff",
    "G": "make it in your throat: guh", "H": "breathe out warm air: huh",
    "I": "smile small and say ih", "J": "buzz your lips: juh",
    "K": "click at the back: kuh", "L": "lift your tongue: lll",
    "M": "close your lips and hum: mmm", "N": "tongue up and hum: nnn",
    "O": "make a round mouth: oh", "P": "puff your lips: puh",
    "Q": "round your lips: kwuh", "R": "growl gently: rrr",
    "S": "smile and hiss like a snake: sss", "T": "tap your tongue: tuh",
    "U": "open soft and say uh", "V": "bite your lip and buzz: vvv",
    "W": "blow a kiss: wuh", "X": "say kss like a sneeze",
    "Y": "say yuh like yes", "Z": "buzz like a bee: zzz",
}

_VOWELS = set("AEIOU")


def _profile_weak_count(profile: Any, kind: str, key: str) -> int:
    """Return how many times `key` is logged as a weak letter/word."""
    if profile is None or not key:
        return 0
    field = "weak_letters" if kind == "letter" else "weak_words"
    data: Any = None
    if hasattr(profile, field):
        data = getattr(profile, field)
    elif isinstance(profile, dict):
        data = profile.get(field)
    if not isinstance(data, dict):
        return 0
    lookup = key.upper() if kind == "letter" else key.lower()
    for raw_key, count in data.items():
        candidate = str(raw_key).upper() if kind == "letter" else str(raw_key).lower()
        if candidate == lookup:
            try:
                return int(count)
            except (TypeError, ValueError):
                return 0
    return 0


def _coerce_level(level: Any) -> int:
    text = str(level).strip().lower()
    for token in ("level_", "level"):
        if text.startswith(token):
            text = text[len(token):]
    try:
        value = int(float(text))
    except (TypeError, ValueError):
        value = 1
    return max(1, value)


class HintEngine:
    """Composes adaptive hints from curriculum data + the child's context."""

    def __init__(
        self,
        letters: list[dict[str, Any]] | None = None,
        vocabulary: list[dict[str, Any]] | None = None,
    ) -> None:
        self._letters_raw = letters
        self._vocab_raw = vocabulary
        self._letter_index: dict[str, dict[str, Any]] | None = None
        self._word_index: dict[str, dict[str, Any]] | None = None

    # ---- lazy data ---------------------------------------------------------
    def _letters(self) -> dict[str, dict[str, Any]]:
        if self._letter_index is None:
            raw = self._letters_raw
            if raw is None:
                try:
                    raw = load_letters()
                except Exception:
                    raw = []
            index: dict[str, dict[str, Any]] = {}
            for entry in raw or []:
                letter = str(entry.get("letter", "")).upper()
                if letter:
                    index[letter] = entry
            self._letter_index = index
        return self._letter_index

    def _words(self) -> dict[str, dict[str, Any]]:
        if self._word_index is None:
            raw = self._vocab_raw
            if raw is None:
                try:
                    raw = load_vocabulary()
                except Exception:
                    raw = []
            index: dict[str, dict[str, Any]] = {}
            for entry in raw or []:
                word = str(entry.get("word", "")).lower()
                if word:
                    index[word] = entry
            self._word_index = index
        return self._word_index

    # ---- small helpers -----------------------------------------------------
    def _example_word(self, letter: str) -> str:
        entry = self._letters().get(letter.upper())
        if entry:
            example = str(entry.get("example_word", "")).strip()
            if example:
                return example
        defaults = {"A": "apple", "B": "ball", "C": "cat"}
        return defaults.get(letter.upper(), "")

    def _spell_out(self, word: str) -> str:
        letters = [c.upper() for c in word if c.isalpha()]
        return " ".join(letters)

    def _effective_level(self, level: Any, weak_count: int) -> int:
        base = _coerce_level(level)
        if weak_count >= 2:
            base += 1
        return base

    # ---- letter tap --------------------------------------------------------
    def letter_hint(
        self,
        target: str,
        *,
        level: Any = 1,
        mistake_type: str = "",
        selected: str = "",
        profile: Any = None,
    ) -> str:
        target_letter = str(target or "").strip().upper()
        if not target_letter:
            return "Let's look together. You can do it!"
        selected_letter = str(selected or "").strip().upper()
        mistake = str(mistake_type or "").strip().lower()
        weak = _profile_weak_count(profile, "letter", target_letter)
        lvl = self._effective_level(level, weak)

        sound = LETTER_SOUND.get(target_letter, "")
        example = self._example_word(target_letter)
        shape = LETTER_SHAPE.get(target_letter, "")

        # Mistake-aware contrast first — most useful right after a wrong tap.
        if mistake == "bd_confusion":
            return f"B has a belly. D has a drum. Touch {target_letter}."
        if selected_letter and selected_letter != target_letter:
            sel_shape = LETTER_SHAPE.get(selected_letter, "")
            if sel_shape and shape:
                return (
                    f"That one is {selected_letter} — {sel_shape}. "
                    f"{target_letter} is {shape}. Touch {target_letter}."
                )

        if lvl <= 1:
            if sound and example:
                return f"Listen: {sound}... {target_letter} is for {example}. Find {target_letter}."
            return f"Find the letter {target_letter}."
        if lvl == 2:
            if shape:
                return f"{target_letter} looks like {shape}. Find {target_letter}."
            return f"The letter {target_letter} has its own special shape."
        # level 3+
        if example:
            return f"You're so close! {target_letter} like {example}. Touch {target_letter} now."
        return f"You're so close! Touch {target_letter} now."

    # ---- word tap ----------------------------------------------------------
    def word_hint(
        self,
        target: str,
        *,
        level: Any = 1,
        mistake_type: str = "",
        selected: str = "",
        profile: Any = None,
    ) -> str:
        target_word = str(target or "").strip().lower()
        if not target_word:
            return "Touch the picture."
        return f"Touch the {target_word.capitalize()}."

    # ---- letter speaking ---------------------------------------------------
    def letter_speaking_hint(
        self,
        target: str,
        *,
        level: Any = 1,
        heard: str = "",
        profile: Any = None,
    ) -> str:
        target_letter = str(target or "").strip().upper()
        if not target_letter:
            return "Take a breath and try again."
        weak = _profile_weak_count(profile, "letter", target_letter)
        lvl = self._effective_level(level, weak)

        sound = LETTER_SOUND.get(target_letter, "")
        mouth = LETTER_MOUTH.get(target_letter, "")
        example = self._example_word(target_letter)
        heard_text = str(heard or "").strip()

        if heard_text and heard_text.lower() != target_letter.lower():
            base = f"So close! I heard {heard_text}. "
        else:
            base = ""

        if lvl <= 1:
            if sound:
                return f"{base}Say the sound slowly: {sound}... that is {target_letter}."
            return f"{base}Say the letter {target_letter}."
        if lvl == 2:
            if mouth:
                return f"{base}{mouth.capitalize()}. That is {target_letter}."
            if example:
                return f"{base}{target_letter} is for {example}. Say {target_letter}."
            return f"{base}Say {target_letter} a little slower."
        return f"{base}Great trying! Say {target_letter} one more time with me."

    # ---- word speaking -----------------------------------------------------
    def word_speaking_hint(
        self,
        target: str,
        *,
        level: Any = 1,
        heard: str = "",
        profile: Any = None,
    ) -> str:
        target_word = str(target or "").strip().lower()
        if not target_word:
            return "Take a breath and try again."
        weak = _profile_weak_count(profile, "word", target_word)
        lvl = self._effective_level(level, weak)

        spelled = self._spell_out(target_word)
        first = target_word[0].upper()
        mouth = LETTER_MOUTH.get(first, "")
        heard_text = str(heard or "").strip()

        if heard_text and heard_text.lower() != target_word.lower():
            base = f"So close! I heard {heard_text}. "
        else:
            base = ""

        if lvl <= 1:
            if spelled:
                return f"{base}Say it slowly with me: {spelled}... {target_word}."
            return f"{base}Say {target_word} with me."
        if lvl == 2:
            if mouth:
                return f"{base}Start with {first}: {mouth}. Then say {target_word}."
            return f"{base}Say {target_word} a little slower."
        return f"{base}You're doing great! Take a breath and say {target_word}."


_engine_singleton: HintEngine | None = None


def get_hint_engine() -> HintEngine:
    global _engine_singleton
    if _engine_singleton is None:
        _engine_singleton = HintEngine()
    return _engine_singleton
