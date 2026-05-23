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
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 3
DEFAULT_DIFFICULTY = 1
MAX_STARS = 3
VOICE_FALLBACK_SCREEN_ID = "offline_continue"
VOICE_FALLBACK_MESSAGE = "Continue offline"
SPLASH_DURATION_MS = 1750
