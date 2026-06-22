"""Project-wide configuration and constants."""
from __future__ import annotations

from pathlib import Path

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
BABY_PINK = "#F4C2C2"

PROJECT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_DIR.parent
SCREEN_SPECS_PATH = WORKSPACE_DIR / "screen_specs.json"
REFERENCE_INTERFACES_DIR = WORKSPACE_DIR / "reference_interfaces"
DATA_DIR = PROJECT_DIR / "data"
PROFILES_DIR = PROJECT_DIR / "profiles"
ASSETS_DIR = PROJECT_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"
UI_CHUNKS_DIR = ASSETS_DIR / "ui_chunks"
UI_CONTROLS_DIR = ASSETS_DIR / "ui_controls"

# Single soft background used across the whole app (kids 2-4 friendly).
# Two pages keep their original art: the start page and the
# "listen, tap and speak" how-to page.
APP_BACKGROUND_PATH = ASSETS_DIR / "app_background.png"
BACKGROUND_EXEMPT_SCREENS = frozenset({"splash_loading", "welcome", "how_to_play", "main_menu"})

LETTER_VOICE_PROMPT = "What letter is this?"
LETTER_CORRECT_SPEECH = "Correct"

DEBUG_HITBOXES = False
VOICE_ENABLED_DEFAULT = True
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 3
DEFAULT_DIFFICULTY = 1
MAX_STARS = 3
VOICE_FALLBACK_SCREEN_ID = "offline_continue"
VOICE_FALLBACK_MESSAGE = "Continue offline"
OFFLINE_WINDOW_CAPTION = "Lumi's Word Adventure - Offline Mode"
DEFAULT_WINDOW_CAPTION = "Lumi's Word Adventure"
SPLASH_DURATION_MS = 1750

# Teacher report (24_teacher_report.png) dynamic overlay tuning at 1280x720.
# Positions are normalized (x, y) anchors for value text inside the reference cards.
TEACHER_REPORT_OVERLAY_COLOR = (72, 58, 88)
TEACHER_REPORT_OVERLAY_PANEL_RGBA = (255, 255, 255, 205)
TEACHER_REPORT_OVERLAY_FONT_VALUE = 22
TEACHER_REPORT_OVERLAY_FONT_LABEL = 17
TEACHER_REPORT_OVERLAY_LINE_GAP = 6
TEACHER_REPORT_OVERLAY_POSITIONS: dict[str, tuple[float, float]] = {
    "stars_earned": (0.30, 0.205),
    "accuracy_percent": (0.30, 0.335),
    "strong_skill": (0.30, 0.465),
    "needs_practice": (0.30, 0.595),
    "recommended_next_activity": (0.70, 0.655),
}
# Recommended-practice hitbox aligned to the callout card on the reference PNG.
TEACHER_REPORT_PRACTICE_HITBOX = (0.60, 0.60, 0.28, 0.25)

# Settings screen (25_settings.png) overlay tuning at 1280x720.
SETTINGS_OVERLAY_COLOR = (72, 58, 88)
SETTINGS_OVERLAY_PANEL_RGBA = (255, 255, 255, 205)
SETTINGS_OVERLAY_POSITION = (0.12, 0.70)
SETTINGS_STATUS_OVERLAY_POSITION = (0.28, 0.84)
SETTINGS_STATUS_DISPLAY_MS = 3500
WORLD_MAP_STATUS_DISPLAY_MS = 3500
SETTINGS_DEV_ACTIONS = frozenset(
    {
        "export_hitboxes",
        "decrease_smoke",
        "increase_smoke",
        "toggle_hitbox_persistent",
        "run_hitbox_smoke",
    }
)

# Microphone check screen (26_microphone_check.png) overlay tuning at 1280x720.
MICROPHONE_CHECK_OVERLAY_COLOR = (72, 58, 88)
MICROPHONE_CHECK_OVERLAY_PANEL_RGBA = (255, 255, 255, 210)
MICROPHONE_CHECK_OVERLAY_POSITION = (0.06, 0.78)
MICROPHONE_CHECK_DEFAULT_PROMPT = "Tap Test Mic to check your microphone."

# Offline continue screen (28_continue_offline.png) overlay tuning at 1280x720.
OFFLINE_OVERLAY_COLOR = (72, 58, 88)
OFFLINE_OVERLAY_PANEL_RGBA = (255, 255, 255, 210)
OFFLINE_OVERLAY_POSITION = (0.36, 0.52)

END_SESSION_MESSAGE = "You did great!"
