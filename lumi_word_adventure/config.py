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

DEBUG_HITBOXES = False
VOICE_ENABLED_DEFAULT = True
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 3
DEFAULT_DIFFICULTY = 1
MAX_STARS = 3
VOICE_FALLBACK_SCREEN_ID = "offline_continue"
VOICE_FALLBACK_MESSAGE = "Continue offline"
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
