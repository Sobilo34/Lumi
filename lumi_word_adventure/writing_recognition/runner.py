"""Run handwriting recognition in-process or via RealTime venv subprocess."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _PACKAGE_DIR.parent


@dataclass(frozen=True)
class RecognitionOutcome:
    recognized: str
    hint: str
    board_path: str = ""
    backend: str = "local"


def _realtime_python_candidates() -> list[Path]:
    env_path = os.environ.get("LUMI_WRITING_PYTHON", "").strip()
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    sibling = _PROJECT_DIR.parent.parent / "RealTime-DigitRecognition" / "myvenv" / "bin" / "python"
    candidates.append(sibling)
    candidates.append(Path.home() / "bilal_projects" / "Learning" / "AIU" / "python" / "RealTime-DigitRecognition" / "myvenv" / "bin" / "python")
    return [path for path in candidates if path.is_file()]


def fallback_python() -> Path | None:
    for path in _realtime_python_candidates():
        try:
            probe = subprocess.run(
                [str(path), "-c", "from tf_keras.models import load_model"],
                capture_output=True,
                timeout=30,
                check=False,
            )
            if probe.returncode == 0:
                return path
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def recognition_available() -> bool:
    try:
        from writing_recognition.process_image import recognition_available as local_ready

        if local_ready():
            return True
    except Exception:
        pass
    return fallback_python() is not None


def recognition_error_message() -> str:
    try:
        from writing_recognition import process_image as proc

        if proc._load_error:
            return str(proc._load_error)
    except Exception:
        pass
    if fallback_python() is None:
        return "TensorFlow is not installed in this environment."
    return ""


def warm_recognition_model() -> None:
    """Load the CNN once so the first Verify click feels instant."""
    python = fallback_python()
    if python is None:
        try:
            from writing_recognition.process_image import _ensure_model

            _ensure_model()
        except Exception:
            pass
        return
    model_path = _PACKAGE_DIR / "cnn_model" / "letter_classifier.h5"
    script = (
        "from tf_keras.models import load_model; "
        f"load_model({str(model_path)!r}); "
        "print('ready')"
    )
    try:
        subprocess.run(
            [str(python), "-c", script],
            cwd=str(_PROJECT_DIR),
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def recognize_snapshot(snapshot: Path, mode: str, *, board_out: Path | None = None, expected_letter: str = "") -> RecognitionOutcome:
    mode_key = "words" if str(mode).strip().lower() == "words" else "letters"
    board_path = board_out or (_PACKAGE_DIR / ".recognition_board.png")
    expected = str(expected_letter or "").strip()
    expected_letter_arg = expected.upper() if mode_key == "letters" and len(expected) == 1 else ""
    expected_word_arg = expected.lower() if mode_key == "words" else ""

    try:
        from writing_recognition.process_image import recognition_available as local_ready
        from writing_recognition.process_image import recognize_letters, recognize_word

        if local_ready():
            if mode_key == "letters":
                board, results = recognize_letters(str(snapshot), single=True, expected_letter=expected_letter_arg)
                recognized = str(results[0]["letter"]) if results else ""
                hint = str(results[0].get("hint") or "") if results else "No letter detected. Try larger, darker strokes."
            else:
                board, _ = recognize_letters(str(snapshot), single=False)
                recognized, hint = recognize_word(str(snapshot), expected_word=expected_word_arg)
                if not recognized:
                    hint = hint or "Draw the whole word with clear spacing between letters."
            import cv2

            cv2.imwrite(str(board_path), board)
            return RecognitionOutcome(recognized=recognized, hint=str(hint or ""), board_path=str(board_path), backend="local")
    except Exception:
        pass

    python = fallback_python()
    if python is None:
        raise RuntimeError(recognition_error_message() or "Handwriting recognition is not available.")

    expected_for_cli = expected_letter_arg or expected_word_arg
    cmd = [
        str(python),
        "-m",
        "writing_recognition._cli",
        str(snapshot),
        mode_key,
        str(board_path),
    ]
    if expected_for_cli:
        cmd.append(expected_for_cli)
    completed = subprocess.run(
        cmd,
        cwd=str(_PROJECT_DIR),
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or "Recognition subprocess failed.")

    payload = json.loads(completed.stdout.strip() or "{}")
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return RecognitionOutcome(
        recognized=str(payload.get("recognized") or ""),
        hint=str(payload.get("hint") or ""),
        board_path=str(board_path),
        backend="subprocess",
    )
