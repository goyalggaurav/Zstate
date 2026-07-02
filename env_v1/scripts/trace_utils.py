#!/usr/bin/env python3
"""Normalize env traces to shared trajectory_v1 contract."""

from __future__ import annotations

import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from shared.trace_utils import validate_trajectory_v1_minimal  # noqa: E402


def enrich_env_trace(trace: dict, scores: dict | None = None) -> dict:
    """
    Add trajectory_v1 fields alongside legacy env trace fields.
    Does not remove legacy keys (episode_id, run_id, mode, tool_log).
    """
    enriched = deepcopy(trace)
    run_id = trace.get("run_id") or trace.get("trajectory_id")
    if not run_id:
        run_id = f"env_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        enriched["run_id"] = run_id

    enriched["trajectory_id"] = trace.get("trajectory_id") or run_id
    enriched["episode_or_task_id"] = trace.get("episode_or_task_id") or trace.get("episode_id")
    enriched["track"] = trace.get("track", "env")

    if scores:
        enriched["reward"] = {
            **scores.get("components", {}),
            "composite_reward": scores.get("composite_reward"),
            "failure_modes": scores.get("failure_modes", []),
        }
        enriched["fractures"] = scores.get("fracture_codes", [])
    elif "fractures" not in enriched:
        enriched["fractures"] = []

    if "reward" not in enriched:
        enriched["reward"] = {}

    return enriched


__all__ = ["enrich_env_trace", "validate_trajectory_v1_minimal"]
