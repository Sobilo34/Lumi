from pathlib import Path

import pytest

from data_loader import DataLoadError, load_default_profile, load_letters, load_sentences, load_vocabulary


def test_load_letters_returns_expected_entries() -> None:
    letters = load_letters()
    assert {entry["letter"] for entry in letters} >= {"A", "B", "C", "D", "E", "F", "I", "P"}


def test_load_vocabulary_returns_expected_words() -> None:
    vocabulary = load_vocabulary()
    assert {entry["word"] for entry in vocabulary} == {"cat", "dog", "sun", "ball", "apple", "boat", "flower"}


def test_load_sentences_returns_expected_sentences() -> None:
    sentences = load_sentences()
    assert len(sentences) == 5
    assert sentences[0]["prompt"].startswith("Build the sentence")


def test_load_default_profile_has_new_schema() -> None:
    profile = load_default_profile()
    assert profile["total_stars"] == 0
    assert profile["current_world"] == "main_menu"
    assert "badges" in profile


def test_missing_file_raises_helpful_error(tmp_path: Path) -> None:
    from data_loader import load_json_file

    with pytest.raises(DataLoadError, match="Missing data file"):
        load_json_file(tmp_path / "missing.json", base_dir=tmp_path)