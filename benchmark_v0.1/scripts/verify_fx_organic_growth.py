#!/usr/bin/env python3
"""
Archetype L1 verification — fx_organic_growth.
All segment names, metric IDs, tolerances, and traps are loaded from ground truth JSON.

Usage:
  python verify_fx_organic_growth.py --ground-truth ../ground_truth/PEP_fx_organic_growth_gt.json
  python verify_fx_organic_growth.py --ground-truth ../ground_truth/PEP_fx_organic_growth_gt.json --agent-output agent.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fracture_registry import fracture_codes as resolve_fracture_codes, l1_map_for_task

FAILURE_FRACTURE = l1_map_for_task("PEP_fx_organic_growth")


def load_ground_truth(path: Path) -> dict:
    doc = json.loads(path.read_text())
    values: dict[str, float | int] = {}
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

    schema = doc.get("verification_schema", {})
    policy = doc.get("verification_policy", {})
    failure_modes = {item["id"]: item for item in doc.get("failure_modes", [])}

    spot_metrics: dict[str, float] = {}
    spot_mode = failure_modes.get("spot_rate_method", {})
    for sig in spot_mode.get("wrong_signatures", {}):
        spot_metrics[sig] = spot_mode["wrong_signatures"][sig]

    return {
        "task_id": doc.get("task_id", "unknown"),
        "values": values,
        "metric_meta": metric_meta,
        "schema": schema,
        "policy": policy,
        "policy_tolerances": policy.get("tolerances", {}),
        "failure_modes": failure_modes,
        "spot_trap": spot_mode.get("wrong_signatures", {}),
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


def _tolerance_for_metric(metric_id: str, gt: dict, default: float = 0) -> float:
    meta = gt["metric_meta"].get(metric_id, {})
    if meta.get("tolerance") is not None:
        return float(meta["tolerance"])

    suffix_map = {
        "_organic_cc_growth_pct": "organic_cc_pct_strict",
        "_reported_growth_pct": "reported_growth_pct",
        "_fx_impact_pct": "fx_impact_pct",
    }
    for suffix, policy_key in suffix_map.items():
        if metric_id.endswith(suffix) and policy_key in gt["policy_tolerances"]:
            return float(gt["policy_tolerances"][policy_key])

    if metric_id.startswith("wae_") and "wae_fx_rate" in gt["policy_tolerances"]:
        return float(gt["policy_tolerances"]["wae_fx_rate"])
    if "_net_revenue_" in metric_id and "revenue_usd_millions" in gt["policy_tolerances"]:
        return float(gt["policy_tolerances"]["revenue_usd_millions"])
    return default


def _spot_trap_triggered(values: dict, gt: dict) -> bool:
    trap = gt["spot_trap"]
    if not trap:
        return False
    return all(_get(values, metric_id) == wrong_val for metric_id, wrong_val in trap.items())


def classify_failure(values: dict, gt: dict) -> list[str]:
    modes: list[str] = []
    expected = gt["values"]
    schema = gt["schema"]

    if _spot_trap_triggered(values, gt):
        modes.append("spot_rate_method")
        return modes

    reported_trap = gt["reported_only_trap"]
    if reported_trap:
        for metric_id, wrong_val in reported_trap.items():
            if _get(values, metric_id) == wrong_val:
                modes.append("reported_only")
                break

    for segment in schema.get("segments", []):
        metrics = segment.get("metrics", {})
        rev_key = metrics.get("net_revenue_fy2025")
        if not rev_key:
            continue
        actual = _get(values, rev_key)
        exp = expected.get(rev_key)
        bounds = segment.get("revenue_bounds_usd_millions")
        if actual is None or exp is None or not bounds or len(bounds) != 2:
            continue
        if actual != exp and (actual < bounds[0] or actual > bounds[1]):
            modes.append("wrong_region")
            break

    return modes


def verify(values: dict, gt: dict) -> dict:
    expected = gt["values"]
    schema = gt["schema"]
    checks: list[dict] = []
    method_alt_metrics: list[str] = []
    computed: dict[str, float | None] = {}

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
            tol = _tolerance_for_metric(metric_id, gt)

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

    for instrument in schema.get("fx_instruments", []):
        imetrics = instrument.get("metrics", {})
        critical = instrument.get("critical", True)
        for _year, metric_id in imetrics.items():
            add(metric_id, _get(values, metric_id), critical=critical)

    for segment in schema.get("segments", []):
        slug = segment.get("slug", "segment")
        metrics = segment.get("metrics", {})
        for key in ("net_revenue_fy2024", "net_revenue_fy2025"):
            metric_id = metrics.get(key)
            if metric_id:
                add(metric_id, _get(values, metric_id))
        for key in ("reported_growth_pct", "fx_impact_pct"):
            metric_id = metrics.get(key)
            if metric_id:
                add(metric_id, _get(values, metric_id))
        organic_id = metrics.get("organic_cc_growth_pct")
        if organic_id:
            add(
                organic_id,
                _get(values, organic_id),
                critical=True,
                allow_method_alt=True,
            )

        rep_id = metrics.get("reported_growth_pct")
        fx_id = metrics.get("fx_impact_pct")
        organic_id = metrics.get("organic_cc_growth_pct")
        if rep_id and fx_id and organic_id:
            formula_key = f"{slug}_cc_formula_pct"
            rep = _get(values, rep_id)
            fx = _get(values, fx_id)
            formula_val = _organic_from_components(
                rep if rep is not None else expected.get(rep_id),
                fx if fx is not None else expected.get(fx_id),
            )
            computed[formula_key] = formula_val
            add(
                formula_key,
                formula_val,
                tol=_tolerance_for_metric(organic_id, gt, default=0.2),
                expected_key=organic_id,
            )

    all_pass = all(c["pass"] for c in checks)
    l1_pass = all(c.get("l1_pass", c["pass"]) for c in checks)
    critical_fail = any(not c.get("l1_pass", c["pass"]) and c["critical"] for c in checks)
    failure_modes = [] if l1_pass else classify_failure(values, gt)
    if method_alt_metrics and not all_pass:
        failure_modes.append("method_alt")
    fracture_codes_list = resolve_fracture_codes(failure_modes, task_id=gt["task_id"], layer="L1")

    return {
        "task_id": gt["task_id"],
        "archetype": schema.get("archetype", "fx_organic_growth"),
        "all_pass": all_pass,
        "l1_pass": l1_pass,
        "critical_fail": critical_fail,
        "method_alt_metrics": method_alt_metrics,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes_list,
        "checks": checks,
        "computed": computed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-output", type=Path, help="JSON file with agent structured output")
    parser.add_argument(
        "--ground-truth",
        type=Path,
        required=True,
        help="Ground truth JSON with verification_schema",
    )
    args = parser.parse_args(argv)

    gt = load_ground_truth(args.ground_truth)
    if not gt["schema"].get("segments"):
        print(json.dumps({"error": "verification_schema.segments missing from ground truth"}), file=sys.stderr)
        return 2

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt["values"]

    report = verify(values, gt)
    print(json.dumps(report, indent=2))
    return 0 if report["l1_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
