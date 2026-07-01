#!/usr/bin/env python3
"""
Layer 1 verification — PEP FX organic growth (FY2025).
Run against agent-extracted values or ground truth inputs.

Usage:
  python verify_pep_fx_organic_growth.py
  python verify_pep_fx_organic_growth.py --agent-output agent_values.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# FY2025 (USD millions, pct) — PepsiCo 10-K filed 2026-02-18, period ended 2025-12-27
GT_FY2025 = {
    "europe_net_revenue_fy2025": 12_354,
    "europe_net_revenue_fy2024": 11_892,
    "amesa_net_revenue_fy2025": 5_670,
    "amesa_net_revenue_fy2024": 5_240,
    "wae_eur_usd_fy2025": 1.024,
    "wae_eur_usd_fy2024": 1.081,
    "europe_reported_growth_pct": 3.9,
    "europe_fx_impact_pct": -6.1,
    "europe_organic_cc_growth_pct": 10.0,
    "amesa_reported_growth_pct": 8.2,
    "amesa_fx_impact_pct": -1.5,
    "amesa_organic_cc_growth_pct": 9.7,
}

# Spot-rate trap signature (year-end rates — wrong method)
SPOT_TRAP = {
    "wae_eur_usd_fy2025": 1.058,
    "wae_eur_usd_fy2024": 1.104,
}

FAILURE_FRACTURE = {
    "spot_rate_method": "FX_METHOD_ERR",
    "wrong_region": "SCOPE_ERR",
    "reported_only": "CC_OMIT",
    "wrong_period": "HALLUC_FILL",
}


def _get(values: dict, key: str):
    return values.get(key)


def _pct_close(actual, expected, tol: float) -> bool:
    if actual is None or expected is None:
        return False
    return abs(float(actual) - float(expected)) <= tol


def _organic_from_components(reported, fx) -> float | None:
    if reported is None or fx is None:
        return None
    return round(float(reported) - float(fx), 1)


def classify_failure(values: dict) -> list[str]:
    modes: list[str] = []

    wae25 = _get(values, "wae_eur_usd_fy2025")
    wae24 = _get(values, "wae_eur_usd_fy2024")
    if wae25 == SPOT_TRAP["wae_eur_usd_fy2025"] and wae24 == SPOT_TRAP["wae_eur_usd_fy2024"]:
        modes.append("spot_rate_method")
        return modes

    e_cc = _get(values, "europe_organic_cc_growth_pct")
    a_cc = _get(values, "amesa_organic_cc_growth_pct")
    if e_cc == GT_FY2025["europe_reported_growth_pct"] or a_cc == GT_FY2025["amesa_reported_growth_pct"]:
        modes.append("reported_only")

    e25 = _get(values, "europe_net_revenue_fy2025")
    if e25 is not None and e25 != GT_FY2025["europe_net_revenue_fy2025"]:
        if e25 < 9000 or e25 > 15000:
            modes.append("wrong_region")

    return modes


def verify(values: dict) -> dict:
    gt = GT_FY2025
    checks = []

    def add(metric_id: str, expected, actual, tol: float = 0, critical: bool = False):
        if tol:
            passed = _pct_close(actual, expected, tol)
        else:
            passed = actual is not None and expected is not None and actual == expected
        checks.append({
            "metric_id": metric_id,
            "expected": expected,
            "actual": actual,
            "pass": passed,
            "critical": critical,
        })

    e25 = _get(values, "europe_net_revenue_fy2025")
    e24 = _get(values, "europe_net_revenue_fy2024")
    a25 = _get(values, "amesa_net_revenue_fy2025")
    a24 = _get(values, "amesa_net_revenue_fy2024")
    w25 = _get(values, "wae_eur_usd_fy2025")
    w24 = _get(values, "wae_eur_usd_fy2024")

    add("europe_net_revenue_fy2025", gt["europe_net_revenue_fy2025"], e25)
    add("europe_net_revenue_fy2024", gt["europe_net_revenue_fy2024"], e24)
    add("amesa_net_revenue_fy2025", gt["amesa_net_revenue_fy2025"], a25)
    add("amesa_net_revenue_fy2024", gt["amesa_net_revenue_fy2024"], a24)
    add("wae_eur_usd_fy2025", gt["wae_eur_usd_fy2025"], w25, tol=0.001, critical=True)
    add("wae_eur_usd_fy2024", gt["wae_eur_usd_fy2024"], w24, tol=0.001, critical=True)

    e_rep = _get(values, "europe_reported_growth_pct")
    e_fx = _get(values, "europe_fx_impact_pct")
    a_rep = _get(values, "amesa_reported_growth_pct")
    a_fx = _get(values, "amesa_fx_impact_pct")

    add("europe_reported_growth_pct", gt["europe_reported_growth_pct"], e_rep, tol=0.1)
    add("europe_fx_impact_pct", gt["europe_fx_impact_pct"], e_fx, tol=0.1)
    add("amesa_reported_growth_pct", gt["amesa_reported_growth_pct"], a_rep, tol=0.1)
    add("amesa_fx_impact_pct", gt["amesa_fx_impact_pct"], a_fx, tol=0.1)

    e_cc = _get(values, "europe_organic_cc_growth_pct")
    a_cc = _get(values, "amesa_organic_cc_growth_pct")
    add("europe_organic_cc_growth_pct", gt["europe_organic_cc_growth_pct"], e_cc, tol=0.2, critical=True)
    add("amesa_organic_cc_growth_pct", gt["amesa_organic_cc_growth_pct"], a_cc, tol=0.2, critical=True)

    e_cc_formula = _organic_from_components(
        e_rep if e_rep is not None else gt["europe_reported_growth_pct"],
        e_fx if e_fx is not None else gt["europe_fx_impact_pct"],
    )
    a_cc_formula = _organic_from_components(
        a_rep if a_rep is not None else gt["amesa_reported_growth_pct"],
        a_fx if a_fx is not None else gt["amesa_fx_impact_pct"],
    )
    add("europe_cc_formula_pct", gt["europe_organic_cc_growth_pct"], e_cc_formula, tol=0.1)
    add("amesa_cc_formula_pct", gt["amesa_organic_cc_growth_pct"], a_cc_formula, tol=0.1)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)
    failure_modes = [] if all_pass else classify_failure(values)
    fracture_codes = list(dict.fromkeys(FAILURE_FRACTURE[m] for m in failure_modes if m in FAILURE_FRACTURE))

    return {
        "task_id": "PEP_fx_organic_growth",
        "all_pass": all_pass,
        "critical_fail": critical_fail,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
        "checks": checks,
        "computed": {
            "europe_cc_formula_pct": e_cc_formula,
            "amesa_cc_formula_pct": a_cc_formula,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    args = parser.parse_args()

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = GT_FY2025

    report = verify(values)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
