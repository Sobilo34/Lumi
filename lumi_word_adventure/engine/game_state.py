"""Shared runtime state for the game."""
from __future__ import annotations

from dataclasses import dataclass, field

from config import DEFAULT_DIFFICULTY, VOICE_ENABLED_DEFAULT


@dataclass
class GameState:
    current_screen_id: str = "splash_loading"
    selected_profile: str = "player_1"
    running: bool = True
    last_action: str = ""
    last_mistake_type: str = ""
    splash_started_at: int = 0
    stars: int = 0
    difficulty: int = DEFAULT_DIFFICULTY
    voice_enabled: bool = VOICE_ENABLED_DEFAULT
    current_task_prompt: str = ""
    current_task_target: str = ""
    current_hint_level: int = 0
    letter_demo_mode: bool = True
    preserve_word_garden_task: bool = False
    current_word_mode: str = ""
    word_garden_support: str = ""
    word_garden_option_count: int = 4
    last_word_selected: str = ""
    last_word_feedback_message: str = ""
    last_spoken_text: str = ""
    sentence_slots: list[str] = field(default_factory=lambda: ["", "", "", ""])
    sentence_locked_indices: list[int] = field(default_factory=list)
    sentence_target_words: list[str] = field(default_factory=lambda: ["I", "see", "a", "cat"])
    sentence_feedback_message: str = ""
    bd_practice_target: str = ""
    bd_practice_step: int = 0
    bd_confusion_attempts: int = 0
    history: list[str] = field(default_factory=list)
    last_unlocked_badges: list[str] = field(default_factory=list)
