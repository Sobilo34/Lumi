"""Dynamic view-model passed to component screen renderers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SceneView:
    screen_id: str = ""
    child_name: str = "Lumi"
    lumi_energy: int = 100
    lumi_energy_max: int = 100
    stars_filled: int = 0
    total_stars: int = 0
    progress_text: str = ""
    target_letter: str = "A"
    slot_letters: tuple[str, ...] = ()
    held_letter: str = ""
    target_word: str = "cat"
    slot_words: tuple[str, ...] = ()
    voice_target: str = "apple"
    voice_listening: bool = False
    sentence_prompt: str = "Build the sentence."
    sentence_words: tuple[str, ...] = ()
    sentence_slots: tuple[str, ...] = ()
    feedback_message: str = ""
    music_enabled: bool = True
    voice_enabled: bool = True
    difficulty_mode: str = "Medium"
    settings_status: str = ""
    teacher_report: dict[str, Any] = field(default_factory=dict)
    offline_message: str = ""
    microphone_status: str = ""
    practice_cards: tuple[str, ...] = ("Practice B / D", "Practice Words", "Practice Sentences")
    badge_names: tuple[str, ...] = ()
    loading_progress: float = 0.66
