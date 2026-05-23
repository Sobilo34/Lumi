"""Main runtime loop and screen orchestration."""
from __future__ import annotations

import pygame

from config import DEBUG_HITBOXES, SPLASH_DURATION_MS, VOICE_FALLBACK_SCREEN_ID
from engine.asset_manager import AssetManager
from engine.game_state import GameState
from engine.screen_registry import ScreenRegistry
from ui.screens import create_screen_with_hitboxes


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.asset_manager = AssetManager()
        self.registry = ScreenRegistry()
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self.screens = {
            screen_id: create_screen_with_hitboxes(
                self.registry.get_image_filename(screen_id),
                self.registry.get_hitboxes(screen_id),
                self.asset_manager,
            )
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
            self._handle_action(action)

    def _handle_action(self, action: str) -> None:
        if action in self.screens:
            self.set_screen(action)
            return
        if action == "back" or action == "home":
            self.set_screen("main_menu")
            return
        if action == "go_to_profile_selection":
            self.set_screen("profile_selection")
            return
        if action == "go_to_world_map":
            self.set_screen("world_map")
            return
        if action == "start_play":
            self.set_screen("world_map")
            return
        if action == "open_settings" or action == "settings":
            self.set_screen("settings")
            return
        if action == "test_mic" or action == "test_microphone":
            self.set_screen("microphone_check")
            return
        if action == "skip_mic":
            self.set_screen("settings")
            return
        if action == "play_again":
            self.set_screen("world_map")
            return
        if action == "view_report" or action == "open_report":
            self.set_screen("teacher_report")
            return
        if action == "continue_offline":
            self.set_screen("main_menu")
            return
        if action == "repeat_instruction_audio" or action == "repeat_instruction":
            return
        if action == "replay_welcome_audio" or action == "replay_main_menu_audio" or action == "replay_instruction_audio":
            return
        if action == "toggle_music" or action == "toggle_voice" or action == "change_difficulty" or action == "reset_progress":
            return
        if action == "show_profile" or action == "repeat_prompt" or action == "show_hint" or action == "voice_or_speak_mode":
            return
        if action == "next_activity":
            self.set_screen("word_garden_game")
            return

    def update(self) -> None:
        self.current_screen.update()

    def draw(self) -> None:
        self.current_screen.draw(self.screen, debug_hitboxes=DEBUG_HITBOXES)
        if self.state.current_screen_id == VOICE_FALLBACK_SCREEN_ID:
            pygame.display.set_caption("Lumi's Word Adventure - Offline Mode")
