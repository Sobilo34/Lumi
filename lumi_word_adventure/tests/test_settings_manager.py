"""Settings manager persistence tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.settings_manager import (
    DEFAULT_SETTINGS,
    SettingsManager,
    difficulty_mode_to_level,
    level_to_difficulty_mode,
    normalize_settings,
)


@pytest.fixture()
def settings_path(tmp_path: Path) -> Path:
    return tmp_path / "settings.json"


def test_missing_settings_file_creates_defaults(settings_path: Path) -> None:
    manager = SettingsManager(settings_path=settings_path)

    assert settings_path.exists()
    assert manager.load_settings() == DEFAULT_SETTINGS


def test_toggle_music_flips_and_saves(settings_path: Path) -> None:
    manager = SettingsManager(settings_path=settings_path)
    assert manager.toggle_music() is False

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved["music_enabled"] is False
    assert manager.load_settings()["music_enabled"] is False


def test_toggle_voice_flips_and_saves(settings_path: Path) -> None:
    manager = SettingsManager(settings_path=settings_path)
    assert manager.toggle_voice() is False

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert saved["voice_enabled"] is False


def test_cycle_difficulty_medium_hard_easy_medium(settings_path: Path) -> None:
    manager = SettingsManager(settings_path=settings_path)

    assert manager.load_settings()["difficulty_mode"] == "Medium"
    assert manager.cycle_difficulty() == "Hard"
    assert manager.cycle_difficulty() == "Easy"
    assert manager.cycle_difficulty() == "Medium"


def test_reset_settings_returns_defaults(settings_path: Path) -> None:
    manager = SettingsManager(settings_path=settings_path)
    manager.toggle_music()
    manager.toggle_voice()
    manager.cycle_difficulty()

    reset = manager.reset_settings()
    assert reset == DEFAULT_SETTINGS
    assert json.loads(settings_path.read_text(encoding="utf-8")) == DEFAULT_SETTINGS


def test_invalid_settings_values_are_safely_corrected(settings_path: Path) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(
            {
                "music_enabled": "yes",
                "voice_enabled": 0,
                "difficulty_mode": "Hardcore",
                "debug_hitboxes": "off",
            }
        ),
        encoding="utf-8",
    )

    manager = SettingsManager(settings_path=settings_path)
    normalized = manager.load_settings()

    assert normalized["music_enabled"] is True
    assert normalized["voice_enabled"] is False
    assert normalized["difficulty_mode"] == "Medium"
    assert normalized["debug_hitboxes"] is False


def test_difficulty_mode_level_mapping() -> None:
    assert difficulty_mode_to_level("Easy") == 1
    assert difficulty_mode_to_level("Medium") == 2
    assert difficulty_mode_to_level("Hard") == 3
    assert level_to_difficulty_mode(2) == "Medium"


def test_normalize_settings_handles_missing_profiles_dir(tmp_path: Path) -> None:
    nested = tmp_path / "new_profiles" / "settings.json"
    manager = SettingsManager(settings_path=nested)
    settings = manager.load_settings()

    assert nested.exists()
    assert settings == DEFAULT_SETTINGS


def test_invalid_json_falls_back_to_defaults(settings_path: Path) -> None:
    settings_path.write_text("{not valid", encoding="utf-8")
    manager = SettingsManager(settings_path=settings_path)

    assert manager.load_settings() == DEFAULT_SETTINGS
    assert json.loads(settings_path.read_text(encoding="utf-8")) == DEFAULT_SETTINGS


def test_normalize_settings_helper() -> None:
    assert normalize_settings(None) == DEFAULT_SETTINGS
    assert normalize_settings({"difficulty_mode": "hard"})["difficulty_mode"] == "Hard"
