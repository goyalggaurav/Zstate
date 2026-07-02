"""Weak mock agents for all published Track A tasks (P3-16)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent.parent
BENCH = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import l1_values_from_gt  # noqa: E402

PLAN_ID = "mock_weak_v1"


def _period_for_task(task: dict) -> str:
    return task["required_documents"][0]["fiscal_period"]


def _search(ticker: str, period: str, section: str) -> dict:
    return {
        "type": "tool_call",
        "tool": "Search_Filing",
        "input": {"ticker": ticker, "period": period, "section": section},
    }


def _python(expression: str) -> dict:
    return {
        "type": "tool_call",
        "tool": "Python_Interpreter",
        "input": {"expression": expression},
    }


def _submit(structured_output: dict) -> dict:
    return {
        "type": "submit_structured_output",
        "structured_output": structured_output,
    }


class ScriptedWeakMockAgent:
    """Replay a fixed weak tool sequence ending in an intentional L1 failure."""

    plan_id = PLAN_ID

    def __init__(self, actions: list[dict]) -> None:
        self._actions = actions
        self._step = 0

    def next_action(self, _context: dict[str, Any]) -> dict | None:
        if self._step >= len(self._actions):
            return None
        action = self._actions[self._step]
        self._step += 1
        return action


def _googl_actions(task: dict) -> list[dict]:
    ticker = task["ticker"]
    period = _period_for_task(task)
    return [
        _search(ticker, period, "segment_financials"),
        _search(ticker, period, "revenue_disaggregation"),
        _python("89637 + 20028 + 411"),
        _submit({
            "google_services_revenue": 89_637,
            "google_cloud_revenue": 20_028,
            "other_bets_revenue": 411,
            "hedging_gains_losses": None,
            "consolidated_total_revenue": 110_076,
            "segment_sum": 110_076,
            "reconciling_item_amount": None,
        }),
    ]


def _pep_actions(task: dict) -> list[dict]:
    ticker = task["ticker"]
    period = _period_for_task(task)
    trap_path = BENCH / "contract_fixtures" / "PEP_fx_organic_growth_trap_pep_reported_only.json"
    values = json.loads(trap_path.read_text(encoding="utf-8"))
    return [
        _search(ticker, period, "segment_financials"),
        _search(ticker, period, "narrative_fx"),
        _python("8.0"),
        _submit(values),
    ]


def _amzn_actions(task: dict) -> list[dict]:
    ticker = task["ticker"]
    period = _period_for_task(task)
    values = l1_values_from_gt("AMZN_footnote_reconciliation")
    values["international_reported_growth_pct"] = 10.0
    values["international_cc_growth_pct"] = 13.0
    return [
        _search(ticker, period, "segment_financials"),
        _search(ticker, period, "narrative_fx"),
        _python("426305 + 161894 + 128725"),
        _submit(values),
    ]


def _nflx_actions(task: dict) -> list[dict]:
    ticker = task["ticker"]
    values = l1_values_from_gt("NFLX_guidance_drift")
    values["ytd_content_cash_payments_usd_m"] = 11_658
    return [
        _search(ticker, "2024Q4", "narrative_guidance"),
        _search(ticker, "2025Q3", "quantitative_actuals"),
        _python("11658"),
        _submit(values),
    ]


def _ko_actions(task: dict) -> list[dict]:
    ticker = task["ticker"]
    period = _period_for_task(task)
    trap_path = BENCH / "contract_fixtures" / "KO_footnote_reconciliation_trap_ko_omit_bottling.json"
    values = json.loads(trap_path.read_text(encoding="utf-8"))
    return [
        _search(ticker, period, "segment_financials"),
        _search(ticker, period, "consolidated_primary"),
        _python("11513 + 6334 + 19586 + 5638 + 144 - 1009"),
        _submit(values),
    ]


_MOCK_BUILDERS = {
    "GOOGL_footnote_reconciliation": _googl_actions,
    "PEP_fx_organic_growth": _pep_actions,
    "AMZN_footnote_reconciliation": _amzn_actions,
    "NFLX_guidance_drift": _nflx_actions,
    "KO_footnote_reconciliation": _ko_actions,
}

EXPECTED_MOCK_FRACTURES: dict[str, set[str]] = {
    "GOOGL_footnote_reconciliation": {"RECON_OMIT"},
    "PEP_fx_organic_growth": {"CC_OMIT"},
    "AMZN_footnote_reconciliation": {"CC_OMIT"},
    "NFLX_guidance_drift": {"CASH_VS_AMORT_ERR"},
    "KO_footnote_reconciliation": {"RECON_OMIT"},
}


def make_mock_agent(task_id: str, task: dict) -> ScriptedWeakMockAgent:
    builder = _MOCK_BUILDERS.get(task_id)
    if builder is None:
        raise NotImplementedError(f"mock agent not defined for {task_id!r}")
    return ScriptedWeakMockAgent(builder(task))
