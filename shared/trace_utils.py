"""Shared trajectory_v1 validation (Track A + Track B)."""

from __future__ import annotations

TRAJECTORY_REQUIRED = ("trajectory_id", "episode_or_task_id", "track", "termination", "steps")


def validate_trajectory_v1_minimal(trace: dict) -> list[str]:
    """Return list of missing required fields for trajectory_v1."""
    return [field for field in TRAJECTORY_REQUIRED if not trace.get(field)]
