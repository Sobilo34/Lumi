"""Background music and feedback SFX; music ducks under TTS, mic, and SFX."""
from __future__ import annotations

import threading
from pathlib import Path

import pygame

from config import (
    BACKGROUND_MUSIC_DUCK_VOLUME,
    BACKGROUND_MUSIC_FILE,
    BACKGROUND_MUSIC_NORMAL_VOLUME,
    SOUNDS_DIR,
)

_SFX_FILES = {
    "correct": "correct.wav",
    "wrong": "wrong.wav",
    "star": "star.wav",
    "badge": "badge.wav",
}


class SoundManager:
    def __init__(self) -> None:
        self._music_loaded = False
        self._enabled = False
        self._playback_allowed = False
        self._music_path: Path | None = None
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._duck_counts: dict[str, int] = {}
        self._ensure_default_sfx()
        self._try_load_default_music()
        self._load_sfx()

    @property
    def music_available(self) -> bool:
        return self._music_loaded

    def _ensure_default_sfx(self) -> None:
        try:
            from engine.sfx_generator import generate_default_sfx

            generate_default_sfx(SOUNDS_DIR)
        except Exception as error:
            print(f"[Lumi Audio] Could not generate default SFX: {error}")

    def _try_load_default_music(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as error:
            print(f"[Lumi Audio] Mixer unavailable: {error}")
            return

        candidates = (BACKGROUND_MUSIC_FILE, "background.ogg", "background.mp3", "music.ogg", "music.mp3")
        seen: set[str] = set()
        for filename in candidates:
            if filename in seen:
                continue
            seen.add(filename)
            path = SOUNDS_DIR / filename
            if not path.is_file():
                continue
            try:
                pygame.mixer.music.load(str(path))
                self._music_loaded = True
                self._music_path = path
                pygame.mixer.music.set_volume(BACKGROUND_MUSIC_NORMAL_VOLUME)
                print(f"[Lumi Audio] Background music loaded: {path.name}")
                return
            except Exception as error:
                print(f"[Lumi Audio] Could not load '{path.name}': {error}")

    def _load_sfx(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            return

        for name, filename in _SFX_FILES.items():
            path = SOUNDS_DIR / filename
            if not path.is_file():
                continue
            try:
                self._sfx[name] = pygame.mixer.Sound(str(path))
            except Exception as error:
                print(f"[Lumi Audio] Could not load SFX '{filename}': {error}")

    def _sync_playback(self) -> None:
        if not self._music_loaded:
            return
        try:
            should_play = bool(self._enabled and self._playback_allowed)
            if should_play:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                self._apply_volume()
            else:
                pygame.mixer.music.stop()
        except Exception as error:
            print(f"[Lumi Audio] Music playback error: {error}")

    def allow_background_playback(self) -> None:
        """Start looping background music after the welcome screen (if music is enabled)."""
        if self._playback_allowed:
            return
        self._playback_allowed = True
        self._sync_playback()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self._sync_playback()

    def duck(self, reason: str) -> None:
        if not self._music_loaded or not self._enabled or not self._playback_allowed:
            return
        key = str(reason or "other").strip().lower() or "other"
        self._duck_counts[key] = self._duck_counts.get(key, 0) + 1
        self._apply_volume()

    def unduck(self, reason: str) -> None:
        if not self._music_loaded:
            return
        key = str(reason or "other").strip().lower() or "other"
        current = self._duck_counts.get(key, 0)
        if current <= 1:
            self._duck_counts.pop(key, None)
        else:
            self._duck_counts[key] = current - 1
        self._apply_volume()

    def _apply_volume(self) -> None:
        if not self._music_loaded:
            return
        try:
            if not pygame.mixer.music.get_busy():
                return
            volume = (
                BACKGROUND_MUSIC_DUCK_VOLUME
                if any(count > 0 for count in self._duck_counts.values())
                else BACKGROUND_MUSIC_NORMAL_VOLUME
            )
            pygame.mixer.music.set_volume(volume)
        except Exception as error:
            print(f"[Lumi Audio] Volume update error: {error}")

    def play_sfx(self, name: str) -> None:
        sound = self._sfx.get(name)
        if sound is None:
            return
        try:
            self.duck("sfx")
            sound.play()
            length_ms = int(sound.get_length() * 1000)
            delay = max(0.12, (length_ms / 1000.0) + 0.05)

            def _release() -> None:
                self.unduck("sfx")

            threading.Timer(delay, _release).start()
        except Exception as error:
            self.unduck("sfx")
            print(f"[Lumi Audio] SFX playback error ({name}): {error}")

    def stop(self) -> None:
        if not self._music_loaded:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
