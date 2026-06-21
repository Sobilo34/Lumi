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
    feedback_message: str = ""
    music_enabled: bool = True
    voice_enabled: bool = True
    difficulty_mode: str = "Medium"
    settings_status: str = ""
    teacher_report: dict[str, Any] = field(default_factory=dict)
    offline_message: str = ""
    microphone_status: str = ""
    practice_cards: tuple[str, ...] = ("Practice B / D", "Practice Words")
    badge_names: tuple[str, ...] = ()
    loading_progress: float = 0.66
    highlight_letter_slot: int = -1
    letter_success_slot: int = -1
    letter_success_progress: float = 0.0
    # Points / rewards
    total_points: int = 0
    points_rank: str = "Little Sprout"
    points_emoji: str = "🌱"
    points_progress: float = 0.0
    points_to_next: int = 0
    next_rank_name: str = ""
    best_streak: int = 0
    current_streak: int = 0
    badges_count: int = 0
    last_points_awarded: int = 0
