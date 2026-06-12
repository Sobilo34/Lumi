"""Local settings persistence for Lumi's Word Adventure."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
from typing import Any

from config import PROFILES_DIR

SETTINGS_FILENAME = "settings.json"
DIFFICULTY_MODES = ("Easy", "Medium", "Hard")
DEFAULT_SETTINGS: dict[str, Any] = {
    "music_enabled": True,
    "voice_enabled": True,
    "difficulty_mode": "Medium",
    "debug_hitboxes": False,
}


def _settings_path(path: Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return PROFILES_DIR / SETTINGS_FILENAME


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _normalize_difficulty_mode(value: Any) -> str:
    if isinstance(value, str):
        cleaned = value.strip().capitalize()
        if cleaned in DIFFICULTY_MODES:
            return cleaned
        if cleaned.isdigit():
            index = int(cleaned)
            if 1 <= index <= len(DIFFICULTY_MODES):
                return DIFFICULTY_MODES[index - 1]
    if isinstance(value, int) and 1 <= value <= len(DIFFICULTY_MODES):
        return DIFFICULTY_MODES[value - 1]
    return str(DEFAULT_SETTINGS["difficulty_mode"])


def normalize_settings(raw_settings: dict[str, Any] | None) -> dict[str, Any]:
    """Return a safe settings dict, filling invalid or missing values."""
    source = raw_settings if isinstance(raw_settings, dict) else {}
    defaults = deepcopy(DEFAULT_SETTINGS)
    return {
        "music_enabled": _coerce_bool(source.get("music_enabled"), bool(defaults["music_enabled"])),
        "voice_enabled": _coerce_bool(source.get("voice_enabled"), bool(defaults["voice_enabled"])),
        "difficulty_mode": _normalize_difficulty_mode(source.get("difficulty_mode", defaults["difficulty_mode"])),
        "debug_hitboxes": _coerce_bool(source.get("debug_hitboxes"), bool(defaults["debug_hitboxes"])),
    }


def difficulty_mode_to_level(difficulty_mode: str) -> int:
    normalized = _normalize_difficulty_mode(difficulty_mode)
    return DIFFICULTY_MODES.index(normalized) + 1


def level_to_difficulty_mode(level: int) -> str:
    if 1 <= int(level) <= len(DIFFICULTY_MODES):
        return DIFFICULTY_MODES[int(level) - 1]
    return str(DEFAULT_SETTINGS["difficulty_mode"])


class SettingsManager:
    def __init__(self, settings_path: str | Path | None = None) -> None:
        self.settings_path = _settings_path(Path(settings_path) if settings_path is not None else None)
        self._settings = self.load_settings()

    def load_settings(self) -> dict[str, Any]:
        path = self.settings_path
        path.parent.mkdir(parents=True, exist_ok=True)

        if not path.exists():
            self._settings = normalize_settings(DEFAULT_SETTINGS)
            self.save_settings(self._settings)
            return deepcopy(self._settings)

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            payload = {}

        normalized = normalize_settings(payload if isinstance(payload, dict) else {})
        self._settings = normalized
        if normalized != payload:
            self.save_settings(normalized)
        return deepcopy(self._settings)

    def save_settings(self, settings: dict[str, Any]) -> None:
        normalized = normalize_settings(settings)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2, ensure_ascii=False)
        self._settings = normalized

    def toggle_music(self) -> bool:
        settings = self.load_settings()
        settings["music_enabled"] = not bool(settings["music_enabled"])
        self.save_settings(settings)
        return bool(settings["music_enabled"])

    def toggle_voice(self) -> bool:
        settings = self.load_settings()
        settings["voice_enabled"] = not bool(settings["voice_enabled"])
        self.save_settings(settings)
        return bool(settings["voice_enabled"])

    def cycle_difficulty(self) -> str:
        settings = self.load_settings()
        current = _normalize_difficulty_mode(settings["difficulty_mode"])
        next_index = (DIFFICULTY_MODES.index(current) + 1) % len(DIFFICULTY_MODES)
        settings["difficulty_mode"] = DIFFICULTY_MODES[next_index]
        self.save_settings(settings)
        return settings["difficulty_mode"]

    def reset_settings(self) -> dict[str, Any]:
        self.save_settings(deepcopy(DEFAULT_SETTINGS))
        return deepcopy(self._settings)


_default_manager: SettingsManager | None = None


def _default() -> SettingsManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = SettingsManager()
    return _default_manager


def load_settings() -> dict[str, Any]:
    return _default().load_settings()


def save_settings(settings: dict[str, Any]) -> None:
    _default().save_settings(settings)


def toggle_music() -> bool:
    return _default().toggle_music()


def toggle_voice() -> bool:
    return _default().toggle_voice()


def cycle_difficulty() -> str:
    return _default().cycle_difficulty()


def reset_settings() -> dict[str, Any]:
    return _default().reset_settings()
