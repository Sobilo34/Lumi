from pathlib import Path

import pytest

from reports.report_generator import (
    SCREEN_BD_PRACTICE,
    SCREEN_SENTENCE_CASTLE,
    SCREEN_WORD_GARDEN,
    SCREEN_WORLD_MAP,
    calculate_accuracy,
    generate_report,
    get_recommendation,
    get_strong_skill,
    get_weak_area,
    resolve_engine_screen_id,
    save_session_report,
)


def _rich_profile() -> dict:
    return {
        "child_name": "Amina",
        "total_stars": 12,
        "attempts": 10,
        "correct_answers": 8,
        "mastered_letters": ["A", "B", "C", "D"],
        "mastered_words": ["cat", "dog"],
        "weak_letters": {"B": 3, "D": 2},
        "weak_words": {"cat": 4},
        "sentence_errors": {"word_order": 1},
    }


def test_report_helpers_identify_skills_and_recommendation() -> None:
    profile = _rich_profile()

    assert get_strong_skill(profile) == "Letter recognition"
    assert get_weak_area(profile) == "Letters B and D"
    assert get_recommendation(profile) == {
        "activity": "B/D Practice",
        "screen_id": SCREEN_BD_PRACTICE,
    }


def test_calculate_accuracy_from_profile() -> None:
    assert calculate_accuracy({"attempts": 10, "correct_answers": 8}) == 80
    assert calculate_accuracy({"attempts": 0, "accuracy": 55.6}) == 56
    assert calculate_accuracy({}) == 0


@pytest.mark.parametrize(
    ("profile", "expected_screen"),
    [
        ({"weak_letters": {"B": 2, "D": 1}}, SCREEN_BD_PRACTICE),
        ({"weak_letters": {"D": 2}}, SCREEN_BD_PRACTICE),
        ({"weak_letters": {"B": 1}, "weak_words": {"cat": 2}}, SCREEN_WORD_GARDEN),
        ({"sentence_errors": {"word_order": 1}}, SCREEN_SENTENCE_CASTLE),
        ({}, SCREEN_WORLD_MAP),
    ],
)
def test_recommendation_rules(profile: dict, expected_screen: str) -> None:
    recommendation = get_recommendation(profile)
    assert recommendation["screen_id"] == expected_screen


def test_generate_report_writes_session_json(tmp_path: Path) -> None:
    output_path = tmp_path / "custom_report.json"
    report = generate_report(_rich_profile(), output_path=output_path)

    assert output_path.exists()
    assert report["child_name"] == "Amina"
    assert report["stars_earned"] == 12
    assert report["accuracy_percent"] == 80
    assert report["strong_skill"] == "Letter recognition"
    assert report["needs_practice"] == "Letters B and D"
    assert report["weak_letters"] == {"B": 3, "D": 2}
    assert report["weak_words"] == {"cat": 4}
    assert report["sentence_errors"] == {"word_order": 1}
    assert report["recommended_next_activity"] == "B/D Practice"
    assert report["recommended_screen_id"] == SCREEN_BD_PRACTICE
    assert report["generated_at"]
    assert report["session_report_path"] == str(output_path)


def test_save_session_report_default_filename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("reports.report_generator.SESSION_REPORTS_DIR", tmp_path)
    report = {"child_name": "Player 1", "stars_earned": 1}
    path = save_session_report(report)

    assert Path(path).exists()
    assert Path(path).name.startswith("session_report_")
    assert Path(path).suffix == ".json"


def test_resolve_engine_screen_id_maps_mcp_ids() -> None:
    assert resolve_engine_screen_id(SCREEN_BD_PRACTICE) == "bd_practice"
    assert resolve_engine_screen_id(SCREEN_WORD_GARDEN) == "word_garden_game"
    assert resolve_engine_screen_id(SCREEN_SENTENCE_CASTLE) == "sentence_castle_game"
    assert resolve_engine_screen_id(SCREEN_WORLD_MAP) == "world_map"
