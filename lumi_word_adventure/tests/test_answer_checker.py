import pytest

import voice.speech_to_text
from voice.voice_checker import check_answer, check_spoken_answer, guess_spoken_letter, normalize_answer


def test_normalize_answer_strips_extra_whitespace() -> None:
    assert normalize_answer("  I   see   a cat  ") == "i see a cat"


def test_check_answer_accepts_exact_match() -> None:
    assert check_answer("apple", "Apple")


def test_check_answer_rejects_unrelated_answer() -> None:
    assert not check_answer("cat", "dog")


def test_guess_spoken_letter_maps_phonetic_names() -> None:
    assert guess_spoken_letter("gee") == "g"
    assert guess_spoken_letter("bee") == "b"
    assert guess_spoken_letter("letter m") == "m"
    assert guess_spoken_letter("the g") == "g"


def test_check_spoken_answer_accepts_letter_phonetic_name() -> None:
    assert check_spoken_answer("gee", "G") == "correct"
    assert check_spoken_answer("em", "M") == "correct"
    assert check_spoken_answer("the g", "G") == "correct"


def test_vosk_ready_with_pyaudio_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("voice.speech_to_text.VOSK_AVAILABLE", True)
    monkeypatch.setattr("voice.speech_to_text.VOSK_MODEL_PATH", "/tmp/model")
    monkeypatch.setattr("voice.speech_to_text.SD_AVAILABLE", False)
    monkeypatch.setattr("voice.speech_to_text._probe_pyaudio", lambda: True)
    assert voice.speech_to_text._vosk_ready() is True


def test_check_spoken_answer_accepts_word_match() -> None:
    assert check_spoken_answer("cat", "cat") == "correct"
