"""Main runtime loop and screen orchestration."""
from __future__ import annotations

import os

import pygame

from config import (
    DEBUG_HITBOXES,
    DEFAULT_WINDOW_CAPTION,
    END_SESSION_MESSAGE,
    LETTER_CORRECT_SPEECH,
    LETTER_VOICE_PROMPT,
    MICROPHONE_CHECK_DEFAULT_PROMPT,
    OFFLINE_WINDOW_CAPTION,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SETTINGS_DEV_ACTIONS,
    SETTINGS_STATUS_DISPLAY_MS,
    SPLASH_DURATION_MS,
    VOICE_ENABLED_DEFAULT,
    VOICE_FALLBACK_SCREEN_ID,
    WORLD_MAP_STATUS_DISPLAY_MS,
)
import csv
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from engine.control_assets import ControlAssets
from engine import audio_ducking
from engine.adaptive_ai import (
    choose_next_question,
    choose_hint,
    diagnose_letter_mistake,
    diagnose_word_mistake,
    note_curriculum_letter_completed,
    recommend_practice,
)
from engine.feedback import get_feedback, get_hint, get_letter_voice_character_hint, get_lumi_speech
from engine.hint_engine import get_hint_engine
from engine.game_state import GameState
from engine.learner_model import LearnerModel
from engine.microphone_check import run_microphone_check as execute_microphone_check
from engine.personal_tutor import (
    ALPHABET,
    advance_letter_curriculum,
    advance_word_length,
    build_letter_choices,
    build_letter_round,
)
from engine.offline_fallback import offline_prompt_text, resolve_offline_message
from engine.word_garden import (
    WORD_SLOT_COUNT,
    build_word_garden_round,
    build_word_garden_round_for_target,
    get_word_garden_pool,
)
from engine.world_progression import (
    WORLD_LETTER_ISLAND,
    WORLD_WORD_GARDEN,
    WORLD_WRITING_CASTLE,
    latest_completed_world,
    locked_world_message,
    maybe_complete_letter_island,
    maybe_complete_word_garden,
    prepare_world_practice,
    screen_accessible,
    sync_world_completion,
    word_garden_unlocked,
    world_map_progress_text,
)
from engine.writing_progression import (
    advance_writing_curriculum,
    build_writing_round,
    build_writing_round_for_mode,
    maybe_complete_writing_castle,
    writing_castle_progress_text,
)
from engine.screen_registry import ScreenRegistry
from engine.settings_manager import SettingsManager, difficulty_mode_to_level
from engine.sound_manager import SoundManager
from engine.voice_guard import is_stt_ready, safe_listen_once, stt_status_message
from engine.scoring import (
    badge_unlock_speech_message,
    calculate_stars,
    check_badge_unlocks,
    check_letter_island_complete_badge,
    check_letter_milestone_badges,
    update_score,
)
from engine.points import POINTS_PER_BADGE, POINTS_PER_WORLD, points_for_correct, rank_progress
from data_loader import load_letters, load_vocabulary
from engine.asset_manager import AssetManager
from reports.report_generator import generate_report, resolve_engine_screen_id
from ui.microphone_overlay import draw_microphone_check_overlay
from ui.offline_overlay import draw_offline_overlay
from ui.badge_overlay import draw_badge_unlock_overlay
from ui.voice_pronunciation_overlay import draw_voice_pronunciation_overlay
from ui.voice_mic_prompt_overlay import (
    MIC_HINT_MESSAGE,
    draw_mic_hint_badge,
    mic_hint_badge_rect,
    mic_hint_badge_x_inset,
    mic_hitbox_from_hitboxes,
)
from ui.answer_popup_overlay import LETTER_ISLAND_POPUP_ANCHOR_Y_PCT, draw_answer_popup_overlay
from ui.control_buttons_overlay import draw_control_button_placeholders
from ui.loading import draw_fullscreen_loading
from ui.screen_factory import IMAGE_ONLY_SCREEN_IDS_NO_CONTROL_OVERLAY
from ui.world_map_overlay import draw_world_map_overlay
from ui.screen_factory import create_game_screen
from ui.writing_castle_screen import WritingCastleScreen
from ui.writing_layout import (
    WRITING_BOARD_RECT,
    WRITING_BRUSH_RADIUS,
    WRITING_INK_COLOR,
)
from ui.scene_view import SceneView
from ui.chunk_preload import (
    EARLY_SCREEN_IDS,
    GAMEPLAY_REFERENCE_IMAGES,
    IDLE_PRELOAD_SCREEN_IDS,
    build_gameplay_chunk_queue,
    collect_chunk_files,
    preload_item_cost,
    warm_word_garden_draw_cache,
)
from ui.chunk_manifest import card_slot_offset_px, card_slot_rects, get_screen_spec, row_tile_slots
from ui.chunk_screen import ChunkScreen
from ui.hitboxes import Hitbox
from voice.text_to_speech import TextToSpeech
import voice.speech_to_text as speech_to_text
from voice.voice_checker import check_spoken_answer, guess_spoken_letter


LETTER_VOICE_QUESTION = "What letter is this?"
WORD_VOICE_QUESTION = "What is this?"
VOICE_LISTEN_DELAY_MS = 2500
VOICE_PRONUNCIATION_FEEDBACK_MS = 2400
VOICE_CORRECT_ADVANCE_DELAY_MS = 2400
VOICE_MIC_IDLE_SCREENS = frozenset({"letter_voice_challenge", "voice_challenge"})
LETTER_SLOT_COUNT = 4
ANSWER_POPUP_DURATION_MS = 1200
HINT_POPUP_DURATION_MS = 3200
LETTER_ISLAND_ENTRY_SCREENS = frozenset({"world_map", "main_menu", "how_to_play"})
WRITING_CASTLE_ENTRY_SCREENS = frozenset({"world_map", "main_menu", "how_to_play", "progress_complete", "badge_unlock"})
WORD_GARDEN_VISIBLE = get_word_garden_pool()
GAMEPLAY_HITBOX_SCREEN_IDS = frozenset({
    "letter_island_game",
    "word_garden_game",
})
SCREEN_SPECIFIC_PROMPT_ACTIONS = frozenset({
    "letter_island_game",
    "word_garden_game",
    "writing_castle_game",
})
LEGACY_WORD_ACTIONS = {
    "select_word_sun": "sun",
    "select_word_bird": "bird",
    "select_word_apple": "apple",
    "select_word_cup": "cup",
    "answer_sun_correct": "sun",
    "answer_bird_wrong": "bird",
    "answer_apple_wrong": "apple",
    "answer_cup_wrong": "cup",
}


@dataclass
class _WritingRecognitionJob:
    mode: str
    target: str
    recognized: str = ""
    hint: str = ""
    error: str | None = None
    unavailable_message: str | None = None


class GameEngine:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.asset_manager = AssetManager()
        self.control_assets = ControlAssets()
        self.registry = ScreenRegistry()
        self.settings = SettingsManager()
        self.sound = SoundManager()
        audio_ducking.bind(self.sound)
        self.voice = TextToSpeech(enabled=VOICE_ENABLED_DEFAULT)
        self.hint_engine = get_hint_engine()
        self.learner = LearnerModel()
        self._world_points_awarded: set[str] = set()
        self.state = GameState(splash_started_at=pygame.time.get_ticks())
        self._debug_enabled_since: int | None = None
        self._debug_duration_ms = 20_000
        self._word_questions: list | None = None
        self._letter_questions: list | None = None
        self._writing_canvas: pygame.Surface | None = None
        self._writing_draw_on = False
        self._writing_last_pos: tuple[int, int] | None = None
        self._writing_job_result: _WritingRecognitionJob | None = None
        self._writing_job_done = False
        self._writing_snapshot_path = Path(__file__).resolve().parents[1] / "writing_recognition" / ".writing_snapshot.png"
        self._apply_loaded_settings(self.settings.load_settings())
        self._log_voice_startup_status()
        self.screens = self._build_screens()
        self._static_warmed: set[str] = set()
        shipped = self.asset_manager.assets_shipped_ready("word_garden_game") or self.asset_manager.assets_shipped_ready(
            "letter_island_game"
        )
        if shipped and os.environ.get("LUMI_SKIP_PREWARM") != "1":
            self.asset_manager.prewarm_gameplay_assets()
            self._preload_queue: list[tuple[str, str]] = []
            self._image_preload_queue: list[str] = []
            for screen_id in (
                "profile_selection",
                "word_garden_game",
                "voice_challenge",
                "listening_state",
                "letter_voice_challenge",
                "letter_listening_state",
                "letter_island_game",
            ):
                self._warm_screen_static(screen_id)
        else:
            self._preload_queue = self._build_preload_queue()
            self._image_preload_queue = list(GAMEPLAY_REFERENCE_IMAGES)
        self.state.current_screen_id = self.registry.screen_ids[0]
        self.current_screen = self.screens[self.state.current_screen_id]

    def _build_screens(self) -> dict:
        screens: dict = {}
        for screen_id in self.registry.screen_ids:
            hitboxes = self._hitboxes_for_screen(screen_id)
            screen = create_game_screen(
                screen_id,
                hitboxes,
                self.registry,
                self.asset_manager,
                self._scene_view,
            )
            if screen_id == "writing_castle_game" and isinstance(screen, WritingCastleScreen):
                screen._draw_handler = self._handle_writing_draw_event
            screens[screen_id] = screen
        return screens

    def _build_preload_queue(self) -> list[tuple[str, str]]:
        queue: list[tuple[str, str]] = []
        for screen_id in EARLY_SCREEN_IDS:
            spec = get_screen_spec(screen_id, fallback_image=self.registry.get_image_filename(screen_id))
            for filename in collect_chunk_files(spec):
                queue.append((screen_id, filename))
        queue.extend(build_gameplay_chunk_queue())
        return queue

    def _warm_screen_static(self, screen_id: str) -> None:
        if screen_id in self._static_warmed:
            return
        screen = self.screens.get(screen_id)
        if not isinstance(screen, ChunkScreen):
            self._static_warmed.add(screen_id)
            return
        spec = get_screen_spec(screen_id, fallback_image=self.registry.get_image_filename(screen_id))
        screen._composer.warm_static(spec)
        self._static_warmed.add(screen_id)

    def _drain_preload_queue(self, *, budget: int = 6) -> None:
        remaining = budget
        if remaining > 0 and self._image_preload_queue:
            filename = self._image_preload_queue.pop(0)
            self.asset_manager.load_image(filename)
            remaining -= 1
        touched: set[str] = set()
        while remaining > 0 and self._preload_queue:
            screen_id, filename = self._preload_queue[0]
            cost = preload_item_cost(filename)
            if cost > remaining and touched:
                break
            self._preload_queue.pop(0)
            self.asset_manager.load_chunk(screen_id, filename)
            touched.add(screen_id)
            remaining -= cost
            if screen_id == "word_garden_game" and filename == "background.png":
                self._warm_screen_static("word_garden_game")
            if screen_id == "word_garden_game" and filename == "speak_background.png":
                self._warm_screen_static("voice_challenge")
                self._warm_screen_static("listening_state")
            if screen_id == "letter_island_game" and filename == "speak_background.png":
                self._warm_screen_static("letter_voice_challenge")
                self._warm_screen_static("letter_listening_state")
            if screen_id == "word_garden_game" and filename.startswith("objects/"):
                word = Path(filename).stem
                warm_word_garden_draw_cache(self.asset_manager, word)
        for screen_id in touched:
            if not self._preload_queue or not any(item[0] == screen_id for item in self._preload_queue):
                self._warm_screen_static(screen_id)

    def _settings_status_text(self) -> str:
        if not self.state.settings_status_message or self.state.settings_status_shown_at_ms is None:
            return ""
        elapsed = pygame.time.get_ticks() - int(self.state.settings_status_shown_at_ms)
        if elapsed <= SETTINGS_STATUS_DISPLAY_MS:
            return self.state.settings_status_message
        self.state.settings_status_message = ""
        self.state.settings_status_shown_at_ms = None
        return ""

    def _world_map_status_text(self) -> str:
        if not self.state.world_map_status_message or self.state.world_map_status_shown_at_ms is None:
            return ""
        elapsed = pygame.time.get_ticks() - int(self.state.world_map_status_shown_at_ms)
        if elapsed <= WORLD_MAP_STATUS_DISPLAY_MS:
            return self.state.world_map_status_message
        self.state.world_map_status_message = ""
        self.state.world_map_status_shown_at_ms = None
        return ""

    def _show_world_map_status(self, message: str) -> None:
        self.state.world_map_status_message = message
        self.state.world_map_status_shown_at_ms = pygame.time.get_ticks()

    def _show_world_locked_feedback(self, screen_id: str) -> None:
        message = locked_world_message(screen_id)
        self._show_world_map_status(message)
        if self.state.voice_enabled:
            self.voice.speak(message)

    def _mark_world_completed(self, world_id: str) -> None:
        key = str(world_id or "").strip()
        if key:
            self.state.last_completed_world_id = key
            self._award_world_points(key)

    def _start_practice_for_completed_world(self) -> None:
        world_id = str(
            self.state.last_completed_world_id or latest_completed_world(self.learner)
        ).strip()
        if not world_id:
            world_id = WORLD_LETTER_ISLAND
        screen_id = prepare_world_practice(self.learner, world_id)
        self.state.pending_letter_curriculum_advance = False
        self.state.preserve_letter_island_task = False
        self.state.preserve_word_garden_task = False
        self.state.letter_review_mode = False
        self.state.completed_letter_target = ""
        self.state.completed_letter_choices = []
        self.state.gameplay_refresh_pending = True
        self.set_screen(screen_id)
        if self.state.voice_enabled:
            self.voice.speak("Let's practice this world again!")

    def _notify_world_unlocked(self, world_id: str) -> None:
        messages = {
            WORLD_WORD_GARDEN: "Word Garden unlocked!",
            WORLD_WRITING_CASTLE: "Writing Castle unlocked!",
        }
        message = messages.get(world_id, "New world unlocked!")
        self._show_world_map_status(message)
        if self.state.voice_enabled:
            self.voice.speak(message)

    def _notify_parallel_worlds_unlocked(self) -> None:
        message = "Word Garden and Writing Castle unlocked!"
        self._show_world_map_status(message)
        if self.state.voice_enabled:
            self.voice.speak(message)

    def _practice_card_labels(self) -> tuple[str, ...]:
        return (
            "Practice B",
            "Practice D",
            "Practice Word Cat",
        )

    def _progress_text_for_screen(self, screen_id: str) -> str:
        if screen_id == "progress_complete":
            return "Great work today!"
        if screen_id == "world_map":
            return world_map_progress_text(self.learner)
        if screen_id.startswith("letter") or screen_id == "bd_practice":
            return self._letter_progress_text()
        if screen_id.startswith("word"):
            return self._word_progress_text()
        if screen_id == "writing_castle_game":
            return writing_castle_progress_text(self.learner)
        return ""

    def _scene_view(self) -> SceneView:
        screen_id = self.state.current_screen_id
        stars = min(3, max(0, int(getattr(self.state, "stars", 0) or 0)))
        child_name = str(getattr(self.learner, "child_name", None) or "Player 1")
        energy = int(getattr(self.learner, "lumi_energy", 100) or 100)
        loading_progress = 0.66
        if screen_id == "splash_loading":
            elapsed = pygame.time.get_ticks() - int(self.state.splash_started_at or 0)
            loading_progress = min(1.0, max(0.05, elapsed / max(1, SPLASH_DURATION_MS)))

        feedback_message = ""
        if screen_id == "end_session":
            feedback_message = END_SESSION_MESSAGE

        target_letter = str(self.state.current_task_target or "A").upper()
        if screen_id == "bd_practice":
            target_letter = str(self.state.bd_practice_target or target_letter or "B").upper()

        slot_letters = tuple(str(letter).upper() for letter in self.state.letter_choice_slots[:4])
        highlight_letter_slot = int(getattr(self.state, "highlight_letter_slot", -1) or -1)
        letter_success_slot = -1
        letter_success_progress = 0.0
        if screen_id == "letter_island_game":
            highlight_letter_slot = -1
            if self.state.answer_popup_kind == "correct":
                target = str(self.state.current_task_target or "").upper()
                for idx, letter in enumerate(self.state.letter_choice_slots[:4]):
                    if str(letter).upper() == target:
                        letter_success_slot = idx
                        break
                elapsed = pygame.time.get_ticks() - int(self.state.answer_popup_shown_at_ms or 0)
                letter_success_progress = min(
                    1.0,
                    max(0.0, elapsed / max(1, ANSWER_POPUP_DURATION_MS)),
                )

        voice_target = self._voice_challenge_target()
        if screen_id in {"letter_voice_challenge", "letter_listening_state"}:
            voice_target = self._letter_voice_target().lower()
        elif screen_id not in {"voice_challenge", "listening_state"}:
            voice_target = str(self.state.current_task_target or "sun").lower()

        teacher_report = dict(self.state.teacher_report or {})
        if screen_id == "teacher_report" and not teacher_report:
            teacher_report = generate_report(self.learner.get_profile())

        total_points = int(getattr(self.learner, "total_points", 0) or 0)
        progress = rank_progress(total_points)

        return SceneView(
            screen_id=screen_id,
            child_name=child_name,
            lumi_energy=energy,
            lumi_energy_max=100,
            stars_filled=stars,
            total_stars=int(getattr(self.learner, "total_stars", 0) or 0),
            progress_text=self._progress_text_for_screen(screen_id),
            target_letter=target_letter,
            slot_letters=slot_letters,
            held_letter=target_letter,
            target_word=str(self.state.current_task_target or "sun").lower(),
            slot_words=tuple(str(word).lower() for word in self.state.word_choice_slots[:4]),
            voice_target=voice_target,
            voice_listening=screen_id in {"listening_state", "letter_listening_state"},
            feedback_message=feedback_message,
            music_enabled=bool(self.state.music_enabled),
            voice_enabled=bool(self.state.voice_enabled),
            difficulty_mode=self._current_difficulty_mode(),
            settings_status=self._settings_status_text(),
            teacher_report=teacher_report,
            offline_message=str(self.state.offline_status_message or offline_prompt_text("")),
            microphone_status=str(
                self.state.microphone_status_message or MICROPHONE_CHECK_DEFAULT_PROMPT
            ),
            practice_cards=self._practice_card_labels(),
            badge_names=tuple(str(name) for name in (self.state.last_unlocked_badges or [])),
            loading_progress=loading_progress,
            highlight_letter_slot=highlight_letter_slot,
            letter_success_slot=letter_success_slot,
            letter_success_progress=letter_success_progress,
            total_points=total_points,
            points_rank=str(progress["rank_name"]),
            points_emoji=str(progress["rank_emoji"]),
            points_progress=float(progress["progress"]),
            points_to_next=int(progress["points_to_next"]),
            next_rank_name=str(progress["next_rank_name"]),
            best_streak=int(getattr(self.learner, "best_streak", 0) or 0),
            current_streak=int(getattr(self.learner, "correct_streak", 0) or 0),
            badges_count=len(list(getattr(self.learner, "badges", []) or [])),
            last_points_awarded=int(self.state.last_points_awarded or 0),
            writing_mode=str(self.state.writing_mode or "letters"),
            writing_prompt=str(self.state.writing_prompt or self.state.current_task_prompt or ""),
            writing_result_text=str(self.state.writing_result_text or ""),
            writing_hint_text=str(self.state.writing_hint_text or ""),
            writing_canvas=self._writing_canvas,
            writing_loading=bool(self.state.writing_processing),
            app_loading_started_at=int(self.state.app_loading_started_at or 0),
        )

    @property
    def word_questions(self) -> list:
        if self._word_questions is None:
            self._word_questions = load_vocabulary()
        return self._word_questions

    @property
    def letter_questions(self) -> list:
        if self._letter_questions is None:
            self._letter_questions = load_letters()
        return self._letter_questions

    def _hitboxes_for_screen(self, screen_id: str):
        hitboxes = list(self.registry.get_hitboxes(screen_id))
        if screen_id == "letter_island_game":
            hitboxes = [box for box in hitboxes if not box.action.startswith("select_letter_slot_")]
            spec = get_screen_spec(screen_id, fallback_image=self.registry.get_image_filename(screen_id))
            cards = spec.dynamic.get("letter_cards") or {}
            if isinstance(cards, dict):
                for index, (x, y, w, h) in enumerate(row_tile_slots(cards)):
                    hitboxes.append(
                        Hitbox(
                            name=f"Letter slot {index + 1}",
                            rect=pygame.Rect(x, y, w, h),
                            action=f"select_letter_slot_{index}",
                        )
                    )
        if screen_id == "word_garden_game":
            hitboxes = [box for box in hitboxes if not box.action.startswith("select_word_slot_")]
            spec = get_screen_spec(screen_id, fallback_image=self.registry.get_image_filename(screen_id))
            cards = spec.dynamic.get("word_cards") or {}
            if isinstance(cards, dict):
                for index, (x, y, w, h) in enumerate(card_slot_rects(cards)):
                    hitboxes.append(
                        Hitbox(
                            name=f"Word slot {index + 1}",
                            rect=pygame.Rect(x, y, w, h),
                            action=f"select_word_slot_{index}",
                        )
                    )
        if screen_id != "settings":
            return hitboxes
        if DEBUG_HITBOXES or bool(self.settings.load_settings().get("debug_hitboxes")):
            return hitboxes
        return [hitbox for hitbox in hitboxes if hitbox.action not in SETTINGS_DEV_ACTIONS]

    def _current_difficulty_mode(self) -> str:
        return str(self.settings.load_settings().get("difficulty_mode", "Medium"))

    def _apply_loaded_settings(self, settings: dict) -> None:
        self.state.music_enabled = bool(settings.get("music_enabled", True))
        self.state.voice_enabled = bool(settings.get("voice_enabled", VOICE_ENABLED_DEFAULT))
        difficulty_level = difficulty_mode_to_level(str(settings.get("difficulty_mode", "Medium")))
        self.state.difficulty = difficulty_level
        self.learner.difficulty = difficulty_level
        self.learner.save_profile()
        sync_world_completion(self.learner)
        self.voice.set_enabled(self.state.voice_enabled)
        self.sound.set_enabled(self.state.music_enabled)
        self.debug_hitboxes = bool(DEBUG_HITBOXES or settings.get("debug_hitboxes", False))

    def _show_settings_status(self, message: str) -> None:
        self.state.settings_status_message = message
        self.state.settings_status_shown_at_ms = pygame.time.get_ticks()

    def _log_voice_startup_status(self) -> None:
        status_message = speech_to_text.get_status_message()
        backend = "not_ready"
        if "Vosk offline" in status_message:
            backend = "vosk_offline"
        elif "SpeechRecognition" in status_message:
            backend = "speech_recognition"
        print(
            f"[Lumi Voice] tts_enabled={self.state.voice_enabled} "
            f"stt_available={speech_to_text.is_available()} backend={backend} status='{status_message}'"
        )

    def _refresh_screen_hitboxes(self, screen_id: str) -> None:
        """Reload hitboxes for a screen (keeps layout in sync with the PNG)."""
        screen = self.screens.get(screen_id)
        if screen is None or not hasattr(screen, "hitboxes"):
            return
        screen.hitboxes = self._hitboxes_for_screen(screen_id)

    def change_screen(self, screen_id: str) -> None:
        if screen_id in {"world_map", "progress_complete", "word_garden_game", "writing_castle_game"}:
            sync_world_completion(self.learner)
        if not screen_accessible(self.learner, screen_id):
            self._show_world_locked_feedback(screen_id)
            return
        if screen_id in self.screens:
            previous_screen_id = self.state.current_screen_id
            if screen_id == "word_garden_game":
                if self.state.preserve_word_garden_task:
                    self.state.preserve_word_garden_task = False
                else:
                    self._configure_word_garden_task()
                if self.state.gameplay_refresh_pending:
                    self.state.gameplay_refresh_pending = False
            if screen_id in GAMEPLAY_HITBOX_SCREEN_IDS:
                self._refresh_screen_hitboxes(screen_id)
            if screen_id == "letter_island_game":
                if self.state.preserve_letter_island_task:
                    self.state.preserve_letter_island_task = False
                elif (
                    self.state.gameplay_refresh_pending
                    or previous_screen_id in LETTER_ISLAND_ENTRY_SCREENS
                    or previous_screen_id == "settings"
                    or not str(self.state.current_task_target or "").strip()
                    or " " in str(self.state.current_task_target or "")
                ):
                    self._configure_letter_island_task()
                    self.state.gameplay_refresh_pending = False
            if screen_id == "microphone_check":
                self.state.microphone_status_message = ""
                self.state.microphone_test_mode = False
                self.state.microphone_return_screen = "settings"
            if screen_id == VOICE_FALLBACK_SCREEN_ID:
                pygame.display.set_caption(OFFLINE_WINDOW_CAPTION)
            elif previous_screen_id == VOICE_FALLBACK_SCREEN_ID:
                pygame.display.set_caption(DEFAULT_WINDOW_CAPTION)
            if screen_id == "practice_weak_skills":
                # get adaptive recommendation and present supportive practice options
                try:
                    rec = recommend_practice(self.learner)
                except Exception:
                    rec = {}
                self.state.practice_recommendation = rec
                # supportive speech
                self.voice.speak("Here are some gentle practice ideas. Choose one you like.")
            if screen_id == "teacher_report":
                self._configure_teacher_report()
            if screen_id == "end_session":
                self._configure_end_session()
            if screen_id == "listening_state" and previous_screen_id == "microphone_check":
                screen_id = self._run_microphone_check()
            if screen_id == "world_map":
                sync_world_completion(self.learner)
            if screen_id == "writing_castle_game":
                if self.state.preserve_writing_castle_task:
                    self.state.preserve_writing_castle_task = False
                elif (
                    self.state.gameplay_refresh_pending
                    or previous_screen_id in WRITING_CASTLE_ENTRY_SCREENS
                    or not str(self.state.writing_prompt or "").strip()
                ):
                    self._configure_writing_castle_task()
                    self.state.gameplay_refresh_pending = False
                else:
                    self._ensure_writing_canvas()
                self._warm_writing_recognition()
            if screen_id == "progress_complete":
                sync_world_completion(self.learner)
                if not self.state.last_completed_world_id:
                    self.state.last_completed_world_id = latest_completed_world(self.learner)
                self._refresh_screen_hitboxes("progress_complete")
            if screen_id == "settings":
                self._refresh_screen_hitboxes("settings")
            if screen_id == "badge_unlock":
                self._refresh_screen_hitboxes("badge_unlock")
            if previous_screen_id == "welcome" and screen_id != "welcome":
                self.sound.allow_background_playback()
            self.state.current_screen_id = screen_id
            self.current_screen = self.screens[screen_id]
            self.state.history.append(screen_id)
            if self.state.suppress_screen_speech_once:
                self.state.suppress_screen_speech_once = False
            else:
                self._speak_for_screen(screen_id)
            if screen_id in {"letter_voice_challenge", "voice_challenge"}:
                self.state.voice_mic_prompt_at_ms = pygame.time.get_ticks()
                self._schedule_auto_voice_listen()

    def _should_show_voice_mic_prompt(self) -> bool:
        if self.state.current_screen_id not in VOICE_MIC_IDLE_SCREENS:
            return False
        if not is_stt_ready():
            return False
        if str(self.state.voice_pronunciation_feedback or "").strip():
            return False
        if str(self.state.voice_round_advance_pending or "").strip():
            return False
        return True

    def _handle_mic_hint_badge_click(self, position: tuple[int, int]) -> bool:
        if not self._should_show_voice_mic_prompt():
            return False
        mic_rect = mic_hitbox_from_hitboxes(list(getattr(self.current_screen, "hitboxes", []) or []))
        if mic_rect is None:
            return False
        if mic_hint_badge_rect(mic_rect, x_inset=mic_hint_badge_x_inset(self.state.current_screen_id)).collidepoint(position):
            self.voice.speak(MIC_HINT_MESSAGE, tone="instruct")
            return True
        return False

    def _schedule_auto_voice_listen(self) -> None:
        if not is_stt_ready():
            return
        if self.state.voice_pronunciation_feedback or self.state.voice_round_advance_pending:
            return
        self.state.voice_listen_pending = True
        self.state.voice_listen_scheduled_at_ms = pygame.time.get_ticks() + VOICE_LISTEN_DELAY_MS

    def _show_voice_pronunciation_feedback(self, kind: str) -> None:
        cleaned = str(kind or "").strip().lower()
        if cleaned not in {"correct", "try_again"}:
            return
        self.state.voice_pronunciation_feedback = cleaned
        self.state.voice_pronunciation_feedback_at_ms = pygame.time.get_ticks()
        self.state.voice_listen_pending = False

    def _clear_voice_pronunciation_feedback(self) -> None:
        self.state.voice_pronunciation_feedback = ""
        self.state.voice_pronunciation_feedback_at_ms = 0

    def _schedule_voice_correct_advance(self, activity: str) -> None:
        self.state.voice_round_advance_pending = str(activity or "").strip().lower()
        self.state.voice_round_advance_at_ms = pygame.time.get_ticks() + VOICE_CORRECT_ADVANCE_DELAY_MS
        self.state.voice_listen_pending = False

    def _maybe_complete_voice_correct_advance(self) -> None:
        pending = str(self.state.voice_round_advance_pending or "").strip().lower()
        if not pending:
            return
        if pygame.time.get_ticks() < int(self.state.voice_round_advance_at_ms or 0):
            return
        self.state.voice_round_advance_pending = ""
        self._clear_voice_pronunciation_feedback()
        if pending == "letter":
            self._advance_to_next_letter_voice_round()
        elif pending == "word":
            self._advance_to_next_word_voice_round()

    def _update_voice_pronunciation_feedback(self) -> None:
        feedback = str(self.state.voice_pronunciation_feedback or "").strip().lower()
        if not feedback:
            return
        elapsed = pygame.time.get_ticks() - int(self.state.voice_pronunciation_feedback_at_ms or 0)
        if elapsed <= VOICE_PRONUNCIATION_FEEDBACK_MS:
            return
        if self.state.voice_round_advance_pending:
            return
        self._clear_voice_pronunciation_feedback()
        if self.state.current_screen_id in VOICE_MIC_IDLE_SCREENS:
            self.state.voice_mic_prompt_at_ms = pygame.time.get_ticks()
            if is_stt_ready():
                self._schedule_auto_voice_listen()

    def _maybe_start_scheduled_voice_listen(self) -> None:
        if not self.state.voice_listen_pending:
            return
        if pygame.time.get_ticks() < int(self.state.voice_listen_scheduled_at_ms or 0):
            return
        self.state.voice_listen_pending = False
        if self.state.current_screen_id == "letter_voice_challenge":
            self._start_letter_voice_listening()
        elif self.state.current_screen_id == "voice_challenge":
            self._start_voice_listening()

    def _toggle_debug_hitboxes(self) -> None:
        """Toggle runtime hitbox debug overlay for temporary visual alignment aid."""
        self.debug_hitboxes = not bool(self.debug_hitboxes)
        if self.debug_hitboxes:
            self._debug_enabled_since = pygame.time.get_ticks()
            print("[DEBUG] Hitbox overlay ON")
            if self.state.voice_enabled:
                self.voice.speak("Hitbox debug on")
        else:
            self._debug_enabled_since = None
            print("[DEBUG] Hitbox overlay OFF")
            if self.state.voice_enabled:
                self.voice.speak("Hitbox debug off")

    def _toggle_debug_persistent(self) -> None:
        """Toggle persistent debug overlay state stored in GameState (for dev sessions)."""
        self.state.debug_persistent = not bool(self.state.debug_persistent)
        if self.state.debug_persistent:
            # ensure overlay shows
            self.debug_hitboxes = True
            self._debug_enabled_since = None
            print("[DEBUG] Persistent hitbox overlay ENABLED")
            if self.state.voice_enabled:
                self.voice.speak("Persistent hitbox overlay enabled")
        else:
            self.debug_hitboxes = False
            self._debug_enabled_since = None
            print("[DEBUG] Persistent hitbox overlay DISABLED")
            if self.state.voice_enabled:
                self.voice.speak("Persistent hitbox overlay disabled")

    def _show_offline_fallback(self, reason: str | None = None) -> None:
        message = resolve_offline_message(reason)
        self.state.offline_status_message = offline_prompt_text(message)
        self.state.microphone_status_message = message
        self.state.microphone_test_mode = False
        print(f"[Lumi Offline] {self.state.offline_status_message}")
        self.set_screen(VOICE_FALLBACK_SCREEN_ID)

    def _begin_voice_challenge(self) -> None:
        self._configure_voice_challenge_task()
        if not is_stt_ready():
            print(f"[Lumi Voice] {stt_status_message()}")
            self._show_offline_fallback(stt_status_message())
            return
        self.set_screen("voice_challenge")

    def _begin_letter_voice_challenge(self) -> None:
        self._configure_letter_voice_task()
        if not is_stt_ready():
            print(f"[Lumi Voice] {stt_status_message()}")
        self.set_screen("letter_voice_challenge")

    def _start_voice_listening(self) -> None:
        self.state.voice_listen_pending = False
        self._configure_voice_challenge_task()
        if not is_stt_ready():
            print(f"[Lumi Voice] {stt_status_message()}")
            self._show_offline_fallback(stt_status_message())
            return
        self.state.suppress_screen_speech_once = True
        self.set_screen("listening_state")
        spoken = safe_listen_once(timeout=7)
        self._process_voice_capture_result(spoken)

    def _start_letter_voice_listening(self) -> None:
        self.state.voice_listen_pending = False
        self._configure_letter_voice_task()
        if not is_stt_ready():
            message = stt_status_message()
            print(f"[Lumi Voice] {message}")
            self.state.microphone_status_message = message
            if self.state.voice_enabled:
                self.voice.speak(message)
            self.set_screen("letter_voice_challenge")
            return
        self.state.suppress_screen_speech_once = True
        self.set_screen("letter_listening_state")
        spoken = safe_listen_once(timeout=7)
        self._process_letter_voice_capture_result(spoken)

    def _run_microphone_check(self) -> str:
        """Run a short microphone readiness test from the microphone check screen."""
        self.state.microphone_test_mode = True
        self.state.microphone_return_screen = "settings"
        result = execute_microphone_check()
        self.state.microphone_status_message = str(result.get("status_message", MICROPHONE_CHECK_DEFAULT_PROMPT))
        next_screen = str(result.get("next_screen_id", VOICE_FALLBACK_SCREEN_ID))

        if not result.get("available"):
            self.state.microphone_test_mode = False
            message = str(result.get("status_message", ""))
            self.state.offline_status_message = offline_prompt_text(message)
            self.state.microphone_status_message = message
            print(f"[Lumi Offline] {self.state.offline_status_message}")
            if self.state.voice_enabled:
                self.voice.speak(message or get_lumi_speech(VOICE_FALLBACK_SCREEN_ID))
            return next_screen

        if self.state.voice_enabled:
            self.voice.speak(self.state.microphone_status_message)
        return next_screen

    def _finish_microphone_test(self) -> None:
        return_screen = self.state.microphone_return_screen or "settings"
        self.state.microphone_test_mode = False
        self.set_screen(return_screen)

    def _export_hitboxes_to_csv(self) -> str:
        """Export current hitbox definitions to a CSV under ./diagnostics/ and return file path."""
        try:
            out_dir = os.path.join(os.getcwd(), "diagnostics")
            os.makedirs(out_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hitboxes_{ts}.csv"
            path = os.path.join(out_dir, filename)
            with open(path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    "screen_id",
                    "image",
                    "hitbox_name",
                    "x_pct",
                    "y_pct",
                    "w_pct",
                    "h_pct",
                    "x_px",
                    "y_px",
                    "w_px",
                    "h_px",
                    "action",
                    "target",
                ])
                width, height = (1280, 720)
                for definition in self.registry._definitions:
                    image = definition.image_filename
                    sid = definition.screen_id
                    for hb in definition.hitboxes:
                        x_px = round(width * hb.x_pct)
                        y_px = round(height * hb.y_pct)
                        w_px = round(width * hb.w_pct)
                        h_px = round(height * hb.h_pct)
                        writer.writerow([
                            sid,
                            image,
                            hb.name,
                            hb.x_pct,
                            hb.y_pct,
                            hb.w_pct,
                            hb.h_pct,
                            x_px,
                            y_px,
                            w_px,
                            h_px,
                            hb.action,
                            hb.target,
                        ])
            print(f"[DEBUG] Hitboxes exported to {path}")
            if self.state.voice_enabled:
                self.voice.speak(f"Exported hitboxes to diagnostics")
            # record in state so UI can show dialog
            try:
                self.state.last_export_path = path
                self.state.last_export_time_ms = pygame.time.get_ticks()
            except Exception:
                pass
            return path
        except Exception as exc:
            print(f"[DEBUG] Failed to export hitboxes: {exc}")
            if self.state.voice_enabled:
                self.voice.speak("Failed to export hitboxes")
            return ""

    def _play_feedback_sfx(self, result: str, *, stars_earned: int = 0) -> None:
        if result == "badge":
            self.sound.play_sfx("badge")
        elif result == "correct":
            self.sound.play_sfx("star" if stars_earned >= 3 else "correct")
        elif result == "wrong":
            self.sound.play_sfx("wrong")

    def _award_answer_points(self, stars_earned: int) -> int:
        """Award points for a correct answer using the current streak."""
        streak = int(getattr(self.learner, "correct_streak", 0) or 0)
        earned = points_for_correct(stars_earned, streak)
        self.learner.add_points(earned)
        self.learner.note_best_streak(streak)
        self.state.last_points_awarded = earned
        return earned

    def _award_world_points(self, world_id: str) -> None:
        key = str(world_id or "").strip()
        if not key:
            return
        if key in self._world_points_awarded:
            return
        self._world_points_awarded.add(key)
        self.learner.add_points(POINTS_PER_WORLD)

    def _show_answer_popup(
        self,
        kind: str,
        message: str,
        *,
        next_screen: str,
        refresh: bool = False,
        preserve: bool = False,
        sfx: str = "",
        stars_earned: int = 0,
        speech: str | None = None,
    ) -> None:
        """Show an in-place Correct/Try again popup that auto-dismisses, then continues."""
        self.state.answer_popup_kind = kind
        self.state.answer_popup_message = str(message or "").strip()
        self.state.answer_popup_shown_at_ms = pygame.time.get_ticks()
        self.state.answer_popup_next_screen = str(next_screen or "")
        self.state.answer_popup_refresh = bool(refresh)
        self.state.answer_popup_preserve = bool(preserve)
        if sfx:
            self._play_feedback_sfx(sfx, stars_earned=stars_earned)
        popup_tone = "celebrate" if kind == "correct" else "soothe"
        spoken = self.state.answer_popup_message if speech is None else str(speech).strip()
        self._speak_tutor_line(spoken, tone=popup_tone)

    def _show_hint_popup(self, message: str) -> None:
        """Show a non-blocking on-screen hint banner and speak it warmly."""
        msg = str(message or "").strip()
        if not msg:
            return
        self.state.answer_popup_kind = "hint"
        self.state.answer_popup_message = msg
        self.state.answer_popup_shown_at_ms = pygame.time.get_ticks()
        self.state.answer_popup_next_screen = ""
        self.state.answer_popup_refresh = False
        self.state.answer_popup_preserve = False
        self._speak_tutor_line(msg, tone="encourage")

    def _resolve_answer_popup(self) -> None:
        next_screen = self.state.answer_popup_next_screen
        refresh = self.state.answer_popup_refresh
        preserve = self.state.answer_popup_preserve
        self.state.answer_popup_kind = ""
        self.state.answer_popup_message = ""
        self.state.answer_popup_shown_at_ms = 0
        self.state.answer_popup_next_screen = ""
        self.state.answer_popup_refresh = False
        self.state.answer_popup_preserve = False
        if not next_screen:
            return
        if refresh:
            self.state.gameplay_refresh_pending = True
        if preserve:
            if next_screen == "letter_island_game":
                self.state.preserve_letter_island_task = True
            elif next_screen == "word_garden_game":
                self.state.preserve_word_garden_task = True
            elif next_screen == "writing_castle_game":
                self.state.preserve_writing_castle_task = True
        self.set_screen(next_screen)

    def _show_letter_mistake_feedback(self, message: str, *, return_screen: str = "letter_island_game") -> None:
        msg = str(message or "").strip() or "Good try. You can do it!"
        self.state.last_letter_feedback_message = msg
        self._show_answer_popup(
            "wrong",
            msg,
            next_screen=str(return_screen or "letter_island_game"),
            preserve=True,
            sfx="wrong",
        )

    def _show_word_mistake_feedback(self, message: str, *, return_screen: str = "word_garden_game") -> None:
        msg = str(message or "").strip() or "Good try. Listen and try again."
        self.state.last_word_feedback_message = msg
        self._show_answer_popup(
            "wrong",
            msg,
            next_screen=str(return_screen or "word_garden_game"),
            preserve=True,
            sfx="wrong",
        )

    def _show_letter_correct_feedback(self, message: str, *, stars_earned: int = 0) -> None:
        custom = str(message or "").strip()
        if custom:
            spoken = custom
            display = custom
        else:
            spoken = LETTER_CORRECT_SPEECH
            display = ""
        self.state.last_letter_feedback_message = spoken
        self._show_answer_popup(
            "correct",
            display,
            next_screen="letter_island_game",
            refresh=True,
            sfx="correct",
            stars_earned=stars_earned,
            speech=spoken,
        )

    def _show_word_correct_feedback(self, message: str, *, stars_earned: int = 0) -> None:
        msg = str(message or "").strip() or self._word_garden_correct_message()
        self.state.last_word_feedback_message = msg
        self._show_answer_popup(
            "correct",
            msg,
            next_screen="word_garden_game",
            refresh=True,
            sfx="correct",
            stars_earned=stars_earned,
        )

    def _speak_tutor_line(self, text: str, tone: str = "neutral") -> None:
        cleaned = str(text or "").strip()
        if not cleaned or not self.state.voice_enabled:
            return
        self.voice.clear_pending()
        self.voice.speak(cleaned, tone=tone)

    def _letter_progress_text(self) -> str:
        index = int(getattr(self.learner, "current_letter_index", 0) or 0)
        index = max(0, min(index, len(ALPHABET) - 1))
        letter = ALPHABET[index]
        return f"Letter journey: learning {letter} ({index + 1}/26)"

    def _word_progress_text(self) -> str:
        length = int(getattr(self.learner, "current_word_length", 3) or 3)
        mastered = len(self.learner.mastered_words or [])
        return f"Word garden: {length}-letter words · {mastered} mastered"

    def _resolve_letter_from_action(self, action: str) -> str | None:
        if action.startswith("select_letter_slot_"):
            try:
                slot_index = int(action.rsplit("_", 1)[-1])
            except ValueError:
                return None
            if 0 <= slot_index < len(self.state.letter_choice_slots):
                return self.state.letter_choice_slots[slot_index].upper()
        legacy = {
            "select_letter_a": "A",
            "select_letter_b": "B",
            "select_letter_d": "D",
            "select_letter_p": "P",
        }
        return legacy.get(action)

    def _slot_index_for_letter(self, letter: str) -> int | None:
        target = letter.strip().upper()
        for index, slot_letter in enumerate(self.state.letter_choice_slots):
            if str(slot_letter).upper() == target:
                return index
        return None

    def _target_word_slot_index(self) -> int | None:
        target = str(self.state.current_task_target or "").strip().lower()
        if not target:
            return None
        for index, word in enumerate(self.state.word_choice_slots):
            if str(word).strip().lower() == target:
                return index
        return None

    def _resolve_word_from_action(self, action: str) -> str | None:
        if action.startswith("select_word_slot_"):
            try:
                slot_index = int(action.rsplit("_", 1)[-1])
            except ValueError:
                return None
            if 0 <= slot_index < len(self.state.word_choice_slots):
                return self.state.word_choice_slots[slot_index].lower()
        return LEGACY_WORD_ACTIONS.get(action)

    def _word_garden_pool(self) -> tuple[str, ...]:
        return get_word_garden_pool()

    def _pick_visible_word(self, preferred: str, fallback: str = "sun") -> str:
        pool = self._word_garden_pool()
        cleaned = preferred.strip().lower()
        if cleaned in pool:
            return cleaned
        if fallback in pool:
            return fallback
        return pool[0] if pool else "sun"

    def _build_word_garden_round(self) -> dict:
        last_target = str(
            self.state.last_word_garden_target
            or getattr(self.learner, "last_word_garden_target", "")
            or ""
        ).strip().lower()
        return build_word_garden_round(
            self.learner,
            pool=self._word_garden_pool(),
            vocabulary_data=self.word_questions,
            last_target=last_target,
        )

    def _apply_letter_round(self, target: str, choices: list[str]) -> None:
        letter = str(target or "A").upper()
        slots = [str(item).upper() for item in choices[:LETTER_SLOT_COUNT]]
        if letter not in slots:
            slots = [str(item).upper() for item in build_letter_choices(letter, self.letter_questions)[:LETTER_SLOT_COUNT]]
        self.state.current_task_target = letter
        self.state.letter_choice_slots = slots

    def _configure_letter_island_task(self) -> None:
        if self.state.pending_letter_curriculum_advance:
            mastered_letter = str(self.state.current_task_target or "A").upper()
            advance_letter_curriculum(self.learner, mastered=True, letter=mastered_letter)
            self.state.pending_letter_curriculum_advance = False

        round_data = build_letter_round(self.learner, self.letter_questions)
        letter = str(round_data.get("target") or "A").upper()
        choices = build_letter_choices(letter, self.letter_questions)
        self.state.current_task_prompt = str(round_data.get("prompt") or f"Find the letter {letter}.")
        self._apply_letter_round(letter, choices)
        self.state.letter_review_mode = bool(round_data.get("review_mode"))
        self.state.current_hint_level = 0
        self.state.last_mistake_type = ""
        self.state.bd_confusion_attempts = 0
        self.state.bd_practice_target = ""
        self.state.bd_practice_step = 0
        self.state.highlight_letter_slot = -1
        self.state.last_selected_letter = ""
        self.state.completed_letter_target = ""
        self.state.completed_letter_choices = []
        self.state.current_round_wrong_count = 0
        self._warm_letter_round_assets(letter, choices)

    def _warm_letter_round_assets(self, target: str, choices: list[str]) -> None:
        asset_root = "letter_island_game"
        tile_w = int(1280 * 0.11)
        tile_h = int(720 * 0.22)
        find_w = int(1280 * 0.34)
        find_h = int(720 * 0.1)
        letters = {str(target).upper()}
        letters.update(str(item).upper() for item in choices[:LETTER_SLOT_COUNT])
        for letter in letters:
            self.asset_manager.scaled_find_prompt(asset_root, letter, find_w, find_h)
            self.asset_manager.scaled_letter_tile(asset_root, letter, tile_w, tile_h, selected=False)
            self.asset_manager.scaled_letter_tile(
                asset_root,
                letter,
                tile_w,
                tile_h,
                selected=True,
                selected_scale=1.22,
            )

    def _configure_bd_practice(self, target_letter: str = "B") -> None:
        self.state.bd_practice_target = target_letter
        self.state.bd_practice_step = 0 if target_letter == "B" else 1
        self.state.current_task_target = target_letter
        self.state.current_task_prompt = f"Find the letter {target_letter}."
        self.state.current_hint_level = 0

    def _apply_word_garden_round(self, round_data: dict) -> None:
        """Keep voice, prompt text, and card images on the same target word."""
        pool = self._word_garden_pool()
        target_word = str(round_data.get("target") or "sun").strip().lower()
        if target_word not in pool:
            target_word = pool[0] if pool else "sun"
        choices = [
            str(word).strip().lower()
            for word in round_data.get("choices") or []
            if str(word).strip().lower() in pool
        ]
        if len(choices) < WORD_SLOT_COUNT or target_word not in choices:
            round_data = build_word_garden_round_for_target(
                self.learner,
                target_word,
                pool=pool,
                vocabulary_data=self.word_questions,
            )
            target_word = str(round_data.get("target") or target_word).lower()
            choices = [
                str(word).strip().lower()
                for word in round_data.get("choices") or []
                if str(word).strip().lower() in pool
            ]
        if target_word not in choices:
            choices = [target_word, *[word for word in choices if word != target_word]]
            choices = choices[:WORD_SLOT_COUNT]
            while len(choices) < WORD_SLOT_COUNT:
                for filler in pool:
                    if filler not in choices:
                        choices.append(filler)
                    if len(choices) >= WORD_SLOT_COUNT:
                        break
        prompt = f"Touch the {target_word.capitalize()}."
        self.state.current_task_target = target_word
        self.state.current_task_prompt = prompt
        self.state.word_choice_slots = choices[:WORD_SLOT_COUNT]
        self.state.current_hint_level = 0
        self.state.current_word_mode = str(round_data.get("reason") or "")
        self.state.word_garden_support = ""
        self.state.word_garden_option_count = len(self.state.word_choice_slots)
        self.state.last_word_selected = ""
        self.state.last_word_feedback_message = ""
        self.state.last_word_garden_target = target_word
        self.learner.last_word_garden_target = target_word
        self.learner.save_profile()
        self._warm_word_garden_round_assets(target_word, choices[:WORD_SLOT_COUNT])

    def _warm_word_garden_round_assets(self, target: str, choices: list[str]) -> None:
        words = {str(target).strip().lower()}
        words.update(str(word).strip().lower() for word in choices[:WORD_SLOT_COUNT])
        self.asset_manager.warm_word_garden_round(tuple(sorted(words)))

    def _configure_word_garden_task(self) -> None:
        self._apply_word_garden_round(self._build_word_garden_round())

    def _warm_writing_recognition(self) -> None:
        import threading

        def _run() -> None:
            try:
                from writing_recognition.runner import warm_recognition_model

                warm_recognition_model()
            except Exception:
                pass

        threading.Thread(target=_run, daemon=True).start()

    def _configure_writing_castle_task(self, *, mode: str | None = None) -> None:
        if mode is not None:
            round_data = build_writing_round_for_mode(self.learner, mode)
        else:
            round_data = build_writing_round(self.learner)
        mode_key = str(round_data.get("mode") or "letters")
        target = str(round_data.get("target") or "A")
        prompt = str(round_data.get("prompt") or f"Write the letter {target}.")
        speech = str(round_data.get("speech") or prompt)
        self.state.writing_mode = mode_key
        self.state.writing_prompt = prompt
        self.state.current_task_target = target.upper() if mode_key == "letters" else target.lower()
        self.state.current_task_prompt = prompt
        self.state.writing_result_text = ""
        self.state.writing_hint_text = ""
        self.state.current_round_wrong_count = 0
        self.state.current_hint_level = 0
        self._reset_writing_canvas()
        self.state.last_spoken_text = speech

    def _begin_app_loading(self, message: str) -> None:
        self.state.app_loading = True
        self.state.app_loading_message = str(message or "Loading...").strip() or "Loading..."
        self.state.app_loading_started_at = pygame.time.get_ticks()

    def _end_app_loading(self) -> None:
        self.state.app_loading = False
        self.state.app_loading_message = ""
        self.state.app_loading_started_at = 0

    def _toggle_writing_mode(self) -> None:
        next_mode = "words" if str(self.state.writing_mode or "letters") == "letters" else "letters"
        self._clear_writing_board()
        self._configure_writing_castle_task(mode=next_mode)
        if self.state.voice_enabled:
            spoken = str(self.state.last_spoken_text or self.state.writing_prompt or "").strip()
            if spoken:
                self.voice.speak(spoken, tone="instruct")

    def _ensure_writing_canvas(self) -> pygame.Surface:
        if self._writing_canvas is None:
            self._reset_writing_canvas()
        return self._writing_canvas  # type: ignore[return-value]

    def _reset_writing_canvas(self) -> None:
        width = max(64, WRITING_BOARD_RECT.width - 12)
        height = max(64, WRITING_BOARD_RECT.height - 12)
        self._writing_canvas = pygame.Surface((width, height))
        self._writing_canvas.fill((255, 255, 255))

    def _clear_writing_board(self) -> None:
        self._reset_writing_canvas()
        self.state.writing_result_text = ""
        self.state.writing_hint_text = ""

    def _writing_board_point(self, position: tuple[int, int]) -> tuple[int, int] | None:
        canvas = self._ensure_writing_canvas()
        board_rect = WRITING_BOARD_RECT.inflate(-6, -6)
        if not board_rect.collidepoint(position):
            return None
        local_x = int((position[0] - board_rect.x) * canvas.get_width() / max(1, board_rect.width))
        local_y = int((position[1] - board_rect.y) * canvas.get_height() / max(1, board_rect.height))
        local_x = max(0, min(canvas.get_width() - 1, local_x))
        local_y = max(0, min(canvas.get_height() - 1, local_y))
        return local_x, local_y

    def _draw_writing_stroke(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        canvas = self._ensure_writing_canvas()
        pygame.draw.line(canvas, WRITING_INK_COLOR, start, end, WRITING_BRUSH_RADIUS * 2)
        pygame.draw.circle(canvas, WRITING_INK_COLOR, end, WRITING_BRUSH_RADIUS)

    def _handle_writing_draw_event(self, event: pygame.event.Event) -> bool:
        if self.state.current_screen_id != "writing_castle_game":
            return False
        if self.state.answer_popup_kind or self.state.writing_processing:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            point = self._writing_board_point(event.pos)
            if point is None:
                return False
            self._writing_draw_on = True
            self._writing_last_pos = point
            pygame.draw.circle(self._ensure_writing_canvas(), WRITING_INK_COLOR, point, WRITING_BRUSH_RADIUS)
            return True
        if event.type == pygame.MOUSEMOTION and self._writing_draw_on:
            point = self._writing_board_point(event.pos)
            if point is None or self._writing_last_pos is None:
                return True
            self._draw_writing_stroke(self._writing_last_pos, point)
            self._writing_last_pos = point
            return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._writing_draw_on = False
            self._writing_last_pos = None
            return self._writing_board_point(event.pos) is not None
        return False

    def _save_writing_snapshot(self) -> Path:
        canvas = self._ensure_writing_canvas()
        path = self._writing_snapshot_path
        path.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(canvas, str(path))
        return path

    def _submit_writing(self) -> None:
        if self.state.writing_processing:
            return

        from writing_recognition.runner import recognition_available, recognition_error_message

        if not recognition_available():
            detail = recognition_error_message()
            message = "Handwriting recognition is not ready yet. Try again soon."
            if detail:
                message = f"{message} ({detail})"
            self._show_writing_mistake_feedback(message)
            return

        import threading

        snapshot = self._save_writing_snapshot()
        mode = str(self.state.writing_mode or "letters")
        target = str(self.state.current_task_target or "")
        board_out = self._writing_snapshot_path.with_name(".recognition_board.png")

        self.state.writing_processing = True
        self._begin_app_loading("Reading your writing...")
        self._writing_job_done = False
        self._writing_job_result = None

        def _worker() -> None:
            try:
                from writing_recognition.runner import recognize_snapshot

                outcome = recognize_snapshot(
                    snapshot,
                    mode,
                    board_out=board_out,
                    expected_letter=target if mode == "letters" else "",
                )
                self._writing_job_result = _WritingRecognitionJob(
                    mode=mode,
                    target=target,
                    recognized=str(outcome.recognized or ""),
                    hint=str(outcome.hint or ""),
                )
            except Exception as exc:
                self._writing_job_result = _WritingRecognitionJob(
                    mode=mode,
                    target=target,
                    error=str(exc),
                )
            finally:
                self._writing_job_done = True

        threading.Thread(target=_worker, daemon=True, name="lumi-writing-ocr").start()

    def _poll_writing_recognition(self) -> None:
        if not self._writing_job_done:
            return
        self._writing_job_done = False
        job = self._writing_job_result
        self._writing_job_result = None
        self.state.writing_processing = False
        self._end_app_loading()
        if job is None:
            return
        if job.error:
            self._show_writing_mistake_feedback(f"Could not read your writing. Try again. ({job.error})")
            return
        if job.unavailable_message:
            self._show_writing_mistake_feedback(job.unavailable_message)
            return
        self._apply_writing_recognition(job)

    def _apply_writing_recognition(self, job: _WritingRecognitionJob) -> None:
        from writing_recognition import letter_answer_matches, word_answer_matches

        mode = job.mode
        target = job.target
        recognized = job.recognized
        self.state.writing_result_text = recognized
        self.state.writing_hint_text = str(job.hint or "")

        if mode == "letters":
            correct = letter_answer_matches(target, recognized)
        else:
            correct = word_answer_matches(target, recognized)

        if correct:
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.correct_answers = int(self.learner.correct_answers) + 1
            self.learner.update_accuracy()
            self.learner.update_correct_streak()
            update_score(self.learner, stars_earned)
            self._award_answer_points(stars_earned)
            advance_writing_curriculum(self.learner)
            self.learner.save_profile()
            if maybe_complete_writing_castle(self.learner):
                self._mark_world_completed(WORLD_WRITING_CASTLE)
            self._show_writing_correct_feedback(stars_earned=stars_earned)
        else:
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.update_accuracy()
            self.learner.update_correct_streak()
            expected = target.upper() if mode == "letters" else target.lower()
            got = recognized.upper() if mode == "letters" else recognized.lower()
            message = f"I read '{got or '?'}'. Try writing {expected} again."
            self._show_writing_mistake_feedback(message)

    def _show_writing_correct_feedback(self, *, stars_earned: int = 0) -> None:
        message = get_feedback(True)["message"]
        self._show_answer_popup(
            "correct",
            message,
            next_screen="writing_castle_game",
            refresh=True,
            sfx="correct",
            stars_earned=stars_earned,
        )

    def _show_writing_mistake_feedback(self, message: str) -> None:
        msg = str(message or "").strip() or "Good try. Write it again!"
        self._show_answer_popup(
            "wrong",
            msg,
            next_screen="writing_castle_game",
            preserve=True,
            sfx="wrong",
        )

    def _configure_voice_challenge_task(self) -> None:
        target = self._voice_challenge_target()
        self.state.current_task_target = target
        self.state.current_task_prompt = WORD_VOICE_QUESTION
        self.state.current_hint_level = 0
        self.asset_manager.warm_word_garden_round((target,))

    def _configure_letter_voice_task(self) -> None:
        target = self._letter_voice_target()
        self.state.current_task_target = target
        self.state.current_task_prompt = LETTER_VOICE_PROMPT
        self.state.current_hint_level = 0
        self.asset_manager.scaled_letter_tile(
            "letter_island_game",
            target,
            int(SCREEN_WIDTH * 0.24),
            int(SCREEN_HEIGHT * 0.32),
            selected=False,
        )

    def _letter_voice_target(self) -> str:
        candidate = str(self.state.current_task_target or "").strip().upper()
        if len(candidate) == 1 and candidate.isalpha():
            return candidate
        slots = [str(item).strip().upper() for item in self.state.letter_choice_slots[:LETTER_SLOT_COUNT]]
        for letter in slots:
            if len(letter) == 1 and letter.isalpha():
                return letter
        return "A"

    def _voice_challenge_target(self) -> str:
        candidate = str(self.state.current_task_target or "").strip().lower()
        pool = self._word_garden_pool()
        if candidate in pool:
            return candidate
        if self.state.word_choice_slots:
            first = str(self.state.word_choice_slots[0] or "").strip().lower()
            if first in pool:
                return first
        return self._pick_visible_word(candidate or "sun")

    def _reset_all_progress(self) -> None:
        """Reset saved learner progress and clear in-memory gameplay state."""
        self.learner.reset_profile(keep_child_name=True)
        settings = self.settings.load_settings()
        difficulty_level = difficulty_mode_to_level(str(settings.get("difficulty_mode", "Medium")))
        self.learner.difficulty = difficulty_level
        self.learner.lumi_energy = 100
        self.learner.save_profile()
        self.state.difficulty = difficulty_level

        self.state.stars = 0
        self.state.last_action = ""
        self.state.last_mistake_type = ""
        self.state.current_hint_level = 0
        self.state.letter_demo_mode = False
        self.state.preserve_letter_island_task = False
        self.state.preserve_word_garden_task = False
        self.state.letter_review_mode = False
        self.state.pending_letter_curriculum_advance = False
        self.state.completed_letter_target = ""
        self.state.completed_letter_choices = []
        self.state.highlight_letter_slot = -1
        self.state.last_selected_letter = ""
        self.state.last_letter_feedback_message = ""
        self.state.last_word_selected = ""
        self.state.last_word_feedback_message = ""
        self.state.current_word_mode = ""
        self.state.word_garden_support = ""
        self.state.word_garden_option_count = 4
        self.state.bd_practice_target = ""
        self.state.bd_practice_step = 0
        self.state.bd_confusion_attempts = 0
        self.state.last_unlocked_badges = []
        self.state.badge_return_screen = ""
        self.state.world_map_status_message = ""
        self.state.world_map_status_shown_at_ms = None
        self.state.current_round_wrong_count = 0
        self.state.last_spoken_text = ""
        self.state.practice_recommendation = None
        self.state.teacher_report = None
        self.state.microphone_status_message = ""
        self.state.end_session_pending = False
        self.state.session_end_report_path = ""
        self.state.offline_status_message = ""
        self.state.word_choice_slots = list(self._word_garden_pool())
        self.state.gameplay_refresh_pending = True
        self.state.history = [self.state.current_screen_id] if self.state.current_screen_id else []

        # Letter island owns current_task_target; word configures on screen entry.
        self._configure_letter_island_task()

    def _badge_continue_screen(self) -> str:
        """Resume gameplay after a badge unlock; level summary only for world finales."""
        from engine.scoring import LETTER_ISLAND_COMPLETE_BADGE

        names = [str(name).strip() for name in (self.state.last_unlocked_badges or [])]
        if names and names[0] == LETTER_ISLAND_COMPLETE_BADGE:
            return "progress_complete"
        for screen_id in reversed(self.state.history):
            if screen_id in {
                "letter_island_game",
                "bd_practice",
                "letter_voice_challenge",
                "letter_listening_state",
            }:
                return "letter_island_game"
            if screen_id in {"word_garden_game", "voice_challenge", "listening_state"}:
                return "word_garden_game"
        return "letter_island_game"

    def _handle_badges(self, unlocked: list[str], *, return_screen: str = "") -> None:
        """Record unlocked badges and switch to the badge unlock screen."""
        if not unlocked:
            return
        self.state.last_unlocked_badges = unlocked
        self.learner.add_points(POINTS_PER_BADGE * len(unlocked))
        self.state.badge_return_screen = return_screen or self._badge_continue_screen()
        self._play_feedback_sfx("badge")
        self.set_screen("badge_unlock")

    def _handle_word_garden_selection(self, selected_word: str) -> None:
        target_word = self.state.current_task_target or "sun"
        self.state.last_word_selected = selected_word
        hints_used = int(self.state.current_hint_level or 0)
        first_try = hints_used == 0
        if selected_word == target_word:
            self.learner.record_word_mastery_attempt(
                target_word,
                correct=True,
                first_try=first_try,
                hints_used=hints_used,
            )
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.update_correct_streak()
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.correct_answers = int(self.learner.correct_answers) + 1
            self.learner.update_accuracy()
            update_score(self.learner, stars_earned)
            self._award_answer_points(stars_earned)
            self.learner.mark_word_mastered(target_word)
            if maybe_complete_word_garden(self.learner):
                self._mark_world_completed(WORLD_WORD_GARDEN)
            unlocked = check_badge_unlocks(self.learner)
            self.state.current_hint_level = 0
            self.state.last_word_feedback_message = self._word_garden_correct_message()
            if unlocked:
                self._play_feedback_sfx("correct", stars_earned=stars_earned)
                self._handle_badges(unlocked, return_screen="word_garden_game")
                return
            self._show_word_correct_feedback(self.state.last_word_feedback_message, stars_earned=stars_earned)
            return

        self.learner.record_word_mastery_attempt(
            target_word,
            correct=False,
            first_try=first_try,
            hints_used=hints_used,
            confused_with=selected_word,
        )
        self.learner.update_wrong_streak()
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()
        self.learner.record_weak_word(target_word)
        mistake_type = diagnose_word_mistake(target_word, selected_word, self.word_questions)
        self.state.last_mistake_type = mistake_type
        self.state.current_hint_level = 1
        self._show_word_mistake_feedback(
            get_feedback(
                False,
                mistake_type=mistake_type,
                target=target_word,
                selected=selected_word,
            )["message"],
            return_screen="word_garden_game",
        )

    def _start_word_practice(self, word: str) -> None:
        self.state.preserve_word_garden_task = True
        self._apply_word_garden_round(
            build_word_garden_round_for_target(
                self.learner,
                word,
                pool=self._word_garden_pool(),
                vocabulary_data=self.word_questions,
            )
        )
        self.set_screen("word_garden_game")

    def _configure_teacher_report(self) -> None:
        self.state.teacher_report = generate_report(self.learner.get_profile())

    def _configure_end_session(self) -> None:
        report = generate_report(self.learner.get_profile())
        self.state.teacher_report = report
        saved_path = str(report.get("session_report_path", "") or "")
        self.state.session_end_report_path = saved_path
        print(f"[Lumi Session] End session report saved: {saved_path or 'not saved'}")

    def _open_recommended_practice(self, report: dict) -> None:
        screen_id = resolve_engine_screen_id(str(report.get("recommended_screen_id", "")))
        if screen_id == "bd_practice":
            weak_letters = report.get("weak_letters", {})
            target = "B"
            if isinstance(weak_letters, dict) and int(weak_letters.get("D", 0) or 0) > int(weak_letters.get("B", 0) or 0):
                target = "D"
            self._configure_bd_practice(target)
        elif screen_id == "word_garden_game":
            pool = self._word_garden_pool()
            self._start_word_practice(pool[0] if pool else "sun")
        self.set_screen(screen_id)

    def _handle_teacher_report_action(self, action: str) -> bool:
        if self.state.current_screen_id != "teacher_report":
            return False
        if action in {"back", "report_home", "home"}:
            if self.state.end_session_pending:
                self.state.end_session_pending = False
                self.set_screen("end_session")
            else:
                self.set_screen("main_menu")
            return True
        if action in {"finish_session", "end_session"}:
            self.state.end_session_pending = False
            self.set_screen("end_session")
            return True
        if action == "practice_recommendation":
            report = self.state.teacher_report or generate_report(self.learner.get_profile())
            self._open_recommended_practice(report)
            return True
        if action == "report_refresh":
            self._configure_teacher_report()
            self.set_screen("teacher_report")
            return True
        return False

    def _process_voice_capture_result(self, spoken: str | None) -> None:
        target_word = self._voice_challenge_target()
        spoken_text = (spoken or "").strip().lower()
        self.state.last_spoken_text = spoken_text
        result = check_spoken_answer(spoken_text, target_word)

        if result == "correct":
            stars_earned = calculate_stars(True, self.state.current_hint_level)
            self.learner.update_correct_streak()
            self.learner.attempts = int(self.learner.attempts) + 1
            self.learner.correct_answers = int(self.learner.correct_answers) + 1
            self.learner.update_accuracy()
            update_score(self.learner, stars_earned)
            self._award_answer_points(stars_earned)
            self.learner.mark_word_mastered(target_word)
            completed_worlds = list(self.learner.completed_worlds)
            if "voice_challenge" not in completed_worlds:
                completed_worlds.append("voice_challenge")
                self.learner.completed_worlds = completed_worlds
                self.learner.save_profile()
            unlocked = check_badge_unlocks(self.learner)
            self.state.current_hint_level = 0
            self.state.last_word_feedback_message = "Correct!"
            self._play_feedback_sfx("correct", stars_earned=stars_earned)
            if unlocked:
                self._show_voice_pronunciation_feedback("correct")
                self._speak_tutor_line("Correct!")
                self._handle_badges(unlocked, return_screen="word_correct_feedback")
                return
            self._show_voice_pronunciation_feedback("correct")
            self._speak_tutor_line("Correct!")
            self.state.suppress_screen_speech_once = True
            self.set_screen("voice_challenge")
            self._schedule_voice_correct_advance("word")
            return

        self.learner.update_wrong_streak()
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()

        if result == "close":
            self._show_voice_pronunciation_feedback("try_again")
            self._speak_tutor_line("Try again. Almost! I heard something close.")
            self.state.suppress_screen_speech_once = True
            self.set_screen("voice_challenge")
            return

        self.learner.record_weak_word(target_word)
        self._show_voice_pronunciation_feedback("try_again")
        self._speak_tutor_line(self._voice_voice_try_again_line(target_word, spoken_text))
        self.state.suppress_screen_speech_once = True
        self.set_screen("voice_challenge")

    def _process_letter_voice_capture_result(self, spoken: str | None) -> None:
        target_letter = self._letter_voice_target()
        spoken_text = (spoken or "").strip()
        self.state.last_spoken_text = spoken_text.lower()

        if not spoken_text:
            message = (
                stt_status_message()
                if not is_stt_ready()
                else "I didn't catch that. Try again."
            )
            self.state.microphone_status_message = message
            self._show_voice_pronunciation_feedback("try_again")
            if self.state.voice_enabled:
                self.voice.speak(message)
            self.state.suppress_screen_speech_once = True
            self.set_screen("letter_voice_challenge")
            return

        result = check_spoken_answer(spoken_text, target_letter)
        print(
            f"[Lumi Voice] letter check target={target_letter!r} "
            f"heard={spoken_text!r} result={result}"
        )

        if result == "correct":
            self._award_letter_round_success(target_letter, voice_mode=True)
            return

        self.learner.update_wrong_streak()
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()

        if result == "close":
            self._show_letter_mistake_feedback(
                "Almost! I heard something close. Try again.",
                return_screen="letter_voice_challenge",
            )
            return

        if not self.learner.letter_is_ai_mastered(target_letter):
            self.learner.record_weak_letter(target_letter)
        self._show_letter_mistake_feedback(
            self._letter_voice_help_line(target_letter, heard=spoken_text),
            return_screen="letter_voice_challenge",
        )

    def _voice_voice_try_again_line(self, target_word: str | None = None, spoken: str = "") -> str:
        word = str(target_word or self._voice_challenge_target() or "sun").strip().lower()
        self.state.current_hint_level += 1
        self.learner.record_hint_usage(self.state.current_hint_level)
        if spoken:
            mistake = diagnose_word_mistake(word, spoken, self.word_questions)
            hint = choose_hint(self.learner, "word", mistake, target=word, selected=spoken)
        else:
            hint = get_hint("voice", self.state.current_hint_level, word)
        return f"Try again. {hint}"

    def _letter_voice_help_line(self, target_letter: str | None = None, *, heard: str = "") -> str:
        letter = str(target_letter or self._letter_voice_target() or "A").strip().upper()
        level = max(1, int(getattr(self.state, "current_hint_level", 0) or 0))
        return self.hint_engine.letter_speaking_hint(
            letter, level=level, heard=heard, profile=self.learner
        )

    def _voice_help_line(self, target_word: str | None = None, *, heard: str = "") -> str:
        word = str(target_word or self._voice_challenge_target() or "sun").strip().lower()
        level = max(1, int(getattr(self.state, "current_hint_level", 0) or 0))
        return self.hint_engine.word_speaking_hint(
            word, level=level, heard=heard, profile=self.learner
        )

    def _advance_to_next_letter_voice_round(self) -> None:
        if self.state.pending_letter_curriculum_advance:
            mastered_letter = str(
                self.state.completed_letter_target or self.state.current_task_target or "A"
            ).upper()
            advance_letter_curriculum(self.learner, mastered=True, letter=mastered_letter)
            self.state.pending_letter_curriculum_advance = False
        self._configure_letter_island_task()
        self._configure_letter_voice_task()
        self.state.suppress_screen_speech_once = True
        self.set_screen("letter_voice_challenge")

    def _advance_to_next_word_voice_round(self) -> None:
        self._configure_word_garden_task()
        self._configure_voice_challenge_task()
        self.state.suppress_screen_speech_once = True
        self.set_screen("voice_challenge")

    def _word_target_sound_line(self) -> str:
        return self._word_garden_voice_prompt()

    def _word_garden_voice_prompt(self) -> str:
        target_word = str(self.state.current_task_target or "sun").strip().lower()
        return f"Touch the {target_word.capitalize()}."

    def _word_garden_hint_message(self) -> str:
        target_word = self.state.current_task_target or "sun"
        level = max(1, int(self.state.current_hint_level or 0))
        return self.hint_engine.word_hint(
            target_word,
            level=level,
            mistake_type=self.state.last_mistake_type or "",
            selected=self.state.last_word_selected or "",
            profile=self.learner,
        )

    def _word_garden_correct_message(self) -> str:
        target_word = self.state.current_task_target or "sun"
        return f"Wonderful! {target_word.capitalize()}."

    def _advance_bd_practice(self) -> None:
        if self.state.bd_practice_target == "B":
            self.state.bd_practice_target = "D"
            self.state.bd_practice_step = 1
            self.state.current_task_target = "D"
            self.state.current_task_prompt = "Now find the letter D."
            self.voice.speak("Great job! Now find D.")
            return

        self.learner.mark_letter_mastered("D")
        unlocked_badges = check_badge_unlocks(self.learner)
        self.state.bd_practice_target = ""
        self.state.bd_practice_step = 2
        self.state.current_task_target = "B"
        self.state.current_task_prompt = "Find the letter B."
        if "B and D Master" in unlocked_badges:
            self.voice.speak("Great job! You know B and D!")
            self._handle_badges(["B and D Master"], return_screen="letter_island_game")
        else:
            self._show_letter_correct_feedback("Great job! You know B and D!")

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
        if self.state.app_loading and event.type != pygame.QUIT:
            if event.type != pygame.KEYDOWN or event.key not in {pygame.K_ESCAPE}:
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            # temporary debug toggle
            self._toggle_debug_hitboxes()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
            # keyboard shortcut to toggle persistent debug overlay (dev)
            self._toggle_debug_persistent()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            self.next_screen()
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            self.previous_screen()
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_mic_hint_badge_click(event.pos):
                return
        action = self.current_screen.handle_event(event)
        if action:
            self._handle_action(action)

    def _handle_action(self, action: str) -> None:
        if action in self.screens:
            self.set_screen(action)
            return
        if self._handle_teacher_report_action(action):
            return
        if action == "back":
            self.set_screen("main_menu")
            return
        if action == "home":
            if self.state.current_screen_id in {
                "world_map",
                "letter_island_game",
                "word_garden_game",
                "writing_castle_game",
                "bd_practice",
            }:
                self.set_screen("world_map")
            else:
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
        if self.state.current_screen_id == "word_garden_game":
            if action == "repeat_prompt":
                self._speak_tutor_line(self._word_garden_voice_prompt())
                return
            if action == "show_hint":
                self.state.current_hint_level += 1
                self.learner.record_hint_usage(self.state.current_hint_level)
                self.state.last_word_feedback_message = self._word_garden_hint_message()
                self._show_hint_popup(self.state.last_word_feedback_message)
                return
            if action == "voice_mode":
                self._begin_voice_challenge()
                return
            if action in LEGACY_WORD_ACTIONS or action.startswith("select_word_slot_"):
                selected = self._resolve_word_from_action(action)
                if selected:
                    self._handle_word_garden_selection(selected)
                return
            if action in {"play_cat_sound", "play_target_word_sound"}:
                self._speak_tutor_line(self._word_target_sound_line())
                return
        if self.state.current_screen_id == "writing_castle_game":
            if action == "repeat_prompt":
                spoken = str(self.state.last_spoken_text or self.state.writing_prompt or self.state.current_task_prompt or "").strip()
                if spoken:
                    self._speak_tutor_line(spoken)
                return
            if action in {"verify_writing", "complete_writing"}:
                self._submit_writing()
                return
            if action == "clear_writing":
                self._clear_writing_board()
                return
            if action == "toggle_writing_mode":
                self._toggle_writing_mode()
                return
        if self.state.current_screen_id == "voice_challenge":
            if action == "repeat_word":
                self._speak_tutor_line(WORD_VOICE_QUESTION)
                return
            if action == "voice_help":
                self.state.current_hint_level += 1
                self.learner.record_hint_usage(self.state.current_hint_level)
                self._show_hint_popup(self._voice_help_line(self._voice_challenge_target()))
                return
            if action == "skip_voice":
                self.state.preserve_word_garden_task = True
                self.set_screen("word_garden_game")
                return
            if action == "start_listening":
                self._start_voice_listening()
                return
        if self.state.current_screen_id == "letter_voice_challenge":
            if action == "repeat_letter":
                self._speak_tutor_line(LETTER_VOICE_PROMPT, tone="instruct")
                return
            if action == "letter_voice_help":
                self.state.current_hint_level += 1
                self.learner.record_hint_usage(self.state.current_hint_level)
                self._show_hint_popup(self._letter_voice_help_line(self._letter_voice_target()))
                return
            if action == "skip_letter_voice":
                self.state.preserve_letter_island_task = True
                self.set_screen("letter_island_game")
                return
            if action == "start_letter_listening":
                self._start_letter_voice_listening()
                return
        if self.state.current_screen_id == "bd_practice":
            if action == "repeat_bd_prompt":
                target_letter = self.state.bd_practice_target or "B"
                self.voice.speak(f"B has a belly. D has a drum. Find {target_letter}.")
                return
            if action == "bd_hint":
                self.voice.speak("B has a belly. D has a drum.")
                return
            if action in {"answer_B", "answer_D"}:
                target_letter = self.state.bd_practice_target or "B"
                selected_letter = "B" if action == "answer_B" else "D"
                self.learner.attempts = int(self.learner.attempts) + 1
                if selected_letter == target_letter:
                    self.learner.correct_answers = int(self.learner.correct_answers) + 1
                    self.learner.update_accuracy()
                    self.learner.update_correct_streak()
                    stars_earned = calculate_stars(True, self.state.current_hint_level)
                    update_score(self.learner, stars_earned)
                    self._award_answer_points(stars_earned)
                    self.learner.mark_letter_mastered(selected_letter)
                    self._play_feedback_sfx("correct", stars_earned=stars_earned)
                    self._advance_bd_practice()
                else:
                    self.learner.update_wrong_streak()
                    self.learner.update_accuracy()
                    self.state.last_mistake_type = "bd_confusion"
                    self.learner.record_weak_letter(target_letter)
                    self._show_letter_mistake_feedback(
                        get_feedback(False, mistake_type="bd_confusion")["message"],
                        return_screen="bd_practice",
                    )
                return
        if self.state.current_screen_id == "listening_state":
            if action == "repeat_word":
                if self.state.microphone_test_mode:
                    self.voice.speak(self.state.microphone_status_message or "Microphone is ready.")
                else:
                    self.voice.speak(WORD_VOICE_QUESTION)
                return
            if action in {"stop_listening", "stop_and_process"}:
                if self.state.microphone_test_mode:
                    self._finish_microphone_test()
                    return
                self.voice.speak("Listening stopped. What is this?")
                self.set_screen("voice_challenge")
                return
        if self.state.current_screen_id == "letter_listening_state":
            if action == "repeat_letter":
                self.voice.speak(LETTER_VOICE_PROMPT, tone="instruct")
                return
            if action in {"stop_letter_listening", "stop_listening", "stop_and_process"}:
                self.voice.speak("Listening stopped. What letter is this?")
                self.set_screen("letter_voice_challenge")
                return
        if self.state.current_screen_id == "microphone_check":
            if action in {"test_mic", "test_microphone"}:
                self.set_screen("listening_state")
                return
            if action == "skip_mic":
                self.set_screen("settings")
                return
        if action == "view_report" or action == "open_report":
            self.state.end_session_pending = True
            self.set_screen("teacher_report")
            return
        if action == "continue_offline":
            self.state.offline_status_message = ""
            self.set_screen("main_menu")
            return
        if action == "continue_from_badge":
            return_screen = str(self.state.badge_return_screen or "").strip()
            self.state.badge_return_screen = ""
            if return_screen:
                if return_screen in {"letter_island_game", "word_garden_game"}:
                    self.state.gameplay_refresh_pending = True
                self.set_screen(return_screen)
                return
            if len(self.state.history) >= 2:
                previous = self.state.history[-2]
            else:
                previous = "world_map"
            self.set_screen(previous)
            return
        if action == "view_badges":
            sync_world_completion(self.learner)
            if not self.state.last_completed_world_id:
                self.state.last_completed_world_id = latest_completed_world(self.learner)
            self.set_screen("progress_complete")
            return
        if self.state.current_screen_id == "letter_island_game" and (
            action.startswith("select_letter_slot_")
            or action in {"select_letter_b", "select_letter_d", "select_letter_p", "select_letter_a", "repeat_prompt", "show_hint", "voice_or_speak_mode"}
        ):
            self._handle_letter_island_action(action)
            return
        if action == "repeat_instruction_audio" or action == "repeat_instruction":
            return
        if action == "replay_welcome_audio":
            self._speak_tutor_line(get_lumi_speech("welcome"))
            return
        if action == "replay_main_menu_audio":
            self._speak_tutor_line(get_lumi_speech("main_menu"))
            return
        if action == "replay_instruction_audio":
            return
        if action == "toggle_music":
            music_enabled = self.settings.toggle_music()
            self.state.music_enabled = music_enabled
            self.sound.set_enabled(music_enabled)
            print(f"Music enabled: {music_enabled}")
            if self.state.voice_enabled:
                self.voice.speak("Music on" if music_enabled else "Music off")
            return
        if action in {"change_difficulty", "cycle_difficulty"}:
            difficulty_mode = self.settings.cycle_difficulty()
            difficulty_level = difficulty_mode_to_level(difficulty_mode)
            self.state.difficulty = difficulty_level
            self.learner.difficulty = difficulty_level
            self.learner.save_profile()
            print(f"Difficulty mode: {difficulty_mode}")
            if self.state.voice_enabled:
                self.voice.speak(f"Difficulty {difficulty_mode}")
            return
        if action in {"reset_progress", "reset_profile"}:
            if self.state.current_screen_id != "settings":
                return
            self._reset_all_progress()
            print("Profile reset successfully")
            self._show_settings_status("Profile reset successfully")
            if self.state.voice_enabled:
                self.voice.speak("Progress reset")
            return
        if action == "toggle_voice":
            voice_enabled = self.settings.toggle_voice()
            self.state.voice_enabled = voice_enabled
            self.voice.set_enabled(voice_enabled)
            print(f"Voice enabled: {voice_enabled}")
            if voice_enabled:
                self.voice.speak("Voice is on.")
            return
        if self.state.current_screen_id == "progress_complete":
            if action == "next_world":
                sync_world_completion(self.learner)
                if word_garden_unlocked(self.learner):
                    self.set_screen("word_garden_game")
                    return
                try:
                    current = int(self.learner.current_world or 1)
                except Exception:
                    current = 1
                self.learner.current_world = current + 1
                self.learner.save_profile()
                self.set_screen("world_map")
                return
            if action == "practice_again":
                self._start_practice_for_completed_world()
                return
        if action == "practice_bd_b":
            self._configure_bd_practice("B")
            self.set_screen("bd_practice")
            return
        if action == "practice_bd_d":
            self._configure_bd_practice("D")
            self.set_screen("bd_practice")
            return
        if action == "practice_word_cat" or action == "practice_word_sun":
            pool = self._word_garden_pool()
            self._start_word_practice(pool[0] if pool else "sun")
            return
        if action == "toggle_hitbox_persistent":
            self._toggle_debug_persistent()
            return
        if action == "export_hitboxes":
            path = self._export_hitboxes_to_csv()
            print(f"[DEBUG] export path: {path}")
            return
        if action == "increase_smoke":
            # increase by 1000ms up to 60000ms
            current = int(self.state.debug_smoke_duration_ms or 5000)
            new = min(60000, current + 1000)
            self.state.debug_smoke_duration_ms = new
            if self.state.voice_enabled:
                self.voice.speak(f"Smoke duration {int(new/1000)} seconds")
            print(f"[DEBUG] Smoke duration now {new}ms")
            return
        if action == "decrease_smoke":
            current = int(self.state.debug_smoke_duration_ms or 5000)
            new = max(1000, current - 1000)
            self.state.debug_smoke_duration_ms = new
            if self.state.voice_enabled:
                self.voice.speak(f"Smoke duration {int(new/1000)} seconds")
            print(f"[DEBUG] Smoke duration now {new}ms")
            return
        if action == "run_hitbox_smoke":
            # run a short hitbox smoke test using configured duration
            self.debug_hitboxes = True
            self._debug_enabled_since = pygame.time.get_ticks()
            # use configured duration
            self._debug_duration_ms = int(self.state.debug_smoke_duration_ms or 5000)
            print(f"[DEBUG] Running hitbox smoke test ({int(self._debug_duration_ms/1000)}s)")
            if self.state.voice_enabled:
                self.voice.speak("Running hitbox smoke test")
            return
        if action == "show_profile" or action == "repeat_prompt" or action == "show_hint":
            if self.state.current_screen_id in SCREEN_SPECIFIC_PROMPT_ACTIONS:
                return
            if action == "show_hint":
                self._speak_tutor_line(get_feedback("hint")["message"])
            elif action == "repeat_prompt":
                self._speak_tutor_line(self.state.current_task_prompt or get_lumi_speech(self.state.current_screen_id))
            return
        if self.state.current_screen_id == "letter_island_game":
            self._handle_letter_island_action(action)
            return
        if action == "next_activity":
            self.set_screen("word_garden_game")
            return

        if action in {"repeat_bd_prompt", "bd_hint", "answer_B", "answer_D", "next_hint_or_bd_practice", "try_again"}:
            return

    def _award_letter_round_success(self, target_letter: str, *, voice_mode: bool = False) -> None:
        target_letter = str(target_letter or "A").strip().upper()
        first_try = int(self.state.current_round_wrong_count) <= 0
        stars_earned = calculate_stars(True, self.state.current_hint_level)
        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.correct_answers = int(self.learner.correct_answers) + 1
        self.learner.update_accuracy()
        self.learner.update_correct_streak()
        update_score(self.learner, stars_earned)
        self._award_answer_points(stars_earned)
        self.learner.record_letter_mastery_attempt(
            target_letter,
            correct=True,
            first_try=first_try,
            hints_used=self.state.current_hint_level,
        )
        if not self.state.letter_review_mode:
            note_curriculum_letter_completed(self.learner)
            self.state.pending_letter_curriculum_advance = True
        world_just_completed = maybe_complete_letter_island(
            self.learner,
            letter=target_letter,
            curriculum=not self.state.letter_review_mode,
        )
        if world_just_completed:
            self._mark_world_completed(WORLD_LETTER_ISLAND)
            self._notify_parallel_worlds_unlocked()
        island_complete_badge = check_letter_island_complete_badge(self.learner)
        if island_complete_badge:
            self.state.current_hint_level = 0
            self.state.bd_confusion_attempts = 0
            self.state.last_mistake_type = ""
            self.state.last_selected_letter = target_letter
            self.state.highlight_letter_slot = -1
            self.state.completed_letter_target = target_letter
            self.state.completed_letter_choices = [
                str(item).upper() for item in self.state.letter_choice_slots[:LETTER_SLOT_COUNT]
            ]
            correct_message = get_feedback(True)["message"]
            self.state.last_letter_feedback_message = (
                f"{correct_message} You perfected every letter A–Z!"
            )
            self.state.stars = stars_earned
            if voice_mode:
                self._show_voice_pronunciation_feedback("correct")
                self._speak_tutor_line("Correct!")
            self._handle_badges(island_complete_badge, return_screen="progress_complete")
            return
        milestone_unlocked = check_letter_milestone_badges(
            self.learner,
            target_letter,
            curriculum=not self.state.letter_review_mode,
        )
        unlocked = milestone_unlocked
        self.state.current_hint_level = 0
        self.state.bd_confusion_attempts = 0
        self.state.last_mistake_type = ""
        self.state.last_selected_letter = target_letter
        self.state.highlight_letter_slot = -1
        self.state.completed_letter_target = target_letter
        self.state.completed_letter_choices = [
            str(item).upper() for item in self.state.letter_choice_slots[:LETTER_SLOT_COUNT]
        ]
        if unlocked:
            resume = "progress_complete" if world_just_completed else "letter_island_game"
            if voice_mode:
                self._show_voice_pronunciation_feedback("correct")
                self._speak_tutor_line("Correct!")
            else:
                self._play_feedback_sfx("correct", stars_earned=stars_earned)
            if world_just_completed:
                self.state.stars = stars_earned
            self._handle_badges(unlocked, return_screen=resume)
            return
        if world_just_completed:
            self.state.stars = stars_earned
            self.state.last_letter_feedback_message = (
                f"{LETTER_CORRECT_SPEECH}. You finished Letter Island!"
            )
            if voice_mode:
                self._show_voice_pronunciation_feedback("correct")
                self._speak_tutor_line("Correct!")
            self.set_screen("progress_complete")
            return
        if voice_mode:
            self._show_voice_pronunciation_feedback("correct")
            self._speak_tutor_line("Correct!")
            self.state.suppress_screen_speech_once = True
            self.set_screen("letter_voice_challenge")
            self._schedule_voice_correct_advance("letter")
            return
        self._show_letter_correct_feedback("", stars_earned=stars_earned)

    def _handle_letter_island_action(self, action: str) -> None:
        target_letter = (self.state.current_task_target or "A").upper()

        if action == "repeat_prompt":
            self._speak_tutor_line(self.state.current_task_prompt or f"Find the letter {target_letter}.")
            return

        if action == "show_hint":
            self.state.current_hint_level += 1
            self.learner.record_hint_usage(self.state.current_hint_level)
            hint_message = self.hint_engine.letter_hint(
                target_letter,
                level=self.state.current_hint_level,
                mistake_type=self.state.last_mistake_type,
                selected=self.state.last_selected_letter,
                profile=self.learner,
            )
            self._show_hint_popup(hint_message)
            return

        if action == "voice_or_speak_mode":
            self._begin_letter_voice_challenge()
            return

        selected_letter = self._resolve_letter_from_action(action)
        if selected_letter is None:
            return

        if selected_letter == target_letter:
            self._award_letter_round_success(target_letter)
            return

        self.learner.attempts = int(self.learner.attempts) + 1
        self.learner.update_accuracy()
        self.learner.update_wrong_streak()
        self.state.current_round_wrong_count += 1
        self.state.last_selected_letter = selected_letter
        self.state.highlight_letter_slot = self._slot_index_for_letter(selected_letter) or -1
        self.state.last_mistake_type = diagnose_letter_mistake(target_letter, selected_letter)
        if not self.learner.letter_is_ai_mastered(target_letter):
            self.learner.record_weak_letter(target_letter)
        self.learner.record_letter_mastery_attempt(
            target_letter,
            correct=False,
            hints_used=self.state.current_hint_level,
            confused_with=selected_letter,
        )
        feedback = get_feedback(
            False,
            mistake_type=self.state.last_mistake_type,
            target=target_letter,
            selected=selected_letter,
        )
        self.state.last_letter_feedback_message = feedback["message"]
        if self.state.last_mistake_type == "bd_confusion":
            self.state.bd_confusion_attempts += 1
            if self.state.bd_confusion_attempts >= 2:
                self._configure_bd_practice(target_letter if target_letter in {"B", "D"} else "B")
                self.set_screen("bd_practice")
                return
            self._show_letter_mistake_feedback(feedback["message"])
            return
        self._show_letter_mistake_feedback(feedback["message"])
        return

    def _speak_for_screen(self, screen_id: str) -> None:
        if not self.state.voice_enabled:
            return
        self.voice.clear_pending()

        if screen_id == "welcome":
            self.voice.speak(get_lumi_speech(screen_id), tone="encourage")
            return

        if screen_id == "how_to_play":
            return

        if screen_id == "world_map":
            self.voice.speak(get_lumi_speech(screen_id), tone="encourage")
            return

        if screen_id == "letter_island_game":
            self.voice.speak(
                self.state.current_task_prompt or get_lumi_speech(screen_id, self.state.current_task_target),
                tone="instruct",
            )
            return

        if screen_id == "word_garden_game":
            self.voice.speak(self._word_garden_voice_prompt(), tone="instruct")
            return

        if screen_id == "writing_castle_game":
            spoken = str(self.state.last_spoken_text or self.state.writing_prompt or self.state.current_task_prompt or "").strip()
            if spoken:
                self.voice.speak(spoken, tone="instruct")
            return

        if screen_id == "voice_challenge":
            self.voice.speak(WORD_VOICE_QUESTION, tone="instruct")
            return

        if screen_id == "letter_voice_challenge":
            self.voice.speak(LETTER_VOICE_PROMPT, tone="instruct")
            return

        if screen_id == "listening_state":
            if self.state.microphone_test_mode:
                self.voice.speak(self.state.microphone_status_message or "Microphone is ready.", tone="encourage")
            else:
                self.voice.speak("I'm listening.", tone="instruct")
            return

        if screen_id == "letter_listening_state":
            self.voice.speak("I'm listening.", tone="instruct")
            return

        if screen_id == "microphone_check":
            self.voice.speak(self.state.microphone_status_message or MICROPHONE_CHECK_DEFAULT_PROMPT, tone="instruct")
            return

        if screen_id == "bd_practice":
            target_letter = self.state.bd_practice_target or "B"
            self.voice.speak(f"B has a belly. D has a drum. Find {target_letter}.", tone="instruct")
            return

        if screen_id in {VOICE_FALLBACK_SCREEN_ID}:
            spoken = self.state.offline_status_message or get_lumi_speech(screen_id)
            self.voice.speak(spoken, tone="encourage")
            return

        if screen_id == "badge_unlock":
            msg = badge_unlock_speech_message(getattr(self.state, "last_unlocked_badges", None))
            self.voice.speak(msg, tone="celebrate")
            return

        if screen_id == "progress_complete":
            self.voice.speak(get_feedback("level_complete")["message"], tone="celebrate")
            return

        if screen_id == "end_session":
            self.voice.speak(END_SESSION_MESSAGE, tone="celebrate")
            return

        if screen_id == "teacher_report":
            report = self.state.teacher_report or generate_report(self.learner.get_profile())
            recommendation = report.get("recommended_next_activity", "World Map")
            strongest = report.get("strong_skill", "Practice in progress")
            accuracy = report.get("accuracy_percent", 0)
            self.voice.speak(
                f"Report ready. Strongest: {strongest}. Accuracy: {accuracy} percent. Next: {recommendation}.",
                tone="encourage",
            )

    def update(self) -> None:
        self.current_screen.update()
        self._poll_writing_recognition()
        self._update_voice_pronunciation_feedback()
        self._maybe_complete_voice_correct_advance()
        self._maybe_start_scheduled_voice_listen()
        if self.state.answer_popup_kind:
            elapsed = pygame.time.get_ticks() - int(self.state.answer_popup_shown_at_ms or 0)
            duration = HINT_POPUP_DURATION_MS if self.state.answer_popup_kind == "hint" else ANSWER_POPUP_DURATION_MS
            if elapsed >= duration:
                self._resolve_answer_popup()
        if self.state.current_screen_id in IDLE_PRELOAD_SCREEN_IDS:
            budget = 14 if self.state.current_screen_id == "splash_loading" else 8
            if self._preload_queue or self._image_preload_queue:
                self._drain_preload_queue(budget=budget)
        if self.state.current_screen_id == "splash_loading":
            elapsed = pygame.time.get_ticks() - self.state.splash_started_at
            if elapsed >= SPLASH_DURATION_MS:
                self.set_screen("welcome")
        # auto-disable debug overlay after duration expires
        if self.debug_hitboxes and self._debug_enabled_since is not None and not self.state.debug_persistent:
            now = pygame.time.get_ticks()
            if now - self._debug_enabled_since > self._debug_duration_ms:
                self.debug_hitboxes = False
                self._debug_enabled_since = None
                print("[DEBUG] Hitbox overlay auto-disabled")

    def stop(self) -> None:
        self.sound.stop()
        self.voice.shutdown()

    def draw(self) -> None:
        debug_mode = bool(DEBUG_HITBOXES or self.debug_hitboxes)
        self.current_screen.draw(self.screen, debug_hitboxes=debug_mode)
        if debug_mode:
            # draw a small translucent overlay with label and timer
            try:
                font = pygame.font.SysFont(None, 20)
                overlay_surf = pygame.Surface((260, 28), pygame.SRCALPHA)
                overlay_surf.fill((0, 0, 0, 120))
                txt = "HITBOXES: ON"
                if self._debug_enabled_since is not None:
                    remaining = max(0, int((self._debug_duration_ms - (pygame.time.get_ticks() - self._debug_enabled_since)) / 1000))
                    txt = f"HITBOXES: ON ({remaining}s)"
                label = font.render(txt, True, (255, 255, 255))
                overlay_surf.blit(label, (8, 6))
                self.screen.blit(overlay_surf, (10, 10))
            except Exception:
                # fonts may not be available in test environments; fail silently
                pass

        screen_id = self.state.current_screen_id
        if screen_id not in IMAGE_ONLY_SCREEN_IDS_NO_CONTROL_OVERLAY:
            try:
                draw_control_button_placeholders(
                    self.screen,
                    list(getattr(self.current_screen, "hitboxes", []) or []),
                    self.control_assets,
                    writing_mode=str(self.state.writing_mode or "letters"),
                )
            except Exception:
                pass
        if screen_id == "world_map":
            try:
                draw_world_map_overlay(
                    self.screen,
                    status_message=self._world_map_status_text(),
                )
            except Exception:
                pass
        # badge_unlock now renders a full celebration card via dynamic layers
        # (panel, title, icon, subtitle, name, Next button) over the app
        # background — no separate overlay needed.
        if screen_id == "microphone_check":
            try:
                status_text = self.state.microphone_status_message or MICROPHONE_CHECK_DEFAULT_PROMPT
                draw_microphone_check_overlay(self.screen, status_text)
            except Exception:
                pass
        if screen_id == VOICE_FALLBACK_SCREEN_ID:
            try:
                draw_offline_overlay(
                    self.screen,
                    self.state.offline_status_message or offline_prompt_text(""),
                )
            except Exception:
                pass
        if screen_id in {
            "letter_voice_challenge",
            "letter_listening_state",
            "voice_challenge",
            "listening_state",
        }:
            try:
                mic_rect = None
                if self._should_show_voice_mic_prompt():
                    mic_rect = mic_hitbox_from_hitboxes(
                        list(getattr(self.current_screen, "hitboxes", []) or [])
                    )
                    if mic_rect is not None:
                        draw_mic_hint_badge(self.screen, mic_rect)
                draw_voice_pronunciation_overlay(
                    self.screen,
                    feedback=self.state.voice_pronunciation_feedback,
                    shown_at_ms=int(self.state.voice_pronunciation_feedback_at_ms or 0),
                )
            except Exception:
                pass

        if self.state.answer_popup_kind:
            try:
                screen_id = str(self.state.current_screen_id or "")
                compact_popup = screen_id == "letter_island_game"
                draw_answer_popup_overlay(
                    self.screen,
                    kind=self.state.answer_popup_kind,
                    message=self.state.answer_popup_message,
                    anchor_y_pct=LETTER_ISLAND_POPUP_ANCHOR_Y_PCT if compact_popup else None,
                    compact=compact_popup,
                )
            except Exception:
                pass

        if self.state.app_loading and self.state.current_screen_id != "writing_castle_game":
            try:
                draw_fullscreen_loading(
                    self.screen,
                    self.state.app_loading_message,
                    started_at_ms=int(self.state.app_loading_started_at or 0),
                )
            except Exception:
                pass

        # show export notification dialog for a few seconds
        try:
            if self.state.last_export_path and self.state.last_export_time_ms:
                now = pygame.time.get_ticks()
                if now - int(self.state.last_export_time_ms) <= int(self.state.export_display_duration_ms or 5000):
                    try:
                        font = pygame.font.SysFont(None, 18)
                        msg = f"Exported hitboxes: {self.state.last_export_path}"
                        label = font.render(msg, True, (255, 255, 255))
                        bg = pygame.Surface((label.get_width() + 12, label.get_height() + 8), pygame.SRCALPHA)
                        bg.fill((0, 0, 0, 180))
                        bg.blit(label, (6, 4))
                        # center near bottom
                        px = (self.screen.get_width() - bg.get_width()) // 2
                        py = int(self.screen.get_height() * 0.88)
                        self.screen.blit(bg, (px, py))
                    except Exception:
                        pass
                else:
                    # clear old path after display duration
                    self.state.last_export_path = None
                    self.state.last_export_time_ms = None
        except Exception:
            pass
