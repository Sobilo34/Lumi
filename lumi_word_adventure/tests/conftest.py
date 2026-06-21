"""Shared pytest configuration."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _skip_startup_prewarm() -> None:
    """Keep unit tests fast; prewarm is covered by install + manual play."""
    os.environ["LUMI_SKIP_PREWARM"] = "1"


@pytest.fixture(scope="session", autouse=True)
def _disable_real_tts() -> None:
    """Never drive the real pyttsx3 engine in tests.

    The espeak run loop can deadlock when many speak() calls are queued in
    quick succession, which hangs the whole suite. No test depends on actual
    audio, so we stub engine init so speak() becomes a safe no-op.
    """
    from voice.text_to_speech import TextToSpeech

    def _no_engine(self: TextToSpeech) -> None:
        self._engine = None
        self._available = False

    original = TextToSpeech._initialize_engine
    TextToSpeech._initialize_engine = _no_engine
    try:
        yield
    finally:
        TextToSpeech._initialize_engine = original
