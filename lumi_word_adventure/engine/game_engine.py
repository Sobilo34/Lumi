"""Main runtime loop and screen orchestration."""
from __future__ import annotations

import pygame

from config import DEBUG_HITBOXES, SPLASH_DURATION_MS, VOICE_FALLBACK_SCREEN_ID
from engine.asset_manager import AssetManager
from engine.game_state import GameState
from engine.screen_registry import ScreenRegistry
from ui.screens import create_screen


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.asset_manager = AssetManager()
        self.registry = ScreenRegistry()
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self.screens = {
            screen_id: create_screen(self.registry.get_image_filename(screen_id), self.asset_manager)
            for screen_id in self.registry.screen_ids
        }
        self.state.current_screen_id = self.registry.screen_ids[0]
        self.current_screen = self.screens[self.state.current_screen_id]

    def change_screen(self, screen_id: str) -> None:
        if screen_id in self.screens:
            self.state.current_screen_id = screen_id
            self.current_screen = self.screens[screen_id]
            self.state.history.append(screen_id)

    def set_screen(self, screen_id: str) -> None:
        self.change_screen(screen_id)

    def next_screen(self) -> None:
        self.change_screen(self.registry.next_screen_id(self.state.current_screen_id))

    def previous_screen(self) -> None:
        self.change_screen(self.registry.previous_screen_id(self.state.current_screen_id))

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            self.next_screen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            self.previous_screen()
            return
        action = self.current_screen.handle_event(event)
        if action:
            self.set_screen(action)

    def update(self) -> None:
        self.current_screen.update()

    def draw(self) -> None:
        self.current_screen.draw(self.screen, debug_hitboxes=DEBUG_HITBOXES)
        if self.state.current_screen_id == VOICE_FALLBACK_SCREEN_ID:
            pygame.display.set_caption("Lumi's Word Adventure - Offline Mode")
