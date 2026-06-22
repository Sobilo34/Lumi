"""CLI entry for subprocess handwriting recognition (JSON on stdout)."""
from __future__ import annotations

import json
import sys

import cv2

from writing_recognition.process_image import recognize_letters, recognize_word


def main() -> int:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "usage: _cli.py <snapshot> <letters|words> [board_out]"}))
        return 1
    snapshot = sys.argv[1]
    mode = str(sys.argv[2]).strip().lower()
    board_out = sys.argv[3] if len(sys.argv) > 3 else ""

    if mode == "letters":
        board, results = recognize_letters(snapshot, single=True)
        recognized = str(results[0]["letter"]) if results else ""
        hint = str(results[0].get("hint") or "") if results else "No letter detected. Try larger, darker strokes."
    else:
        board, _ = recognize_letters(snapshot, single=False)
        recognized, hint = recognize_word(snapshot)
        if not recognized:
            hint = hint or "Draw the whole word with clear spacing between letters."

    if board_out:
        cv2.imwrite(board_out, board)

    print(
        json.dumps(
            {
                "recognized": recognized,
                "hint": str(hint or ""),
                "mode": mode,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
