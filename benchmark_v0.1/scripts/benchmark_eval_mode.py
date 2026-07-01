"""Eval vs dev prompt profiles for live benchmark campaigns."""

from __future__ import annotations

import os


def eval_mode_enabled(explicit: bool | None = None) -> bool:
    """True when live eval should omit task-specific citation cheat-sheets."""
    if explicit is not None:
        return explicit
    value = os.environ.get("BENCHMARK_EVAL_MODE", "").strip().lower()
    return value in ("1", "true", "yes", "on")
