"""Application entry point for Lumi's Word Adventure."""
from __future__ import annotations

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.game_engine import GameEngine


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lumi's Word Adventure")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    engine = GameEngine(screen)

    try:
        while engine.running:
            for event in pygame.event.get():
                engine.handle_event(event)
            engine.update()
            engine.draw()
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
