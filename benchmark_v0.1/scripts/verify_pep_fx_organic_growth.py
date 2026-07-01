#!/usr/bin/env python3
"""
Layer 1 verification — PEP FX organic growth (FY2025).
All expected values and tolerances are loaded from ground truth JSON.

Usage:
  python verify_pep_fx_organic_growth.py
  python verify_pep_fx_organic_growth.py --agent-output agent_values.json
  python verify_pep_fx_organic_growth.py --ground-truth ../ground_truth/PEP_fx_organic_growth_gt.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_GT_PATH = (
    Path(__file__).resolve().parent.parent / "ground_truth" / "PEP_fx_organic_growth_gt.json"
)

FAILURE_FRACTURE = {
    "spot_rate_method": "FX_METHOD_ERR",
    "wrong_region": "SCOPE_ERR",
    "reported_only": "CC_OMIT",
    "wrong_period": "HALLUC_FILL",
    "method_alt": "METHOD_ALT",
}


def load_ground_truth(path: Path) -> dict:
    doc = json.loads(path.read_text())
    values: dict[str, float | int | bool] = {}
    metric_meta: dict[str, dict] = {}

    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            metric_id = item["metric_id"]
            if isinstance(item.get("value"), bool):
                continue
            values[metric_id] = item["value"]
            metric_meta[metric_id] = {
                "tolerance": item.get("tolerance"),
                "acceptable_range_pp": item.get("acceptable_range_pp"),
            }

    policy = doc.get("verification_policy", {})
    policy_tolerances = policy.get("tolerances", {})
    failure_modes = {item["id"]: item for item in doc.get("failure_modes", [])}

    return {
        "task_id": doc.get("task_id", "PEP_fx_organic_growth"),
        "values": values,
        "metric_meta": metric_meta,
        "policy": policy,
        "policy_tolerances": policy_tolerances,
        "spot_trap": failure_modes.get("spot_rate_method", {}).get("wrong_signatures", {}),
        "reported_only_trap": failure_modes.get("reported_only", {}).get("wrong_signatures", {}),
    }


def _get(values: dict, key: str):
    return values.get(key)


def _pct_close(actual, expected, tol: float) -> bool:
    if actual is None or expected is None:
        return False
    return abs(float(actual) - float(expected)) <= tol


def _in_acceptable_range(actual, range_pp: list[float] | None) -> bool:
    if actual is None or not range_pp or len(range_pp) != 2:
        return False
    value = float(actual)
    return float(range_pp[0]) <= value <= float(range_pp[1])


def _organic_from_components(reported, fx) -> float | None:
    if reported is None or fx is None:
        return None
    return round(float(reported) - float(fx), 1)


def _metric_tolerance(
    metric_id: str,
    gt: dict,
    *,
    default: float = 0,
) -> float:
    meta = gt["metric_meta"].get(metric_id, {})
    if meta.get("tolerance") is not None:
        return float(meta["tolerance"])

    policy_key = {
        "wae_eur_usd_fy2025": "wae_fx_rate",
        "wae_eur_usd_fy2024": "wae_fx_rate",
        "europe_reported_growth_pct": "reported_growth_pct",
        "amesa_reported_growth_pct": "reported_growth_pct",
        "europe_fx_impact_pct": "fx_impact_pct",
        "amesa_fx_impact_pct": "fx_impact_pct",
        "europe_organic_cc_growth_pct": "organic_cc_pct_strict",
        "amesa_organic_cc_growth_pct": "organic_cc_pct_strict",
    }.get(metric_id)
    if policy_key and policy_key in gt["policy_tolerances"]:
        return float(gt["policy_tolerances"][policy_key])
    return default


def classify_failure(values: dict, gt: dict) -> list[str]:
    modes: list[str] = []
    expected = gt["values"]
    spot_trap = gt["spot_trap"]
    reported_trap = gt["reported_only_trap"]

    wae25 = _get(values, "wae_eur_usd_fy2025")
    wae24 = _get(values, "wae_eur_usd_fy2024")
    if (
        spot_trap
        and wae25 == spot_trap.get("wae_eur_usd_fy2025")
        and wae24 == spot_trap.get("wae_eur_usd_fy2024")
    ):
        modes.append("spot_rate_method")
        return modes

    e_cc = _get(values, "europe_organic_cc_growth_pct")
    a_cc = _get(values, "amesa_organic_cc_growth_pct")
    if reported_trap:
        if e_cc == reported_trap.get("europe_organic_cc_growth_pct") or a_cc == reported_trap.get(
            "amesa_organic_cc_growth_pct"
        ):
            modes.append("reported_only")

    e25 = _get(values, "europe_net_revenue_fy2025")
    exp_e25 = expected.get("europe_net_revenue_fy2025")
    if e25 is not None and exp_e25 is not None and e25 != exp_e25:
        if e25 < 9000 or e25 > 15000:
            modes.append("wrong_region")

    return modes


def verify(values: dict, gt: dict) -> dict:
    expected = gt["values"]
    checks: list[dict] = []
    method_alt_metrics: list[str] = []

    def add(
        metric_id: str,
        actual,
        *,
        tol: float | None = None,
        critical: bool = False,
        allow_method_alt: bool = False,
        expected_key: str | None = None,
    ):
        exp = expected.get(expected_key or metric_id)
        if tol is None:
            tol = _metric_tolerance(metric_id, gt)

        strict_pass = _pct_close(actual, exp, tol) if tol else (
            actual is not None and exp is not None and actual == exp
        )
        alt_pass = False
        if allow_method_alt and not strict_pass:
            range_pp = gt["metric_meta"].get(metric_id, {}).get("acceptable_range_pp")
            alt_pass = _in_acceptable_range(actual, range_pp)
            if alt_pass:
                method_alt_metrics.append(metric_id)

        check = {
            "metric_id": metric_id,
            "expected": exp,
            "actual": actual,
            "pass": strict_pass,
            "critical": critical,
        }
        if allow_method_alt:
            check["method_alt"] = alt_pass
            check["l1_pass"] = strict_pass or alt_pass
        checks.append(check)

    e25 = _get(values, "europe_net_revenue_fy2025")
    e24 = _get(values, "europe_net_revenue_fy2024")
    a25 = _get(values, "amesa_net_revenue_fy2025")
    a24 = _get(values, "amesa_net_revenue_fy2024")
    w25 = _get(values, "wae_eur_usd_fy2025")
    w24 = _get(values, "wae_eur_usd_fy2024")

    add("europe_net_revenue_fy2025", e25)
    add("europe_net_revenue_fy2024", e24)
    add("amesa_net_revenue_fy2025", a25)
    add("amesa_net_revenue_fy2024", a24)
    add("wae_eur_usd_fy2025", w25, critical=True)
    add("wae_eur_usd_fy2024", w24, critical=True)

    e_rep = _get(values, "europe_reported_growth_pct")
    e_fx = _get(values, "europe_fx_impact_pct")
    a_rep = _get(values, "amesa_reported_growth_pct")
    a_fx = _get(values, "amesa_fx_impact_pct")

    add("europe_reported_growth_pct", e_rep)
    add("europe_fx_impact_pct", e_fx)
    add("amesa_reported_growth_pct", a_rep)
    add("amesa_fx_impact_pct", a_fx)

    e_cc = _get(values, "europe_organic_cc_growth_pct")
    a_cc = _get(values, "amesa_organic_cc_growth_pct")
    add("europe_organic_cc_growth_pct", e_cc, critical=True, allow_method_alt=True)
    add("amesa_organic_cc_growth_pct", a_cc, critical=True, allow_method_alt=True)

    e_cc_formula = _organic_from_components(
        e_rep if e_rep is not None else expected.get("europe_reported_growth_pct"),
        e_fx if e_fx is not None else expected.get("europe_fx_impact_pct"),
    )
    a_cc_formula = _organic_from_components(
        a_rep if a_rep is not None else expected.get("amesa_reported_growth_pct"),
        a_fx if a_fx is not None else expected.get("amesa_fx_impact_pct"),
    )
    add(
        "europe_cc_formula_pct",
        e_cc_formula,
        tol=0.1,
        expected_key="europe_organic_cc_growth_pct",
    )
    add(
        "amesa_cc_formula_pct",
        a_cc_formula,
        tol=0.1,
        expected_key="amesa_organic_cc_growth_pct",
    )

    all_pass = all(c["pass"] for c in checks)
    l1_pass = all(c.get("l1_pass", c["pass"]) for c in checks)
    critical_fail = any(not c.get("l1_pass", c["pass"]) and c["critical"] for c in checks)
    failure_modes = [] if l1_pass else classify_failure(values, gt)
    if method_alt_metrics and not all_pass:
        failure_modes.append("method_alt")
    fracture_codes = list(dict.fromkeys(FAILURE_FRACTURE[m] for m in failure_modes if m in FAILURE_FRACTURE))

    return {
        "task_id": gt["task_id"],
        "all_pass": all_pass,
        "l1_pass": l1_pass,
        "critical_fail": critical_fail,
        "method_alt_metrics": method_alt_metrics,
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
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=DEFAULT_GT_PATH,
        help="Ground truth JSON (reviewer edits this file only)",
    )
    args = parser.parse_args()

    gt = load_ground_truth(args.ground_truth)

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt["values"]

    report = verify(values, gt)
    print(json.dumps(report, indent=2))
    return 0 if report["l1_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
