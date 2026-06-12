"""Launch Lumi's Word Adventure from the repository root.

Usage:
    python main.py

The game package lives in ``lumi_word_adventure/``. This wrapper adds that
directory to ``sys.path`` so imports resolve regardless of cwd.
"""
from __future__ import annotations

import sys
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent / "lumi_word_adventure"
if not _APP_DIR.is_dir():
    raise SystemExit(f"Missing application directory: {_APP_DIR}")

if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from main import main  # noqa: E402

if __name__ == "__main__":
    main()
