from voice.voice_checker import check_answer, normalize_answer


def test_normalize_answer_strips_extra_whitespace() -> None:
    assert normalize_answer("  I   see   a cat  ") == "i see a cat"


def test_check_answer_accepts_exact_match() -> None:
    assert check_answer("apple", "Apple")


def test_check_answer_rejects_unrelated_answer() -> None:
    assert not check_answer("cat", "dog")
