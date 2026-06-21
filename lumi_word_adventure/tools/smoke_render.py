"""Headless smoke test: build and draw every screen once to catch crashes."""
from __future__ import annotations

import os
import sys
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("LUMI_SKIP_PREWARM", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


def main() -> int:
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    from voice.text_to_speech import TextToSpeech

    TextToSpeech._initialize_engine = lambda self: setattr(self, "_available", False)

    from engine.game_engine import GameEngine

    screen = pygame.display.get_surface()
    engine = GameEngine(screen)

    failures: list[str] = []
    for screen_id in engine.registry.screen_ids:
        try:
            engine.change_screen(screen_id)
            engine.draw()
        except Exception:  # noqa: BLE001
            failures.append(f"{screen_id}:\n{traceback.format_exc()}")

    pygame.quit()
    if failures:
        print("FAILURES:")
        for failure in failures:
            print(failure)
        return 1
    print(f"OK: rendered {len(engine.registry.screen_ids)} screens without error")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
