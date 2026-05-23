"""Application entry point for Lumi's Word Adventure."""
from __future__ import annotations

import pygame

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.asset_manager import AssetManager
from ui.screens import create_temporary_splash_test_screen


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Lumi's Word Adventure")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    asset_manager = AssetManager()
    test_screen = create_temporary_splash_test_screen(asset_manager)

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
            test_screen.update()
            test_screen.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
