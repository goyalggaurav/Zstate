#!/usr/bin/env python3
"""
Layer 1 verification — AMZN footnote reconciliation (FY2025).

Usage:
  python verify_amzn_footnote_reconciliation.py
  python verify_amzn_footnote_reconciliation.py --agent-output agent_values.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
GT_PATH = BENCH / "ground_truth" / "AMZN_footnote_reconciliation_gt.json"

GT_FY2025 = {
    "north_america_net_sales": 426_305,
    "international_net_sales": 161_894,
    "aws_net_sales": 128_725,
    "consolidated_net_sales": 716_924,
    "international_reported_growth_pct": 13.0,
    "international_cc_growth_pct": 10.0,
}

GT_FY2024 = {
    "north_america_net_sales": 387_497,
    "international_net_sales": 142_906,
    "aws_net_sales": 107_556,
    "consolidated_net_sales": 637_959,
}

FAILURE_FRACTURE = {
    "wrong_period": "HALLUC_FILL",
    "intl_fx_swap": "CC_OMIT",
    "segment_sum_mismatch": "RECON_OMIT",
    "treat_sbc_as_segment_line_item": "SBC_ALLOCATION_ERR",
}


def load_gt_constants() -> dict:
    doc = json.loads(GT_PATH.read_text(encoding="utf-8"))
    refs = doc.get("reference_constants") or {}
    traps = {item["id"]: item.get("wrong_signatures", {}) for item in doc.get("failure_modes", [])}
    return {
        "sbc_expense_usd_m": int(refs.get("sbc_expense_usd_m", 19_467)),
        "traps": traps,
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


def _sbc_trap_triggered(values: dict, gt: dict, meta: dict) -> bool:
    sbc = meta["sbc_expense_usd_m"]
    consolidated = _get_field(values, "consolidated_net_sales")
    na = _get_field(values, "north_america_net_sales")
    intl = _get_field(values, "international_net_sales")
    aws = _get_field(values, "aws_net_sales")
    consol_gt = gt["consolidated_net_sales"]

    sig = meta["traps"].get("treat_sbc_as_segment_line_item", {})
    if sig and all(_get_field(values, k) == v for k, v in sig.items()):
        return True

    if consolidated == consol_gt + sbc:
        return True
    if all(v is not None for v in (na, intl, aws, consolidated)):
        if na + intl + aws + sbc == consolidated:
            return True
    return False


def classify_failure(values: dict, gt: dict, meta: dict) -> list[str]:
    consolidated = _get_field(values, "consolidated_net_sales")
    if consolidated == GT_FY2024["consolidated_net_sales"]:
        return ["wrong_period"]

    if _sbc_trap_triggered(values, gt, meta):
        return ["treat_sbc_as_segment_line_item"]

    reported = _get_field(values, "international_reported_growth_pct")
    cc = _get_field(values, "international_cc_growth_pct")
    if _close(reported, 10.0) and _close(cc, 13.0):
        return ["intl_fx_swap"]

    na = _get_field(values, "north_america_net_sales")
    intl = _get_field(values, "international_net_sales")
    aws = _get_field(values, "aws_net_sales")
    if all(v is not None for v in (na, intl, aws, consolidated)):
        if na + intl + aws != consolidated:
            return ["segment_sum_mismatch"]

    return ["wrong_period"]


def verify(values: dict, gt: dict, *, meta: dict | None = None) -> dict:
    meta = meta or load_gt_constants()
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

    def add(metric_id: str, expected, actual, *, critical: bool = False, tolerance: float = 0):
        if tolerance:
            passed = _close(actual, expected, tolerance)
        else:
            passed = actual is not None and expected is not None and actual == expected
        checks.append({
            "metric_id": metric_id,
            "expected": expected,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    add("north_america_net_sales", gt["north_america_net_sales"], na)
    add("international_net_sales", gt["international_net_sales"], intl)
    add("aws_net_sales", gt["aws_net_sales"], aws)
    add("consolidated_net_sales", gt["consolidated_net_sales"], consolidated, critical=True)
    add("international_reported_growth_pct", gt["international_reported_growth_pct"], reported, tolerance=0.05)
    add("international_cc_growth_pct", gt["international_cc_growth_pct"], cc, tolerance=0.05)
    add("segment_sum", gt["consolidated_net_sales"], segment_sum)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)
    failure_modes = [] if all_pass else classify_failure(values, gt, meta)
    fracture_codes = list(dict.fromkeys(FAILURE_FRACTURE[m] for m in failure_modes if m in FAILURE_FRACTURE))

    return {
        "task_id": "AMZN_footnote_reconciliation",
        "all_pass": all_pass,
        "l1_pass": all_pass or not critical_fail,
        "critical_fail": critical_fail,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
        "checks": checks,
        "computed": {
            "segment_sum": segment_sum,
            "balanced": balanced,
            "sbc_trap_triggered": _sbc_trap_triggered(values, gt, meta) if not all_pass else False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    args = parser.parse_args()

    meta = load_gt_constants()
    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = GT_FY2025

    report = verify(values, GT_FY2025, meta=meta)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
