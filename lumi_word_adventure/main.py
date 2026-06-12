"""Application entry point for Lumi's Word Adventure."""
from __future__ import annotations

try:
    import pygame
except ModuleNotFoundError as error:
    raise SystemExit(
        "Pygame is required. Install dependencies with:\n"
        "  pip install -r lumi_word_adventure/requirements.txt"
    ) from error

from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from engine.game_engine import GameEngine


def _init_optional_audio() -> None:
    """Start pygame.mixer when available; missing audio must not block the game."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception as error:
        print(f"[Lumi Audio] Optional mixer unavailable: {error}")


def main() -> None:
    pygame.init()
    _init_optional_audio()
    pygame.display.set_caption("Lumi's Word Adventure")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    if screen.get_size() != (SCREEN_WIDTH, SCREEN_HEIGHT):
        print(
            f"[Lumi] Warning: display size is {screen.get_size()}, "
            f"expected {(SCREEN_WIDTH, SCREEN_HEIGHT)}."
        )
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
        engine.stop()
        pygame.quit()


if __name__ == "__main__":
    main()
