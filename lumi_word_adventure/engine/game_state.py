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
    splash_started_at: int = 0
    stars: int = 0
    difficulty: int = DEFAULT_DIFFICULTY
    voice_enabled: bool = VOICE_ENABLED_DEFAULT
    history: list[str] = field(default_factory=list)
