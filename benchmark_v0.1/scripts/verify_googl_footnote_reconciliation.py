#!/usr/bin/env python3
"""
Layer 1 verification — GOOGL footnote reconciliation (Q1 2026).
Run against agent-extracted values or ground truth inputs.

Usage:
  python verify_googl_footnote_reconciliation.py
  python verify_googl_footnote_reconciliation.py --agent-output agent_values.json
  python verify_googl_footnote_reconciliation.py --period fy2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fracture_registry import fracture_codes as resolve_fracture_codes, l1_map_for_task

# Q1 2026 (USD millions) — Alphabet 10-Q filed 2026-04-30, period ended 2026-03-31
GT_Q1_2026 = {
    "google_services_revenue": 89_637,
    "google_cloud_revenue": 20_028,
    "other_bets_revenue": 411,
    "hedging_gains_losses": -180,
    "consolidated_total_revenue": 109_896,
}

# FY2025 annual reference (USD millions) — Alphabet 10-K filed 2026-02-05
GT_FY2025 = {
    "google_services_revenue": 342_721,
    "google_cloud_revenue": 58_705,
    "other_bets_revenue": 1_537,
    "hedging_gains_losses": -127,
    "consolidated_total_revenue": 402_836,
}

SEGMENT_SUM_Q1_2026 = 110_076

FAILURE_FRACTURE = l1_map_for_task("GOOGL_footnote_reconciliation")


def _get_field(values: dict, *keys: str):
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    return None


def _segments_match_gt(gs, gc, ob, gt: dict) -> bool:
    return (
        gs == gt["google_services_revenue"]
        and gc == gt["google_cloud_revenue"]
        and ob == gt["other_bets_revenue"]
    )


def classify_failure(values: dict, gt: dict) -> list[str]:
    """Return ordered failure_mode ids detected from agent output."""
    gs = _get_field(values, "google_services_revenue", "google_services_revenue_fy2024")
    gc = _get_field(values, "google_cloud_revenue", "google_cloud_revenue_fy2024")
    ob = _get_field(values, "other_bets_revenue", "other_bets_revenue_fy2024")
    hedge = _get_field(
        values, "hedging_gains_losses", "hedging_gains_losses_fy2024", "reconciling_item_amount"
    )
    total = _get_field(values, "consolidated_total_revenue", "consolidated_total_revenue_fy2024")

    modes: list[str] = []

    # FY2025 annual column mistaken for scored period
    if total == GT_FY2025["consolidated_total_revenue"] or hedge == GT_FY2025["hedging_gains_losses"]:
        modes.append("wrong_filing")
        return modes

    if hedge == 180:
        modes.append("sign_error")

    segments_ok = _segments_match_gt(gs, gc, ob, gt)
    if segments_ok and (total == SEGMENT_SUM_Q1_2026 or hedge is None):
        if "sign_error" not in modes:
            modes.append("blind_sum")

    if not segments_ok and any(v is not None for v in (gs, gc, ob, total, hedge)):
        if not modes:
            modes.append("wrong_period")

    return modes


def verify(values: dict, gt: dict) -> dict:
    """Return pass/fail report for reconciliation checks."""
    gs = _get_field(values, "google_services_revenue", "google_services_revenue_fy2024")
    gc = _get_field(values, "google_cloud_revenue", "google_cloud_revenue_fy2024")
    ob = _get_field(values, "other_bets_revenue", "other_bets_revenue_fy2024")
    hedge = _get_field(
        values, "hedging_gains_losses", "hedging_gains_losses_fy2024", "reconciling_item_amount"
    )
    total = _get_field(values, "consolidated_total_revenue", "consolidated_total_revenue_fy2024")

    segment_sum = None
    if all(v is not None for v in (gs, gc, ob)):
        segment_sum = gs + gc + ob

    reconciling = None
    if segment_sum is not None and total is not None:
        reconciling = total - segment_sum

    balanced = None
    if segment_sum is not None and hedge is not None and total is not None:
        balanced = segment_sum + hedge == total

    expected_segment_sum = gt["google_services_revenue"] + gt["google_cloud_revenue"] + gt["other_bets_revenue"]

    checks = []

    def add(metric_id: str, expected, actual, critical: bool = False):
        passed = actual is not None and expected is not None and actual == expected
        checks.append({
            "metric_id": metric_id,
            "expected": expected,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    add("google_services_revenue", gt["google_services_revenue"], gs)
    add("google_cloud_revenue", gt["google_cloud_revenue"], gc)
    add("other_bets_revenue", gt["other_bets_revenue"], ob)
    add("hedging_gains_losses", gt["hedging_gains_losses"], hedge, critical=True)
    add("consolidated_total_revenue", gt["consolidated_total_revenue"], total)
    add("segment_sum", expected_segment_sum, segment_sum)
    add("reconciling_item_amount", gt["hedging_gains_losses"], reconciling, critical=True)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)

    failure_modes = [] if all_pass else classify_failure(values, gt)
    fracture_codes_list = resolve_fracture_codes(
        failure_modes, task_id="GOOGL_footnote_reconciliation", layer="L1"
    )

    return {
        "task_id": "GOOGL_footnote_reconciliation",
        "all_pass": all_pass,
        "critical_fail": critical_fail,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes_list,
        "checks": checks,
        "computed": {
            "segment_sum": segment_sum,
            "reconciling_item": reconciling,
            "balanced": balanced,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    parser.add_argument(
        "--period",
        choices=("q1_2026", "fy2025"),
        default="q1_2026",
        help="Ground truth period (default: q1_2026 scored task)",
    )
    args = parser.parse_args()

    gt = GT_FY2025 if args.period == "fy2025" else GT_Q1_2026

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt

    report = verify(values, gt)
    report["period"] = args.period
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
