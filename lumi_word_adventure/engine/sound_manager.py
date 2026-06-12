"""Optional background music helper; failures must never crash the game."""
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


class SoundManager:
    def __init__(self) -> None:
        self._music_loaded = False
        self._enabled = False
        self._music_path: Path | None = None
        self._try_load_default_music()

    @property
    def music_available(self) -> bool:
        return self._music_loaded

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

    def stop(self) -> None:
        if not self._music_loaded:
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
