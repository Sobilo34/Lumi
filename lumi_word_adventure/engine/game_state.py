"""Shared runtime state for the game."""
from __future__ import annotations

from dataclasses import dataclass, field

from config import DEFAULT_DIFFICULTY, VOICE_ENABLED_DEFAULT


@dataclass
class GameState:
    current_screen_id: str = "splash_loading"
    selected_profile: str = "player_1"
    running: bool = True
    last_action: str = ""
    last_mistake_type: str = ""
    splash_started_at: int = 0
    stars: int = 0
    difficulty: int = DEFAULT_DIFFICULTY
    music_enabled: bool = True
    voice_enabled: bool = VOICE_ENABLED_DEFAULT
    current_task_prompt: str = ""
    current_task_target: str = ""
    current_hint_level: int = 0
    letter_demo_mode: bool = False
    preserve_word_garden_task: bool = False
    preserve_letter_island_task: bool = False
    preserve_writing_castle_task: bool = False
    gameplay_refresh_pending: bool = False
    letter_choice_slots: list[str] = field(default_factory=lambda: ["B", "D", "P", "A"])
    word_choice_slots: list[str] = field(default_factory=lambda: ["sun", "apple", "fish", "bird"])
    letter_review_mode: bool = False
    pending_letter_curriculum_advance: bool = False
    completed_letter_target: str = ""
    completed_letter_choices: list[str] = field(default_factory=list)
    current_word_mode: str = ""
    word_garden_support: str = ""
    word_garden_option_count: int = 4
    last_word_selected: str = ""
    last_word_feedback_message: str = ""
    last_word_garden_target: str = ""
    last_letter_feedback_message: str = ""
    last_selected_letter: str = ""
    highlight_letter_slot: int = -1
    last_spoken_text: str = ""
    sentence_slots: list[str] = field(default_factory=lambda: ["", "", "", ""])
    sentence_locked_indices: list[int] = field(default_factory=list)
    sentence_target_words: list[str] = field(default_factory=lambda: ["I", "see", "a", "cat"])
    sentence_feedback_message: str = ""
    bd_practice_target: str = ""
    bd_practice_step: int = 0
    bd_confusion_attempts: int = 0
    bd_practice_session_wrong: int = 0
    bd_practice_session_hints: int = 0
    history: list[str] = field(default_factory=list)
    last_unlocked_badges: list[str] = field(default_factory=list)
    badge_return_screen: str = ""
    world_map_status_message: str = ""
    world_map_status_shown_at_ms: int | None = None
    practice_recommendation: dict | None = None
    debug_persistent: bool = False
    debug_smoke_duration_ms: int = 5000
    last_export_path: str | None = None
    last_export_time_ms: int | None = None
    export_display_duration_ms: int = 5000
    teacher_report: dict | None = None
    microphone_test_mode: bool = False
    microphone_status_message: str = ""
    microphone_return_screen: str = "settings"
    offline_status_message: str = ""
    settings_status_message: str = ""
    settings_status_shown_at_ms: int | None = None
    end_session_pending: bool = False
    session_end_report_path: str = ""
    last_completed_world_id: str = ""
    last_points_awarded: int = 0
    current_round_wrong_count: int = 0
    voice_listen_pending: bool = False
    voice_listen_scheduled_at_ms: int = 0
    suppress_screen_speech_once: bool = False
    voice_pronunciation_feedback: str = ""
    voice_pronunciation_feedback_at_ms: int = 0
    voice_round_advance_pending: str = ""
    voice_round_advance_at_ms: int = 0
    voice_mic_prompt_at_ms: int = 0
    feedback_return_screen: str = ""
    answer_popup_kind: str = ""
    answer_popup_message: str = ""
    answer_popup_shown_at_ms: int = 0
    answer_popup_next_screen: str = ""
    answer_popup_refresh: bool = False
    answer_popup_preserve: bool = False
    writing_mode: str = "letters"
    writing_prompt: str = ""
    writing_result_text: str = ""
    writing_hint_text: str = ""
    writing_processing: bool = False
    writing_try_again_pending: bool = False
    app_loading: bool = False
    app_loading_message: str = ""
    app_loading_started_at: int = 0
