"""Child-friendly feedback helpers."""
from __future__ import annotations

from typing import Any


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

    if feedback_key == "close" or mistake_type == "voice_close":
        return _feedback_payload("close", "Almost! I heard something close. Try again.")

    if mistake_type == "bd_confusion":
        return _feedback_payload("incorrect", "Good try! B has a belly. D has a drum.")

    if mistake_type == "same_category_vocabulary_confusion":
        if selected:
            return _feedback_payload("incorrect", f"This is {selected}. A cat says meow. Find the cat.")
        return _feedback_payload("incorrect", "This is dog. A cat says meow. Find the cat.")

    if mistake_type == "word_confusion":
        if target and selected:
            return _feedback_payload("incorrect", f"This is {selected}. Look for the cat.")
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


def get_hint(activity_type: str, hint_level: int | str, target: str) -> str:
    activity = activity_type.strip().lower()
    target_text = target.strip() if target else ""
    level = str(hint_level).strip()

    if activity == "letter":
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
            return f"Listen carefully and say {target_text}."
        if level in {"2", "level_2"}:
            return f"Try saying {target_text} a little slower."
        return f"You’re doing well. Say {target_text} again."

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
    if screen == "word_correct_feedback":
        return f"Wonderful! {task.capitalize()}." if task else "Wonderful!"
    if screen == "sentence_castle_game":
        return f"Put the sentence together, {task}." if task else "Put the sentence together."
    if screen == "voice_challenge":
        return f"Say the word with me, {task}." if task else "Say the word with me."
    if screen == "listening_state":
        return "I’m listening carefully."
    if screen == "progress_complete":
        return "Amazing work! You completed the world!"
    if screen == "badge_unlock":
        return "You earned a badge! Great job!"
    if screen == "offline_continue":
        return "No worries. We can continue offline."
    return "Let’s keep learning together!"
