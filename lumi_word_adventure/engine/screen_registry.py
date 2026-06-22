"""Registry for mapping screen IDs to reference interface images."""
from __future__ import annotations

from dataclasses import dataclass

from ui.hitboxes import Hitbox
from ui.voice_footer_layout import footer_slots
from ui.writing_footer_layout import writing_footer_slots


def _footer_hitboxes(
    *,
    names: tuple[str, ...],
    actions: tuple[str, ...],
) -> tuple[HitboxDefinition, ...]:
    slots = footer_slots(len(names))
    return tuple(
        HitboxDefinition(name, x_pct, y_pct, w_pct, h_pct, action=action)
        for name, (x_pct, y_pct, w_pct, h_pct), action in zip(names, slots, actions)
    )


def _voice_footer_hitboxes(
    *,
    repeat_action: str,
    speak_action: str,
    hint_action: str,
    skip_action: str,
) -> tuple[HitboxDefinition, ...]:
    return _footer_hitboxes(
        names=("Repeat", "Speak", "Hint", "Skip"),
        actions=(repeat_action, speak_action, hint_action, skip_action),
    )


def _writing_footer_hitboxes() -> tuple[HitboxDefinition, ...]:
    slots = writing_footer_slots()
    names = ("Verify", "Clear", "Switch mode")
    actions = ("verify_writing", "clear_writing", "toggle_writing_mode")
    return tuple(
        HitboxDefinition(name, x_pct, y_pct, w_pct, h_pct, action=action)
        for name, (x_pct, y_pct, w_pct, h_pct), action in zip(names, slots, actions)
    )


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
                (HitboxDefinition("Start", 0.36, 0.82, 0.28, 0.11, target="how_to_play"),),
            ),
            ScreenDefinition(
                "profile_selection",
                "03_profile_selection.png",
                (
                    HitboxDefinition("Back", 0.015, 0.035, 0.07, 0.11, target="welcome"),
                    HitboxDefinition("Settings", 0.915, 0.035, 0.07, 0.11, target="settings"),
                    HitboxDefinition("Player 1", 0.22, 0.28, 0.18, 0.45, target="main_menu"),
                    HitboxDefinition("Player 2", 0.41, 0.28, 0.18, 0.45, target="main_menu"),
                    HitboxDefinition("New Player", 0.63, 0.28, 0.18, 0.45, target="main_menu"),
                ),
            ),
            ScreenDefinition(
                "main_menu",
                "04_main_menu.png",
                (
                    HitboxDefinition("Play", 0.48, 0.20, 0.46, 0.14, target="world_map"),
                    HitboxDefinition("Practice", 0.48, 0.36, 0.46, 0.14, target="practice_weak_skills"),
                    HitboxDefinition("Report", 0.48, 0.52, 0.46, 0.14, target="teacher_report"),
                    HitboxDefinition("Settings", 0.48, 0.68, 0.46, 0.14, target="settings"),
                    HitboxDefinition("Speaker", 0.02, 0.03, 0.09, 0.11, action="replay_main_menu_audio"),
                    HitboxDefinition("Profile", 0.89, 0.03, 0.09, 0.11, action="show_profile"),
                ),
            ),
            ScreenDefinition(
                "how_to_play",
                "05_instruction_how_to_play.png",
                (
                    HitboxDefinition("Let's Go", 0.28, 0.76, 0.44, 0.16, target="world_map"),
                ),
            ),
            ScreenDefinition(
                "world_map",
                "06_world_map.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="main_menu"),
                    HitboxDefinition("My Points", 0.34, 0.016, 0.32, 0.085, target="points_page"),
                    HitboxDefinition("Letter Island", 0.11, 0.30, 0.22, 0.36, target="letter_island_game"),
                    HitboxDefinition("Word Garden", 0.39, 0.30, 0.22, 0.36, target="word_garden_game"),
                    HitboxDefinition("Writing Castle", 0.67, 0.30, 0.22, 0.36, target="writing_castle_game"),
                ),
            ),
            ScreenDefinition(
                "writing_castle_game",
                "17_sentence_castle_gameplay.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.10, action="home"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.10, target="settings"),
                    *_writing_footer_hitboxes(),
                ),
            ),
            ScreenDefinition(
                "letter_island_game",
                "07_letter_island_gameplay.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.1, target="settings"),
                    HitboxDefinition("Card B", 0.29, 0.41, 0.13, 0.25, action="select_letter_slot_0"),
                    HitboxDefinition("Card D", 0.43, 0.41, 0.13, 0.25, action="select_letter_slot_1"),
                    HitboxDefinition("Card P", 0.57, 0.41, 0.13, 0.25, action="select_letter_slot_2"),
                    HitboxDefinition("Card A", 0.71, 0.41, 0.13, 0.25, action="select_letter_slot_3"),
                    *_footer_hitboxes(
                        names=("Repeat", "Hint", "Speak"),
                        actions=("repeat_prompt", "show_hint", "voice_or_speak_mode"),
                    ),
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
                "letter_voice_challenge",
                "14_voice_say_apple.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.1, target="settings"),
                    *_voice_footer_hitboxes(
                        repeat_action="repeat_letter",
                        speak_action="start_letter_listening",
                        hint_action="letter_voice_help",
                        skip_action="skip_letter_voice",
                    ),
                ),
            ),
            ScreenDefinition(
                "letter_listening_state",
                "15_voice_listening.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.1, target="settings"),
                    HitboxDefinition("Stop", 0.35, 0.77, 0.27, 0.15, action="stop_letter_listening"),
                    HitboxDefinition("Repeat letter", 0.67, 0.8, 0.15, 0.1, action="repeat_letter"),
                ),
            ),
            ScreenDefinition(
                "word_garden_game",
                "11_word_garden_gameplay.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="world_map"),
                    HitboxDefinition("Settings", 0.92, 0.02, 0.06, 0.1, target="settings"),
                    HitboxDefinition("Card cat", 0.24, 0.39, 0.14, 0.27, action="select_word_slot_0"),
                    HitboxDefinition("Card dog", 0.4, 0.39, 0.14, 0.27, action="select_word_slot_1"),
                    HitboxDefinition("Card sun", 0.56, 0.39, 0.14, 0.27, action="select_word_slot_2"),
                    HitboxDefinition("Card ball", 0.72, 0.39, 0.14, 0.27, action="select_word_slot_3"),
                    *_footer_hitboxes(
                        names=("Repeat", "Hint", "Speak"),
                        actions=("repeat_prompt", "show_hint", "voice_mode"),
                    ),
                ),
            ),
            ScreenDefinition(
                "voice_challenge",
                "14_voice_say_apple.png",
                (
                    HitboxDefinition("Home", 0.91, 0.02, 0.07, 0.1, target="world_map"),
                    *_voice_footer_hitboxes(
                        repeat_action="repeat_word",
                        speak_action="start_listening",
                        hint_action="voice_help",
                        skip_action="skip_voice",
                    ),
                ),
            ),
            ScreenDefinition(
                "listening_state",
                "15_voice_listening.png",
                (
                    HitboxDefinition("Stop", 0.35, 0.77, 0.27, 0.15, action="stop_listening"),
                    HitboxDefinition("Repeat word", 0.67, 0.8, 0.15, 0.1, action="repeat_word"),
                ),
            ),
            ScreenDefinition(
                "badge_unlock",
                "21_badge_unlock.png",
                (
                    HitboxDefinition("Next", 0.38, 0.835, 0.24, 0.1, action="continue_from_badge"),
                ),
            ),
            ScreenDefinition(
                "progress_complete",
                "22_progress_level_complete.png",
                (
                    HitboxDefinition("Next World", 0.105, 0.80, 0.24, 0.12, action="next_world"),
                    HitboxDefinition("Practice Again", 0.38, 0.80, 0.24, 0.12, action="practice_again"),
                    HitboxDefinition("View Report", 0.655, 0.80, 0.24, 0.12, action="view_report"),
                ),
            ),
            ScreenDefinition(
                "practice_weak_skills",
                "23_practice_weak_skills.png",
                (
                    # tuned positions/sizes for closer alignment to reference PNG
                    HitboxDefinition("Practice B", 0.195, 0.455, 0.22, 0.20, action="practice_bd_b"),
                    HitboxDefinition("Practice D", 0.425, 0.455, 0.22, 0.20, action="practice_bd_d"),
                    HitboxDefinition("Practice Word Cat", 0.655, 0.455, 0.22, 0.20, action="practice_word_cat"),
                ),
            ),
            ScreenDefinition(
                "teacher_report",
                "24_teacher_report.png",
                (
                    HitboxDefinition("Back", 0.02, 0.03, 0.07, 0.10, action="back"),
                    HitboxDefinition("Home", 0.11, 0.03, 0.07, 0.09, action="home"),
                    HitboxDefinition(
                        "Recommended practice",
                        0.60,
                        0.60,
                        0.28,
                        0.25,
                        action="practice_recommendation",
                    ),
                    HitboxDefinition("Refresh", 0.87, 0.77, 0.11, 0.12, action="report_refresh"),
                ),
            ),
            ScreenDefinition(
                "settings",
                "25_settings.png",
                (
                    HitboxDefinition("Back", 0.02, 0.03, 0.06, 0.09, target="main_menu"),
                    HitboxDefinition("Home", 0.91, 0.03, 0.07, 0.09, target="main_menu"),
                    HitboxDefinition("Music", 0.59, 0.19, 0.13, 0.09, action="toggle_music"),
                    HitboxDefinition("Voice", 0.59, 0.34, 0.14, 0.08, action="toggle_voice"),
                    HitboxDefinition("Test Mic", 0.58, 0.395, 0.14, 0.07, target="microphone_check"),
                    HitboxDefinition("Difficulty", 0.57, 0.505, 0.15, 0.075, action="change_difficulty"),
                    HitboxDefinition("Reset", 0.62, 0.585, 0.17, 0.11, action="reset_progress"),
                    # Developer testing buttons (temporary, visible in settings)
                    HitboxDefinition("Dev Export Hitboxes", 0.12, 0.82, 0.34, 0.06, action="export_hitboxes"),
                    HitboxDefinition("Dev Smoke -", 0.52, 0.82, 0.12, 0.06, action="decrease_smoke"),
                    HitboxDefinition("Dev Smoke +", 0.66, 0.82, 0.12, 0.06, action="increase_smoke"),
                    HitboxDefinition("Dev Toggle Hitboxes", 0.12, 0.85, 0.34, 0.08, action="toggle_hitbox_persistent"),
                    HitboxDefinition("Dev Run Hitbox Smoke", 0.52, 0.85, 0.44, 0.08, action="run_hitbox_smoke"),
                ),
            ),
            ScreenDefinition(
                "microphone_check",
                "26_microphone_check.png",
                (
                    HitboxDefinition("Home", 0.91, 0.03, 0.07, 0.09, target="main_menu"),
                    HitboxDefinition("Test Mic", 0.3, 0.75, 0.3, 0.15, action="test_microphone", target="listening_state"),
                    HitboxDefinition("Skip", 0.64, 0.78, 0.13, 0.1, action="skip_mic", target="settings"),
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
                    HitboxDefinition(
                        "Continue Offline",
                        0.36,
                        0.65,
                        0.29,
                        0.13,
                        action="continue_offline",
                        target="main_menu",
                    ),
                ),
            ),
            ScreenDefinition(
                "points_page",
                "29_points.png",
                (
                    HitboxDefinition("Home", 0.01, 0.02, 0.06, 0.1, target="main_menu"),
                    HitboxDefinition("Play", 0.36, 0.84, 0.28, 0.12, target="world_map"),
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
