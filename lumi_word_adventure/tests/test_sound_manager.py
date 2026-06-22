"""Tests for background music ducking and welcome-screen start gate."""
from __future__ import annotations

import os
from pathlib import Path

import pygame
import pytest

from config import BACKGROUND_MUSIC_DUCK_VOLUME, BACKGROUND_MUSIC_NORMAL_VOLUME
from engine.sound_manager import SoundManager


@pytest.fixture(autouse=True)
def _init_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    if not pygame.get_init():
        pygame.init()
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()


def test_background_music_ducks_and_restores(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    music = tmp_path / "background.mp3"
    music.write_bytes(b"not-real-mp3")
    monkeypatch.setattr("engine.sound_manager.SOUNDS_DIR", tmp_path)
    monkeypatch.setattr("engine.sound_manager.BACKGROUND_MUSIC_FILE", "background.mp3")

    volumes: list[float] = []

    def _set_volume(value: float) -> None:
        volumes.append(float(value))

    monkeypatch.setattr("pygame.mixer.music.set_volume", _set_volume)
    monkeypatch.setattr("pygame.mixer.music.load", lambda _path: None)
    monkeypatch.setattr("pygame.mixer.music.get_busy", lambda: True)
    monkeypatch.setattr("pygame.mixer.music.play", lambda loops=-1: None)
    monkeypatch.setattr("pygame.mixer.music.stop", lambda: None)

    manager = SoundManager()
    manager.allow_background_playback()
    manager.set_enabled(True)
    manager.duck("tts")
    assert volumes[-1] == pytest.approx(BACKGROUND_MUSIC_DUCK_VOLUME)
    manager.unduck("tts")
    assert volumes[-1] == pytest.approx(BACKGROUND_MUSIC_NORMAL_VOLUME)


def test_background_music_waits_until_playback_allowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    music = tmp_path / "background.mp3"
    music.write_bytes(b"not-real-mp3")
    monkeypatch.setattr("engine.sound_manager.SOUNDS_DIR", tmp_path)
    monkeypatch.setattr("engine.sound_manager.BACKGROUND_MUSIC_FILE", "background.mp3")

    play_calls: list[int] = []
    monkeypatch.setattr("pygame.mixer.music.load", lambda _path: None)
    monkeypatch.setattr("pygame.mixer.music.get_busy", lambda: False)
    monkeypatch.setattr("pygame.mixer.music.play", lambda loops=-1: play_calls.append(loops))
    monkeypatch.setattr("pygame.mixer.music.stop", lambda: None)
    monkeypatch.setattr("pygame.mixer.music.set_volume", lambda _value: None)

    manager = SoundManager()
    manager.set_enabled(True)
    assert play_calls == []
    manager.allow_background_playback()
    assert play_calls == [-1]
