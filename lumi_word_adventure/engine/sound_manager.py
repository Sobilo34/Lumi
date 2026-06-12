"""Optional background music and feedback sound helpers; failures must never crash the game."""
from __future__ import annotations

from pathlib import Path

import pygame

from config import SOUNDS_DIR

_MUSIC_CANDIDATES = (
    "background.ogg",
    "background.mp3",
    "music.ogg",
    "music.mp3",
    "main_theme.ogg",
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
        self._music_path: Path | None = None
        self._sfx: dict[str, pygame.mixer.Sound] = {}
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

        for filename in _MUSIC_CANDIDATES:
            path = SOUNDS_DIR / filename
            if not path.is_file():
                continue
            try:
                pygame.mixer.music.load(str(path))
                self._music_loaded = True
                self._music_path = path
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

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        if not self._music_loaded:
            return
        try:
            if self._enabled:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.stop()
        except Exception as error:
            print(f"[Lumi Audio] Music playback error: {error}")

    def play_sfx(self, name: str) -> None:
        sound = self._sfx.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except Exception as error:
            print(f"[Lumi Audio] SFX playback error ({name}): {error}")

    def stop(self) -> None:
        if not self._music_loaded:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
