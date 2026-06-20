"""Shared pytest configuration."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _skip_startup_prewarm() -> None:
    """Keep unit tests fast; prewarm is covered by install + manual play."""
    os.environ["LUMI_SKIP_PREWARM"] = "1"
