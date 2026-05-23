"""Registry for mapping screen IDs to reference interface images."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenDefinition:
    screen_id: str
    image_filename: str


class ScreenRegistry:
    def __init__(self) -> None:
        self._definitions: list[ScreenDefinition] = [
            ScreenDefinition("splash_loading", "01_splash_loading.png"),
            ScreenDefinition("welcome", "02_welcome_start.png"),
            ScreenDefinition("profile_selection", "03_profile_selection.png"),
            ScreenDefinition("main_menu", "04_main_menu.png"),
            ScreenDefinition("how_to_play", "05_instruction_how_to_play.png"),
            ScreenDefinition("world_map", "06_world_map.png"),
            ScreenDefinition("letter_island_game", "07_letter_island_gameplay.png"),
            ScreenDefinition("letter_correct_feedback", "08_letter_correct_feedback.png"),
            ScreenDefinition("letter_mistake_hint", "09_letter_mistake_hint.png"),
            ScreenDefinition("bd_practice", "10_letter_bd_practice.png"),
            ScreenDefinition("word_garden_game", "11_word_garden_gameplay.png"),
            ScreenDefinition("word_correct_feedback", "12_word_correct_feedback.png"),
            ScreenDefinition("word_mistake_hint", "13_word_mistake_hint.png"),
            ScreenDefinition("voice_challenge", "14_voice_say_apple.png"),
            ScreenDefinition("listening_state", "15_voice_listening.png"),
            ScreenDefinition("voice_correct_feedback", "16_voice_result_correct.png"),
            ScreenDefinition("sentence_castle_game", "17_sentence_castle_gameplay.png"),
            ScreenDefinition("sentence_dragging", "18_sentence_dragging_state.png"),
            ScreenDefinition("sentence_mistake_hint", "19_sentence_mistake_hint.png"),
            ScreenDefinition("sentence_correct_feedback", "20_sentence_correct_feedback.png"),
            ScreenDefinition("badge_unlock", "21_badge_unlock.png"),
            ScreenDefinition("progress_complete", "22_progress_level_complete.png"),
            ScreenDefinition("practice_weak_skills", "23_practice_weak_skills.png"),
            ScreenDefinition("teacher_report", "24_teacher_report.png"),
            ScreenDefinition("settings", "25_settings.png"),
            ScreenDefinition("microphone_check", "26_microphone_check.png"),
            ScreenDefinition("end_session", "27_end_session_celebration.png"),
            ScreenDefinition("offline_continue", "28_continue_offline.png"),
        ]
        self._definition_map = {definition.screen_id: definition for definition in self._definitions}

    @property
    def screen_ids(self) -> list[str]:
        return [definition.screen_id for definition in self._definitions]

    def get_image_filename(self, screen_id: str) -> str:
        return self._definition_map[screen_id].image_filename

    def next_screen_id(self, screen_id: str) -> str:
        index = self.screen_ids.index(screen_id)
        return self.screen_ids[(index + 1) % len(self._definitions)]

    def previous_screen_id(self, screen_id: str) -> str:
        index = self.screen_ids.index(screen_id)
        return self.screen_ids[(index - 1) % len(self._definitions)]
