"""Shared trajectory_v1 validation (Track A + Track B)."""

from __future__ import annotations

TRAJECTORY_REQUIRED = ("trajectory_id", "episode_or_task_id", "track", "termination", "steps")


def validate_trajectory_v1_minimal(trace: dict) -> list[str]:
    """Return list of missing required fields for trajectory_v1."""
    missing: list[str] = []
    for field in TRAJECTORY_REQUIRED:
        if field == "steps":
            if field not in trace or trace[field] is None:
                missing.append(field)
        elif not trace.get(field):
            missing.append(field)
    return missing
