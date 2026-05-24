from pathlib import Path

from reports.report_generator import (
    generate_report,
    get_recommendation,
    get_strong_skill,
    get_weak_area,
)


def test_report_helpers_identify_skills_and_recommendation() -> None:
    profile = {
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

    assert get_strong_skill(profile) == "Letter recognition"
    assert get_weak_area(profile) == "Letters B and D"
    assert get_recommendation(profile) == "Practice B/D"


def test_generate_report_writes_session_json(tmp_path: Path) -> None:
    profile = {
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

    output_path = tmp_path / "custom_report.json"
    report = generate_report(profile, output_path=output_path)

    assert output_path.exists()
    assert report["child_name"] == "Amina"
    assert report["stars"] == 12
    assert report["accuracy"] == 80.0
    assert report["recommended_next_activity"] == "Practice B/D"
    assert report["session_report_path"] == str(output_path)