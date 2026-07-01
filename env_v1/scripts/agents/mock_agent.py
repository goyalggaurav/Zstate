"""Deterministic weak agent for offline adapter tests (no API key)."""

from __future__ import annotations

from typing import Any


class MockWeakAgent:
    """Skips prior-year footnotes — triggers partial failure pattern."""

    plan_id = "mock_weak_v1"

    def __init__(self) -> None:
        self._step = 0
        self._actions: list[dict] = [
            {"type": "tool_call", "tool": "get_filing", "input": {"doc_type": "10-Q", "period": "2025Q2"}},
            {"type": "tool_call", "tool": "get_consensus", "input": {"metric": "eps", "period": "2025Q2"}},
            {"type": "tool_call", "tool": "calculator", "input": {"expression": "1.42 - 0.18 - 0.04"}},
            {
                "type": "send_message_to_pm",
                "text": "Adjusted EPS $1.20. I exclude the $0.18 sale-leaseback and $0.04 R&D credit per the 10-Q.",
            },
            {
                "type": "submit_recommendation",
                "adjusted_eps": 1.20,
                "classification": "exclude_both_one_time_items",
                "rationale": "Excluded per 10-Q reconciliation only.",
                "sale_leaseback_excluded": True,
                "rd_credit_treatment": "exclude_one_time",
                "submitted": True,
            },
        ]

    def next_action(self, _context: dict[str, Any]) -> dict | None:
        if self._step >= len(self._actions):
            return None
        action = self._actions[self._step]
        self._step += 1
        return action
