"""Registry for mapping screen IDs to reference interface images."""
from __future__ import annotations

from dataclasses import dataclass

from ui.hitboxes import Hitbox


@dataclass(frozen=True)
class HitboxDefinition:
    name: str
    x_pct: float
    y_pct: float
    w_pct: float
    h_pct: float
    action: str = ""
    target: str = ""


@dataclass(frozen=True)
class ScreenDefinition:
    screen_id: str
    image_filename: str
    hitboxes: tuple[HitboxDefinition, ...] = ()


class ScreenRegistry:
    def __init__(self) -> None:
        self._definitions: list[ScreenDefinition] = [
            ScreenDefinition("splash_loading", "01_splash_loading.png"),
            ScreenDefinition(
                "welcome",
                "02_welcome_start.png",
                (
                    HitboxDefinition("Start", 0.38, 0.78, 0.24, 0.13, target="how_to_play"),
                    HitboxDefinition("Speaker", 0.02, 0.04, 0.06, 0.1, action="replay_welcome_audio"),
                ),
            ),
            ScreenDefinition(
                "profile_selection",
                "03_profile_selection.png",
                (
                    HitboxDefinition("Back", 0.01, 0.02, 0.07, 0.1, target="welcome"),
                    HitboxDefinition("Settings", 0.91, 0.03, 0.07, 0.1, target="settings"),
                    HitboxDefinition("Player 1", 0.22, 0.28, 0.18, 0.45, target="main_menu"),
                    HitboxDefinition("Player 2", 0.43, 0.28, 0.18, 0.45, target="main_menu"),
                    HitboxDefinition("New Player", 0.65, 0.28, 0.18, 0.45, target="main_menu"),
                ),
            ),
            ScreenDefinition(
                "main_menu",
                "04_main_menu.png",
                (
                    HitboxDefinition("Play", 0.57, 0.19, 0.33, 0.17, target="world_map"),
                    HitboxDefinition("Practice", 0.57, 0.4, 0.33, 0.16, target="practice_weak_skills"),
                    HitboxDefinition("Report", 0.57, 0.59, 0.33, 0.15, target="teacher_report"),
                    HitboxDefinition("Settings", 0.57, 0.76, 0.33, 0.15, target="settings"),
                    HitboxDefinition("Speaker", 0.02, 0.04, 0.07, 0.1, action="replay_main_menu_audio"),
                    HitboxDefinition("Profile", 0.88, 0.03, 0.07, 0.1, action="show_profile"),
                ),
            ),
            ScreenDefinition(
                "how_to_play",
                "05_instruction_how_to_play.png",
                (
                    HitboxDefinition("Let's Go", 0.34, 0.82, 0.31, 0.13, target="world_map"),
                    HitboxDefinition("Speaker", 0.7, 0.82, 0.08, 0.13, action="replay_instruction_audio"),
                ),
            ),
            ScreenDefinition(
                "world_map",
                "06_world_map.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="main_menu"),
                    HitboxDefinition("My Words", 0.87, 0.12, 0.08, 0.13, target="practice_weak_skills"),
                    HitboxDefinition("Letter Island", 0.12, 0.4, 0.22, 0.33, target="letter_island_game"),
                    HitboxDefinition("Word Garden", 0.39, 0.38, 0.22, 0.35, target="word_garden_game"),
                    HitboxDefinition("Sentence Castle", 0.68, 0.38, 0.24, 0.36, target="sentence_castle_game"),
                ),
            ),
            ScreenDefinition(
                "letter_island_game",
                "07_letter_island_gameplay.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.1, target="settings"),
                    HitboxDefinition("Card B", 0.29, 0.41, 0.13, 0.25, action="select_letter_b"),
                    HitboxDefinition("Card D", 0.43, 0.41, 0.13, 0.25, action="select_letter_d"),
                    HitboxDefinition("Card P", 0.57, 0.41, 0.13, 0.25, action="select_letter_p"),
                    HitboxDefinition("Card A", 0.71, 0.41, 0.13, 0.25, action="select_letter_a"),
                    HitboxDefinition("Repeat", 0.31, 0.77, 0.1, 0.18, action="repeat_prompt"),
                    HitboxDefinition("Hint", 0.45, 0.77, 0.11, 0.18, action="show_hint"),
                    HitboxDefinition("Speak", 0.6, 0.77, 0.1, 0.18, action="voice_or_speak_mode"),
                ),
            ),
            ScreenDefinition(
                "letter_correct_feedback",
                "08_letter_correct_feedback.png",
                (
                    HitboxDefinition("Next", 0.36, 0.79, 0.29, 0.15, action="next_activity"),
                ),
            ),
            ScreenDefinition(
                "letter_mistake_hint",
                "09_letter_mistake_hint.png",
                (
                    HitboxDefinition("Try Again", 0.26, 0.8, 0.17, 0.12, action="try_again"),
                    HitboxDefinition("Repeat", 0.45, 0.8, 0.17, 0.12, action="repeat_prompt"),
                    HitboxDefinition("Hint", 0.64, 0.8, 0.17, 0.12, action="next_hint_or_bd_practice"),
                ),
            ),
            ScreenDefinition(
                "bd_practice",
                "10_letter_bd_practice.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Repeat", 0.82, 0.05, 0.07, 0.12, action="repeat_bd_prompt"),
                    HitboxDefinition("Hint", 0.91, 0.05, 0.07, 0.12, action="bd_hint"),
                    HitboxDefinition("Answer B", 0.26, 0.78, 0.24, 0.13, action="answer_B"),
                    HitboxDefinition("Answer D", 0.53, 0.78, 0.24, 0.13, action="answer_D"),
                ),
            ),
            ScreenDefinition(
                "word_garden_game",
                "11_word_garden_gameplay.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Card cat", 0.24, 0.39, 0.14, 0.27, action="answer_cat_correct"),
                    HitboxDefinition("Card dog", 0.4, 0.39, 0.14, 0.27, action="answer_dog_wrong"),
                    HitboxDefinition("Card sun", 0.56, 0.39, 0.14, 0.27, action="answer_sun_wrong"),
                    HitboxDefinition("Card ball", 0.72, 0.39, 0.14, 0.27, action="answer_ball_wrong"),
                    HitboxDefinition("Repeat", 0.31, 0.77, 0.1, 0.18, action="repeat_prompt"),
                    HitboxDefinition("Hint", 0.45, 0.77, 0.11, 0.18, action="show_hint"),
                    HitboxDefinition("Speak", 0.6, 0.77, 0.1, 0.18, action="voice_mode"),
                ),
            ),
            ScreenDefinition(
                "word_correct_feedback",
                "12_word_correct_feedback.png",
                (
                    HitboxDefinition("Next", 0.37, 0.82, 0.27, 0.13, action="next_voice_challenge"),
                    HitboxDefinition("Home", 0.91, 0.03, 0.07, 0.1, target="world_map"),
                ),
            ),
            ScreenDefinition(
                "word_mistake_hint",
                "13_word_mistake_hint.png",
                (
                    HitboxDefinition("Try Again", 0.25, 0.78, 0.2, 0.14, action="try_again"),
                    HitboxDefinition("Repeat", 0.48, 0.78, 0.2, 0.14, action="repeat_prompt"),
                    HitboxDefinition("Hint", 0.7, 0.78, 0.16, 0.14, action="show_next_hint"),
                    HitboxDefinition("speaker on cat card", 0.28, 0.42, 0.07, 0.11, action="play_cat_sound"),
                ),
            ),
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
            ScreenDefinition(
                "settings",
                "25_settings.png",
                (
                    HitboxDefinition("Back", 0.02, 0.03, 0.06, 0.09, target="main_menu"),
                    HitboxDefinition("Home", 0.91, 0.03, 0.07, 0.09, target="main_menu"),
                    HitboxDefinition("Music", 0.72, 0.2, 0.12, 0.08, action="toggle_music"),
                    HitboxDefinition("Voice", 0.72, 0.33, 0.12, 0.08, action="toggle_voice"),
                    HitboxDefinition("Test Mic", 0.63, 0.46, 0.19, 0.08, target="microphone_check"),
                    HitboxDefinition("Difficulty", 0.66, 0.58, 0.16, 0.09, action="change_difficulty"),
                    HitboxDefinition("Reset", 0.69, 0.72, 0.14, 0.08, action="reset_progress"),
                ),
            ),
            ScreenDefinition(
                "microphone_check",
                "26_microphone_check.png",
                (
                    HitboxDefinition("Home", 0.91, 0.03, 0.07, 0.09, target="main_menu"),
                    HitboxDefinition("Test Mic", 0.3, 0.75, 0.3, 0.15, target="listening_state"),
                    HitboxDefinition("Skip", 0.64, 0.78, 0.13, 0.1, target="settings"),
                ),
            ),
            ScreenDefinition(
                "end_session",
                "27_end_session_celebration.png",
                (
                    HitboxDefinition("Play Again", 0.25, 0.73, 0.23, 0.13, target="world_map"),
                    HitboxDefinition("View Report", 0.53, 0.73, 0.25, 0.13, target="teacher_report"),
                ),
            ),
            ScreenDefinition(
                "offline_continue",
                "28_continue_offline.png",
                (
                    HitboxDefinition("Continue Offline", 0.36, 0.65, 0.29, 0.13, target="main_menu"),
                ),
            ),
        ]
        self._definition_map = {definition.screen_id: definition for definition in self._definitions}

    @property
    def screen_ids(self) -> list[str]:
        return [definition.screen_id for definition in self._definitions]

    def get_image_filename(self, screen_id: str) -> str:
        return self._definition_map[screen_id].image_filename

    def get_hitboxes(self, screen_id: str) -> list[Hitbox]:
        definition = self._definition_map[screen_id]
        return [
            Hitbox.from_normalized(
                hitbox.name,
                (1280, 720),
                hitbox.x_pct,
                hitbox.y_pct,
                hitbox.w_pct,
                hitbox.h_pct,
                action=hitbox.action,
                target=hitbox.target,
            )
            for hitbox in definition.hitboxes
        ]

    def next_screen_id(self, screen_id: str) -> str:
        index = self.screen_ids.index(screen_id)
        return self.screen_ids[(index + 1) % len(self._definitions)]

    def previous_screen_id(self, screen_id: str) -> str:
        index = self.screen_ids.index(screen_id)
        return self.screen_ids[(index - 1) % len(self._definitions)]
