"""Shared runtime state for the game."""
from __future__ import annotations

from dataclasses import dataclass, field

from config import DEFAULT_DIFFICULTY


@dataclass
class GameState:
    current_screen_id: str = "01_splash_loading"
    selected_profile: str = "player_1"
    running: bool = True
    last_action: str = ""
    splash_started_at: int = 0
    stars: int = 0
    difficulty: int = DEFAULT_DIFFICULTY
    history: list[str] = field(default_factory=list)
