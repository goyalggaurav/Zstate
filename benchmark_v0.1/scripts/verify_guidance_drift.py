#!/usr/bin/env python3
"""
Layer 1 verification — guidance drift archetype (F_guidance_drift).

Supports annual-guidance vs YTD-actual pace comparison (NFLX pilot).

Usage:
  python verify_guidance_drift.py --ground-truth ../ground_truth/NFLX_guidance_drift_gt.json
  python verify_guidance_drift.py --ground-truth ../ground_truth/NFLX_guidance_drift_gt.json --agent-output agent.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FAILURE_FRACTURE = {
    "wrong_ytd_window": "GUIDANCE_PERIOD_ERR",
    "amortization_as_cash": "CASH_VS_AMORT_ERR",
}


def load_ground_truth(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    values: dict[str, float | int | bool] = {}
    tolerances: dict[str, float] = {}
    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            mid = item["metric_id"]
            values[mid] = item["value"]
            if item.get("tolerance") is not None:
                tolerances[mid] = float(item["tolerance"])
    traps: dict[str, dict] = {}
    for mode in doc.get("failure_modes", []):
        traps[mode["id"]] = mode.get("wrong_signatures", {})
    return {
        "task_id": doc["task_id"],
        "values": values,
        "tolerances": tolerances,
        "traps": traps,
        "guidance_spec": doc.get("guidance_spec", {}),
    }


def _get(values: dict, key: str):
    return values.get(key)


def _close(a, b, tol: float = 0) -> bool:
    if a is None or b is None:
        return False
    if tol:
        return abs(float(a) - float(b)) <= tol
    return a == b


def classify_failure(values: dict, gt: dict) -> list[str]:
    for mode_id, sigs in gt["traps"].items():
        if sigs and all(_get(values, k) == v for k, v in sigs.items()):
            return [mode_id]
    return ["wrong_ytd_window"]


def verify(values: dict, gt: dict) -> dict:
    expected = gt["values"]
    annual = _get(values, "guidance_content_cash_annual_usd_m")
    ytd_months = _get(values, "ytd_period_months")
    ytd_cash = _get(values, "ytd_content_cash_payments_usd_m")
    amort = _get(values, "q3_content_amortization_usd_m")
    variance = _get(values, "cash_vs_guidance_pace_variance_pct")
    pace_under = _get(values, "guidance_pace_under")

    implied_pace = None
    if annual is not None and ytd_months is not None:
        implied_pace = round(float(annual) * float(ytd_months) / 12)

    computed_variance = None
    if ytd_cash is not None and implied_pace:
        computed_variance = round((float(ytd_cash) - implied_pace) / implied_pace * 100, 1)

    computed_pace_under = None
    if ytd_cash is not None and implied_pace is not None:
        computed_pace_under = float(ytd_cash) < float(implied_pace)

    checks = []

    def add(metric_id: str, actual, exp, *, tol: float = 0, critical: bool = False):
        passed = _close(actual, exp, tol)
        checks.append({
            "metric_id": metric_id,
            "expected": exp,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    add("guidance_content_cash_annual_usd_m", annual, expected["guidance_content_cash_annual_usd_m"])
    add("ytd_period_months", ytd_months, expected["ytd_period_months"])
    add("ytd_content_cash_payments_usd_m", ytd_cash, expected["ytd_content_cash_payments_usd_m"], critical=True)
    add("q3_content_amortization_usd_m", amort, expected["q3_content_amortization_usd_m"])
    add(
        "cash_vs_guidance_pace_variance_pct",
        variance,
        expected["cash_vs_guidance_pace_variance_pct"],
        tol=gt["tolerances"].get("cash_vs_guidance_pace_variance_pct", 0.15),
        critical=True,
    )
    add(
        "guidance_pace_under",
        pace_under if pace_under is not None else computed_pace_under,
        expected.get("guidance_pace_under"),
        critical=True,
    )

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)
    failure_modes = [] if all_pass else classify_failure(values, gt)
    fracture_codes = list(dict.fromkeys(FAILURE_FRACTURE[m] for m in failure_modes if m in FAILURE_FRACTURE))

    return {
        "task_id": gt["task_id"],
        "archetype": "F_guidance_drift",
        "all_pass": all_pass,
        "l1_pass": all_pass or not critical_fail,
        "critical_fail": critical_fail,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
        "checks": checks,
        "computed": {
            "implied_ytd_pace_usd_m": implied_pace,
            "cash_vs_guidance_pace_variance_pct": computed_variance,
            "guidance_pace_under": computed_pace_under,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--agent-output", type=Path)
    args = parser.parse_args()

    gt = load_ground_truth(args.ground_truth)
    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = {k: v for k, v in gt["values"].items() if not isinstance(v, bool)}
        if "guidance_pace_under" in gt["values"]:
            values["guidance_pace_under"] = gt["values"]["guidance_pace_under"]

    report = verify(values, gt)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
