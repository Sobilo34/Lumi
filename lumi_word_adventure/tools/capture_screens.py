"""Headless capture of selected screens to PNG for visual review."""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("LUMI_SKIP_PREWARM", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH

TARGETS = (
    "welcome",
    "how_to_play",
    "main_menu",
    "world_map",
    "settings",
    "letter_island_game",
    "word_garden_game",
    "voice_challenge",
    "badge_unlock",
    "progress_complete",
    "teacher_report",
    "end_session",
    "points_page",
)


def main() -> int:
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    from voice.text_to_speech import TextToSpeech

    TextToSpeech._initialize_engine = lambda self: setattr(self, "_available", False)

    from engine.game_engine import GameEngine

    engine = GameEngine(pygame.display.get_surface())
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "screenshots")
    os.makedirs(out_dir, exist_ok=True)

    for screen_id in TARGETS:
        if screen_id == "points_page":
            engine.learner.total_points = 320
            engine.learner.best_streak = 7
            engine.learner.correct_streak = 3
        engine.change_screen(screen_id)
        if screen_id == "badge_unlock":
            engine.state.last_unlocked_badges = ["Rising Reader"]
        engine.draw()
        path = os.path.join(out_dir, f"{screen_id}.png")
        pygame.image.save(engine.screen, path)
        print(path)

    pygame.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
