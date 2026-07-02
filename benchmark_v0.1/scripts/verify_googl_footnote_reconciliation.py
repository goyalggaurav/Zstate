#!/usr/bin/env python3
"""
Layer 1 verification — footnote reconciliation archetype (F_adjustment).

Ground truth JSON is the single source for scored values, traps, and annual reference.

Usage:
  python verify_googl_footnote_reconciliation.py --ground-truth ../ground_truth/GOOGL_footnote_reconciliation_gt.json
  python verify_googl_footnote_reconciliation.py --ground-truth ../ground_truth/GOOGL_footnote_reconciliation_gt.json --agent-output agent.json
  python verify_googl_footnote_reconciliation.py --ground-truth ../ground_truth/GOOGL_footnote_reconciliation_gt.json --period fy2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fracture_registry import fracture_codes as resolve_fracture_codes, l1_map_for_task

FAILURE_FRACTURE = l1_map_for_task("GOOGL_footnote_reconciliation")

SEGMENT_METRICS = (
    "google_services_revenue",
    "google_cloud_revenue",
    "other_bets_revenue",
)


def load_ground_truth(path: Path, *, period: str = "q1_2026") -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    values: dict[str, float | int | bool] = {}
    tolerances: dict[str, float] = {}
    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            mid = item["metric_id"]
            values[mid] = item["value"]
            if item.get("tolerance") is not None:
                tolerances[mid] = float(item["tolerance"])

    annual_raw = doc.get("annual_reference_fy2025", {}).get("values_usd_millions", {})
    annual_values = {
        "google_services_revenue": annual_raw.get("google_services"),
        "google_cloud_revenue": annual_raw.get("google_cloud"),
        "other_bets_revenue": annual_raw.get("other_bets"),
        "hedging_gains_losses": annual_raw.get("hedging_gains_losses"),
        "consolidated_total_revenue": annual_raw.get("consolidated_total"),
    }

    scored_values = {
        key: values[key]
        for key in (
            *SEGMENT_METRICS,
            "hedging_gains_losses",
            "consolidated_total_revenue",
        )
        if key in values
    }

    traps: dict[str, dict] = {}
    for mode in doc.get("failure_modes", []):
        traps[mode["id"]] = mode.get("wrong_signatures") or {}

    period_values = annual_values if period == "fy2025" else scored_values

    return {
        "task_id": doc["task_id"],
        "period": period,
        "values": period_values,
        "full_values": values,
        "tolerances": tolerances,
        "traps": traps,
        "annual_reference": annual_values,
        "segment_sum_scored": values.get("segment_sum"),
    }


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

    annual = gt["annual_reference"]
    modes: list[str] = []

    if total == annual.get("consolidated_total_revenue") or hedge == annual.get("hedging_gains_losses"):
        modes.append("wrong_filing")
        return modes

    sign_trap = gt["traps"].get("sign_error", {})
    if sign_trap.get("hedging_gains_losses") is not None and hedge == sign_trap["hedging_gains_losses"]:
        modes.append("sign_error")

    segments_ok = _segments_match_gt(gs, gc, ob, gt["values"])
    segment_sum_scored = gt.get("segment_sum_scored")
    if segments_ok and segment_sum_scored is not None and (total == segment_sum_scored or hedge is None):
        if "sign_error" not in modes:
            modes.append("blind_sum")

    if not segments_ok and any(v is not None for v in (gs, gc, ob, total, hedge)):
        if not modes:
            modes.append("wrong_period")

    return modes


def verify(values: dict, gt: dict) -> dict:
    """Return pass/fail report for reconciliation checks."""
    expected = gt["values"]
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

    expected_segment_sum = (
        expected["google_services_revenue"]
        + expected["google_cloud_revenue"]
        + expected["other_bets_revenue"]
    )

    checks = []

    def add(metric_id: str, exp, actual, critical: bool = False):
        passed = actual is not None and exp is not None and actual == exp
        checks.append({
            "metric_id": metric_id,
            "expected": exp,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    add("google_services_revenue", expected["google_services_revenue"], gs)
    add("google_cloud_revenue", expected["google_cloud_revenue"], gc)
    add("other_bets_revenue", expected["other_bets_revenue"], ob)
    add("hedging_gains_losses", expected["hedging_gains_losses"], hedge, critical=True)
    add("consolidated_total_revenue", expected["consolidated_total_revenue"], total)
    add("segment_sum", expected_segment_sum, segment_sum)
    add("reconciling_item_amount", expected["hedging_gains_losses"], reconciling, critical=True)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)

    failure_modes = [] if all_pass else classify_failure(values, gt)
    fracture_codes_list = resolve_fracture_codes(failure_modes, task_id=gt["task_id"], layer="L1")

    return {
        "task_id": gt["task_id"],
        "archetype": "F_adjustment",
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
    parser.add_argument(
        "--ground-truth",
        type=Path,
        help="Ground truth JSON (default: GOOGL_footnote_reconciliation_gt.json)",
    )
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    parser.add_argument(
        "--period",
        choices=("q1_2026", "fy2025"),
        default="q1_2026",
        help="Ground truth period (default: q1_2026 scored task)",
    )
    args = parser.parse_args()

    gt_path = args.ground_truth
    if gt_path is None:
        gt_path = Path(__file__).resolve().parent.parent / "ground_truth" / "GOOGL_footnote_reconciliation_gt.json"

    gt = load_ground_truth(gt_path, period=args.period)

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt["values"]

    report = verify(values, gt)
    report["period"] = args.period
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
