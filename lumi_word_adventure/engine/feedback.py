"""Child-friendly feedback helpers."""
from __future__ import annotations

from typing import Any

from config import LETTER_VOICE_PROMPT


_VISUAL_CONFUSION_HINTS: dict[tuple[str, str], str] = {
    ("B", "D"): "B has a belly. D has a drum.",
    ("D", "B"): "D has a drum. B has a belly.",
    ("B", "P"): "B has two bumps on one side. P has one long line.",
    ("B", "R"): "B has a belly bump. R has a little leg.",
    ("M", "W"): "M says mmm. W looks like two hills.",
    ("W", "M"): "W has two pointy tops. M has two soft bumps.",
    ("M", "N"): "M has two bumps. N has one slant.",
    ("N", "M"): "N has one slant. M has two bumps.",
    ("C", "G"): "C is open like a cup. G has a little tail.",
    ("G", "C"): "G has a tail inside. C is open like a cup.",
    ("C", "O"): "C is open on the side. O is a full circle.",
    ("O", "C"): "O is round all the way. C has an open side.",
    ("E", "F"): "E has three lines. F has two lines.",
    ("F", "E"): "F has two lines. E has three lines.",
    ("I", "L"): "I is a straight stick. L has a foot.",
    ("L", "I"): "L has a foot at the bottom. I is straight.",
    ("I", "T"): "I is one straight line. T has a top bar.",
    ("T", "I"): "T has a top bar. I is one straight line.",
    ("O", "Q"): "O is a circle. Q has a little tail.",
    ("Q", "O"): "Q has a tail. O is a circle.",
    ("O", "D"): "O is round. D has a straight back.",
    ("D", "O"): "D has a straight back. O is round.",
}


_LETTER_VOICE_CHARACTER_HINTS: dict[str, str] = {
    "A": "A has a point at the top and a line across the middle.",
    "B": "B has a belly bump on one side.",
    "C": "C is open like a cup.",
    "D": "D has a straight back like a drum.",
    "E": "E has three lines across.",
    "F": "F has two lines across.",
    "G": "G has a little tail inside.",
    "H": "H has two tall posts with a bridge.",
    "I": "I is one straight stick.",
    "J": "J has a hook at the bottom.",
    "K": "K has a slant and a leg.",
    "L": "L has a foot at the bottom.",
    "M": "M has two soft bumps.",
    "N": "N has one slant between two posts.",
    "O": "O is round like a circle.",
    "P": "P has a round head on a stick.",
    "Q": "Q is a circle with a little tail.",
    "R": "R has a round head and a leg.",
    "S": "S curves like a snake.",
    "T": "T has a top bar on a stick.",
    "U": "U is open at the top like a cup.",
    "V": "V has two slants that meet at the bottom.",
    "W": "W has two pointy hills.",
    "X": "X has two crossing lines.",
    "Y": "Y splits into two arms at the bottom.",
    "Z": "Z has a top line, a slant, and a bottom line.",
}


def _feedback_payload(feedback_type: str, message: str) -> dict[str, str]:
    return {"type": feedback_type, "message": message}


def get_feedback(
    result: Any,
    mistake_type: str | None = None,
    target: str | None = None,
    selected: str | None = None,
) -> dict[str, str]:
    feedback_key = str(result).strip().lower()

    if feedback_key in {"correct", "badge_unlock", "level_complete"} or result is True:
        if feedback_key == "badge_unlock":
            return _feedback_payload("badge_unlock", "Hooray! You unlocked a new badge!")
        if feedback_key == "level_complete":
            return _feedback_payload("level_complete", "Wonderful! You finished this world with Lumi!")
        return _feedback_payload("correct", "Great job! You helped Lumi!")

    if feedback_key in {"hint", "show_hint"}:
        return _feedback_payload("hint", "Let’s look together. You can do it!")

    if feedback_key == "close" or mistake_type in {"voice_close", "pronunciation_close"}:
        return _feedback_payload("close", "Almost! I heard something close. Try again.")

    if mistake_type == "bd_confusion":
        return _feedback_payload("incorrect", "Good try! B has a belly.")

    if mistake_type == "visual_confusion":
        if target and selected:
            pair_hint = _VISUAL_CONFUSION_HINTS.get((target.upper(), selected.upper()))
            if pair_hint:
                return _feedback_payload("incorrect", f"Good try! {pair_hint}")
            return _feedback_payload(
                "incorrect",
                f"This is {selected.upper()}. Look closely for {target.upper()}.",
            )
        if target:
            return _feedback_payload("incorrect", f"Look closely for {target.upper()}.")

    if mistake_type == "letter_confusion":
        if target and selected:
            return _feedback_payload("incorrect", f"This is {selected.upper()}. Find {target.upper()}.")
        if target:
            return _feedback_payload("incorrect", f"Find {target.upper()}.")
        return _feedback_payload("incorrect", "Good try! Let’s look again.")

    if mistake_type == "same_category_vocabulary_confusion":
        if selected:
            return _feedback_payload("incorrect", f"This is {selected}. A cat says meow. Find the cat.")
        return _feedback_payload("incorrect", "This is dog. A cat says meow. Find the cat.")

    if mistake_type == "word_confusion":
        if target and selected:
            return _feedback_payload("incorrect", f"This is {target}. A {selected} says meow.")
        if target:
            return _feedback_payload("incorrect", f"This is {target}. Let’s look again.")
        return _feedback_payload("incorrect", "Good try! Let’s look again.")

    if mistake_type == "sentence_order":
        if target:
            first_word = target.split()[0]
            return _feedback_payload("incorrect", f"Good try! Start with {first_word}.")
        return _feedback_payload("incorrect", "Good try! Start with the first word.")

    if result is False or feedback_key == "incorrect":
        return _feedback_payload("incorrect", "Good try! Let’s look again.")

    return _feedback_payload("incorrect", "Good try! Let’s look again.")


def get_letter_mistake_hint(
    mistake_type: str,
    *,
    target: str = "",
    selected: str = "",
    hint_level: int | str = 1,
) -> str:
    """Targeted, child-friendly hints after a diagnosed letter mistake."""
    mistake = mistake_type.strip().lower()
    target_letter = target.strip().upper()
    selected_letter = selected.strip().upper()
    level = str(hint_level).strip()

    if mistake == "bd_confusion":
        return "B has a belly. D has a drum."
    if mistake == "visual_confusion" and target_letter and selected_letter:
        pair_hint = _VISUAL_CONFUSION_HINTS.get((target_letter, selected_letter))
        if pair_hint:
            return pair_hint
        return f"Look closely. {target_letter} is not the same as {selected_letter}."
    if level in {"2", "level_2"} and target_letter:
        return f"The letter {target_letter} has its own special shape."
    if target_letter:
        return f"Look for the letter {target_letter}."
    return "Look for the letter again."


def get_letter_voice_character_hint(letter: str, hint_level: int = 1) -> str:
    """Shape or sound hints for spoken letter challenges without revealing the answer."""
    target_letter = letter.strip().upper()
    if not target_letter:
        return "Look at the letter shape again."

    if hint_level <= 1:
        return _LETTER_VOICE_CHARACTER_HINTS.get(
            target_letter,
            f"Look closely at the shape of {target_letter}.",
        )
    if hint_level == 2:
        return f"The letter {target_letter} has its own special sound."
    return f"Listen for the {target_letter} sound and try again."


def get_hint(
    activity_type: str,
    hint_level: int | str,
    target: str,
    *,
    mistake_type: str = "",
    selected: str = "",
) -> str:
    activity = activity_type.strip().lower()
    target_text = target.strip() if target else ""
    level = str(hint_level).strip()

    if activity == "letter":
        if mistake_type:
            return get_letter_mistake_hint(
                mistake_type,
                target=target_text,
                selected=selected,
                hint_level=level,
            )
        if level in {"1", "level_1"}:
            return f"Look for the letter {target_text}."
        if level in {"2", "level_2"}:
            return f"The letter {target_text} has a strong sound."
        return f"Try touching {target_text} one more time."

    if activity == "word":
        if level in {"1", "level_1"}:
            return f"Find the word {target_text}."
        if level in {"2", "level_2"}:
            return f"Look at the first letter in {target_text}."
        return f"You can do it. Try {target_text} again."

    if activity == "sentence":
        if level in {"1", "level_1"}:
            return f"Start with {target_text}."
        if level in {"2", "level_2"}:
            return f"Put the words in the right order for {target_text}."
        return f"Take your time with {target_text}."

    if activity == "voice":
        if level in {"1", "level_1"}:
            return "Listen carefully to the word."
        if level in {"2", "level_2"}:
            return "Try saying the word a little slower."
        return "Take your time and try again."

    return f"Try {target_text} again."


def get_lumi_speech(screen_id: str, current_task: str | None = None) -> str:
    screen = screen_id.strip().lower()
    task = current_task.strip() if current_task else ""

    if screen == "welcome":
        return "Hello! I’m Lumi. Let’s learn together!"
    if screen == "main_menu":
        return "Choose a fun world to play in."
    if screen == "how_to_play":
        return "Listen, tap, and speak. Lumi will help you!"
    if screen == "world_map":
        return "Pick a world to start your adventure."
    if screen == "letter_island_game":
        return f"Find the right letter, {task}." if task else "Find the right letter."
    if screen == "bd_practice":
        return "B has a belly. D has a drum."
    if screen == "word_garden_game":
        return f"Touch the word you hear, {task}." if task else "Touch the word you hear."
    if screen == "writing_castle_game":
        return f"Write on the board, {task}." if task else "Write on the board."
    if screen == "word_correct_feedback":
        return f"Wonderful! {task.capitalize()}." if task else "Wonderful!"
    if screen == "sentence_castle_game":
        return f"Put the sentence together, {task}." if task else "Put the sentence together."
    if screen == "voice_challenge":
        return "What word is this?"
    if screen == "letter_voice_challenge":
        return LETTER_VOICE_PROMPT
    if screen == "letter_listening_state":
        return "I'm listening carefully."
    if screen == "listening_state":
        return "I’m listening carefully."
    if screen == "progress_complete":
        return "Amazing work! You completed the world!"
    if screen == "badge_unlock":
        return "You earned a badge! Great job!"
    if screen == "offline_continue":
        return "No worries. We can continue offline."
    return "Let’s keep learning together!"
