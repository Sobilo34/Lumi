"""Main runtime loop and screen orchestration."""
from __future__ import annotations

from pathlib import Path
import json

import pygame

from config import DEBUG_HITBOXES, SCREEN_SPECS_PATH, SPLASH_DURATION_MS, VOICE_FALLBACK_SCREEN_ID
from engine.game_state import GameState
from ui.screens import build_screen_from_spec


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self.specs = self._load_specs()
        self.screens = {spec["id"]: build_screen_from_spec(spec) for spec in self.specs}
        self.current_screen = self.screens[self.state.current_screen_id]

    def _load_specs(self) -> list[dict]:
        with SCREEN_SPECS_PATH.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload["screens"]

    def set_screen(self, screen_id: str) -> None:
        if screen_id in self.screens:
            self.state.current_screen_id = screen_id
            self.current_screen = self.screens[screen_id]
            self.state.history.append(screen_id)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hitbox = self.current_screen.handle_click(event.pos)
            if hitbox and hitbox.target:
                self.set_screen(hitbox.target)

    def update(self) -> None:
        if self.state.current_screen_id == "01_splash_loading":
            elapsed = pygame.time.get_ticks() - self.state.splash_started_at
            if elapsed >= SPLASH_DURATION_MS:
                self.set_screen("02_welcome_start")

    def draw(self) -> None:
        self.current_screen.draw(self.screen, debug_hitboxes=DEBUG_HITBOXES)
        if self.state.current_screen_id == VOICE_FALLBACK_SCREEN_ID:
            pygame.display.set_caption("Lumi's Word Adventure - Offline Mode")
