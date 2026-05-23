from voice.text_to_speech import TextToSpeech


def test_text_to_speech_safe_methods_do_not_crash() -> None:
    tts = TextToSpeech(enabled=False, rate=120)

    assert tts.speak("Hello Lumi") is False

    tts.set_rate(130)
    tts.set_enabled(True)
    tts.stop()
