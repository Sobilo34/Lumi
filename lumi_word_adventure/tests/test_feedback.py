from engine.feedback import get_feedback, get_hint, get_lumi_speech


def test_correct_feedback_is_supportive() -> None:
    feedback = get_feedback(True)
    assert feedback["type"] == "correct"
    assert feedback["message"] == "Great job! You helped Lumi!"


def test_incorrect_feedback_is_supportive() -> None:
    feedback = get_feedback(False)
    assert feedback["type"] == "incorrect"
    assert feedback["message"] == "Good try! Let’s look again."


def test_bd_confusion_feedback_mentions_belly() -> None:
    feedback = get_feedback(False, mistake_type="bd_confusion")
    assert feedback["type"] == "incorrect"
    assert feedback["message"] == "Good try! B has a belly."


def test_word_confusion_feedback_mentions_target() -> None:
    feedback = get_feedback(False, mistake_type="word_confusion", target="dog", selected="cat")
    assert feedback["type"] == "incorrect"
    assert feedback["message"] == "This is dog. A cat says meow."


def test_sentence_order_feedback_starts_with_first_word() -> None:
    feedback = get_feedback(False, mistake_type="sentence_order", target="I see a cat")
    assert feedback["message"] == "Good try! Start with I."


def test_voice_close_feedback_is_gentle() -> None:
    feedback = get_feedback("close")
    assert feedback["type"] == "close"
    assert feedback["message"] == "Almost! I heard something close. Try again."


def test_hint_messages_reflect_activity_and_target() -> None:
    assert get_hint("letter", 1, "B") == "Look for the letter B."
    assert get_hint("word", 2, "cat") == "Look at the first letter in cat."
    assert get_hint("sentence", 3, "I see a cat") == "Take your time with I see a cat."


def test_lumi_speech_matches_screen() -> None:
    assert get_lumi_speech("welcome").startswith("Hello! I’m Lumi")
    assert "offline" in get_lumi_speech("offline_continue").lower()