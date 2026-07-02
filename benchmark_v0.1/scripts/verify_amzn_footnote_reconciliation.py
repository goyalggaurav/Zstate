#!/usr/bin/env python3
"""
Layer 1 verification — footnote reconciliation archetype (F_exact).

Ground truth JSON is the single source for scored values, traps, and reference constants.

Usage:
  python verify_amzn_footnote_reconciliation.py --ground-truth ../ground_truth/AMZN_footnote_reconciliation_gt.json
  python verify_amzn_footnote_reconciliation.py --ground-truth ../ground_truth/AMZN_footnote_reconciliation_gt.json --agent-output agent.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fracture_registry import fracture_codes as resolve_fracture_codes, l1_map_for_task

FAILURE_FRACTURE = l1_map_for_task("AMZN_footnote_reconciliation")


def load_ground_truth(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    values: dict[str, float | int] = {}
    tolerances: dict[str, float] = {}

    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            mid = item["metric_id"]
            if isinstance(item.get("value"), bool):
                continue
            values[mid] = item["value"]
            if item.get("tolerance") is not None:
                tolerances[mid] = float(item["tolerance"])

    refs = doc.get("reference_constants") or {}
    traps: dict[str, dict] = {}
    for mode in doc.get("failure_modes", []):
        traps[mode["id"]] = mode.get("wrong_signatures") or {}

    wrong_period_trap = traps.get("wrong_period", {})
    prior_consolidated = wrong_period_trap.get("consolidated_net_sales")

    return {
        "task_id": doc["task_id"],
        "values": values,
        "tolerances": tolerances,
        "traps": traps,
        "sbc_expense_usd_m": int(refs.get("sbc_expense_usd_m", 0)),
        "prior_consolidated_net_sales": prior_consolidated,
    }


def _get_field(values: dict, *keys: str):
    for key in keys:
        if key in values and values[key] is not None:
            return values[key]
    return None


def _close(a: float | None, b: float, tol: float = 0.05) -> bool:
    if a is None:
        return False
    return abs(float(a) - float(b)) <= tol


def _sbc_trap_triggered(values: dict, gt: dict) -> bool:
    sbc = gt["sbc_expense_usd_m"]
    consolidated = _get_field(values, "consolidated_net_sales")
    na = _get_field(values, "north_america_net_sales")
    intl = _get_field(values, "international_net_sales")
    aws = _get_field(values, "aws_net_sales")
    consol_gt = gt["values"]["consolidated_net_sales"]

    sig = gt["traps"].get("treat_sbc_as_segment_line_item", {})
    if sig and all(_get_field(values, k) == v for k, v in sig.items()):
        return True

    if consolidated == consol_gt + sbc:
        return True
    if all(v is not None for v in (na, intl, aws, consolidated)):
        if na + intl + aws + sbc == consolidated:
            return True
    return False


def classify_failure(values: dict, gt: dict) -> list[str]:
    consolidated = _get_field(values, "consolidated_net_sales")
    prior = gt.get("prior_consolidated_net_sales")
    if prior is not None and consolidated == prior:
        return ["wrong_period"]

    if _sbc_trap_triggered(values, gt):
        return ["treat_sbc_as_segment_line_item"]

    fx_trap = gt["traps"].get("intl_fx_swap", {})
    reported = _get_field(values, "international_reported_growth_pct")
    cc = _get_field(values, "international_cc_growth_pct")
    if fx_trap and reported is not None and cc is not None:
        rep_exp = fx_trap.get("international_reported_growth_pct")
        cc_exp = fx_trap.get("international_cc_growth_pct")
        if rep_exp is not None and cc_exp is not None:
            if _close(reported, rep_exp, 0.05) and _close(cc, cc_exp, 0.05):
                return ["intl_fx_swap"]

    na = _get_field(values, "north_america_net_sales")
    intl = _get_field(values, "international_net_sales")
    aws = _get_field(values, "aws_net_sales")
    if all(v is not None for v in (na, intl, aws, consolidated)):
        if na + intl + aws != consolidated:
            return ["segment_sum_mismatch"]

    return ["wrong_period"]


def verify(values: dict, gt: dict) -> dict:
    expected = gt["values"]
    na = _get_field(values, "north_america_net_sales")
    intl = _get_field(values, "international_net_sales")
    aws = _get_field(values, "aws_net_sales")
    consolidated = _get_field(values, "consolidated_net_sales")
    reported = _get_field(values, "international_reported_growth_pct")
    cc = _get_field(values, "international_cc_growth_pct")

    segment_sum = None
    if all(v is not None for v in (na, intl, aws)):
        segment_sum = na + intl + aws

    balanced = None
    if segment_sum is not None and consolidated is not None:
        balanced = segment_sum == consolidated

    checks = []

    def add(metric_id: str, exp, actual, *, critical: bool = False, tolerance: float = 0):
        if tolerance:
            passed = _close(actual, exp, tolerance)
        else:
            passed = actual is not None and exp is not None and actual == exp
        checks.append({
            "metric_id": metric_id,
            "expected": exp,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    add("north_america_net_sales", expected["north_america_net_sales"], na)
    add("international_net_sales", expected["international_net_sales"], intl)
    add("aws_net_sales", expected["aws_net_sales"], aws)
    add("consolidated_net_sales", expected["consolidated_net_sales"], consolidated, critical=True)
    add(
        "international_reported_growth_pct",
        expected["international_reported_growth_pct"],
        reported,
        tolerance=gt["tolerances"].get("international_reported_growth_pct", 0.05),
    )
    add(
        "international_cc_growth_pct",
        expected["international_cc_growth_pct"],
        cc,
        tolerance=gt["tolerances"].get("international_cc_growth_pct", 0.05),
    )
    add("segment_sum", expected["consolidated_net_sales"], segment_sum)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)
    failure_modes = [] if all_pass else classify_failure(values, gt)
    fracture_codes_list = resolve_fracture_codes(failure_modes, task_id=gt["task_id"], layer="L1")

    return {
        "task_id": gt["task_id"],
        "archetype": "F_exact",
        "all_pass": all_pass,
        "l1_pass": all_pass or not critical_fail,
        "critical_fail": critical_fail,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes_list,
        "checks": checks,
        "computed": {
            "segment_sum": segment_sum,
            "balanced": balanced,
            "sbc_trap_triggered": _sbc_trap_triggered(values, gt) if not all_pass else False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ground-truth",
        type=Path,
        help="Ground truth JSON (default: AMZN_footnote_reconciliation_gt.json)",
    )
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    args = parser.parse_args()

    gt_path = args.ground_truth
    if gt_path is None:
        gt_path = Path(__file__).resolve().parent.parent / "ground_truth" / "AMZN_footnote_reconciliation_gt.json"

    gt = load_ground_truth(gt_path)

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt["values"]

    report = verify(values, gt)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
