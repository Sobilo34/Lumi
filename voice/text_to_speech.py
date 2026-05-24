"""Compatibility proxy for TextToSpeech.

Routes imports to the main implementation under lumi_word_adventure.voice.
"""
from lumi_word_adventure.voice.text_to_speech import TextToSpeech

__all__ = ["TextToSpeech"]
