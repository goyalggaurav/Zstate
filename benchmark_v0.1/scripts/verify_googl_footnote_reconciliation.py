#!/usr/bin/env python3
"""
Layer 1 verification script — GOOGL footnote reconciliation (FY2024).
Run against agent-extracted values or ground truth inputs.

Usage:
  python verify_googl_footnote_reconciliation.py
  python verify_googl_footnote_reconciliation.py --agent-output agent_values.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ground truth FY2024 (USD millions) — Alphabet 10-K filed 2025-02-05
GT = {
    "google_services_revenue_fy2024": 304_930,
    "google_cloud_revenue_fy2024": 43_229,
    "other_bets_revenue_fy2024": 1_648,
    "hedging_gains_losses_fy2024": 211,
    "consolidated_total_revenue_fy2024": 350_018,
}


def verify(values: dict) -> dict:
    """Return pass/fail report for reconciliation checks."""
    gs = values.get("google_services_revenue_fy2024")
    gc = values.get("google_cloud_revenue_fy2024")
    ob = values.get("other_bets_revenue_fy2024")
    hedge = values.get("hedging_gains_losses_fy2024") or values.get("reconciling_item_amount")
    total = values.get("consolidated_total_revenue_fy2024")

    segment_sum = None
    if all(v is not None for v in (gs, gc, ob)):
        segment_sum = gs + gc + ob

    reconciling = None
    if segment_sum is not None and total is not None:
        reconciling = total - segment_sum

    balanced = None
    if segment_sum is not None and hedge is not None and total is not None:
        balanced = segment_sum + hedge == total

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

    add("google_services_revenue_fy2024", GT["google_services_revenue_fy2024"], gs)
    add("google_cloud_revenue_fy2024", GT["google_cloud_revenue_fy2024"], gc)
    add("other_bets_revenue_fy2024", GT["other_bets_revenue_fy2024"], ob)
    add("hedging_gains_losses_fy2024", GT["hedging_gains_losses_fy2024"], hedge, critical=True)
    add("consolidated_total_revenue_fy2024", GT["consolidated_total_revenue_fy2024"], total)
    add("segment_sum_fy2024", GT["google_services_revenue_fy2024"] + GT["google_cloud_revenue_fy2024"] + GT["other_bets_revenue_fy2024"], segment_sum)
    add("reconciling_item_amount", GT["hedging_gains_losses_fy2024"], reconciling, critical=True)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)

    return {
        "task_id": "GOOGL_footnote_reconciliation",
        "all_pass": all_pass,
        "critical_fail": critical_fail,
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
    args = parser.parse_args()

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = GT

    report = verify(values)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
