import sys
import os
import pytest

# Ensure project root is on sys.path so tests can import local packages when
# pytest is invoked from different working directories/environments.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from voice.voice_checker import check_spoken_answer


def test_exact_match():
    assert check_spoken_answer("cat", "cat") == "correct"


def test_close_match():
    # depending on fuzzy algorithm, this may be 'correct' or 'close'
    res = check_spoken_answer("kat", "cat")
    assert res in ("correct", "close")


def test_incorrect_match():
    assert check_spoken_answer("ball", "apple") == "incorrect"
