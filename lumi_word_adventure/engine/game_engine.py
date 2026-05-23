"""Main runtime loop and screen orchestration."""
from __future__ import annotations

import pygame

from config import DEBUG_HITBOXES, SPLASH_DURATION_MS, VOICE_ENABLED_DEFAULT, VOICE_FALLBACK_SCREEN_ID
from engine.asset_manager import AssetManager
from engine.learner_model import LearnerModel
from engine.game_state import GameState
from engine.screen_registry import ScreenRegistry
from engine.feedback import get_feedback, get_lumi_speech
from reports.report_generator import generate_report
from ui.screens import create_screen_with_hitboxes
from voice.text_to_speech import TextToSpeech


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.asset_manager = AssetManager()
        self.registry = ScreenRegistry()
        self.voice = TextToSpeech(enabled=VOICE_ENABLED_DEFAULT)
        self.learner = LearnerModel()
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self.voice.set_enabled(self.state.voice_enabled)
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
            self._speak_for_screen(screen_id)

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
        if action == "toggle_music" or action == "change_difficulty" or action == "reset_progress":
            return
        if action == "toggle_voice":
            self.state.voice_enabled = not self.state.voice_enabled
            self.voice.set_enabled(self.state.voice_enabled)
            if self.state.voice_enabled:
                self.voice.speak("Voice is on.")
            return
        if action == "show_profile" or action == "repeat_prompt" or action == "show_hint" or action == "voice_or_speak_mode":
            if action == "show_hint":
                self.voice.speak(get_feedback("hint")["message"])
            elif action == "repeat_prompt":
                self.voice.speak(get_lumi_speech(self.state.current_screen_id))
            return
        if action == "next_activity":
            self.set_screen("word_garden_game")
            return

    def _speak_for_screen(self, screen_id: str) -> None:
        if not self.state.voice_enabled:
            return

        if screen_id in {"welcome", "how_to_play", "world_map", "voice_challenge", "listening_state", "offline_continue"}:
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id in {"letter_island_game", "word_garden_game", "sentence_castle_game"}:
            self.voice.speak(get_lumi_speech(screen_id))
            return

        if screen_id in {"letter_correct_feedback", "word_correct_feedback", "sentence_correct_feedback", "voice_correct_feedback"}:
            self.voice.speak(get_feedback(True)["message"])
            return

        if screen_id in {"letter_mistake_hint", "word_mistake_hint", "sentence_mistake_hint"}:
            self.voice.speak(get_feedback("hint")["message"])
            return

        if screen_id == "badge_unlock":
            self.voice.speak(get_feedback("badge_unlock")["message"])
            return

        if screen_id == "progress_complete":
            self.voice.speak(get_feedback("level_complete")["message"])
            return

        if screen_id == "teacher_report":
            report = generate_report(self.learner.get_profile())
            self.voice.speak(
                f"{report['child_name']} has {report['stars']} stars and {report['correct_answers']} correct answers."
            )

    def update(self) -> None:
        self.current_screen.update()
        if self.state.current_screen_id == "splash_loading":
            elapsed = pygame.time.get_ticks() - self.state.splash_started_at
            if elapsed >= SPLASH_DURATION_MS:
                self.set_screen("welcome")

    def stop(self) -> None:
        self.voice.stop()

    def draw(self) -> None:
        self.current_screen.draw(self.screen, debug_hitboxes=DEBUG_HITBOXES)
        if self.state.current_screen_id == VOICE_FALLBACK_SCREEN_ID:
            pygame.display.set_caption("Lumi's Word Adventure - Offline Mode")
