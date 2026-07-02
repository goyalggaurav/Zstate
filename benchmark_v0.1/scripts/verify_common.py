"""Shared L1 verification helpers."""

from __future__ import annotations


def is_empty_agent_output(values: dict | None) -> bool:
    """True when the agent produced no metric values (e.g. timeout without submit)."""
    if not values:
        return True
    return not any(v is not None for v in values.values())
