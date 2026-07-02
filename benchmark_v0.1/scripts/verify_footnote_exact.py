#!/usr/bin/env python3
"""
Archetype L1 verification — footnote reconciliation (F_exact).

Segment net revenues (+ optional additive / elimination bridge lines) sum to consolidated; FX growth pair optional.
All metric IDs, tolerances, and traps load from ground truth JSON + verification_schema.

Usage:
  python verify_footnote_exact.py --ground-truth ../ground_truth/KO_footnote_reconciliation_gt.json
  python verify_footnote_exact.py --ground-truth ../ground_truth/KO_footnote_reconciliation_gt.json --agent-output agent.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fracture_registry import fracture_codes as resolve_fracture_codes, l1_map_for_task
from verify_common import is_empty_agent_output


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

    schema = doc.get("verification_schema") or {}
    refs = doc.get("reference_constants") or {}
    traps: dict[str, dict] = {}
    for mode in doc.get("failure_modes", []):
        traps[mode["id"]] = mode.get("wrong_signatures") or {}

    return {
        "task_id": doc["task_id"],
        "values": values,
        "tolerances": tolerances,
        "schema": schema,
        "traps": traps,
        "reference_constants": refs,
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


def _reconciliation_sum(
    values: dict,
    segment_metrics: list[str],
    additive_metrics: list[str] | None = None,
    elimination_metrics: list[str] | None = None,
) -> int | float | None:
    metrics = (
        list(segment_metrics)
        + list(additive_metrics or [])
        + list(elimination_metrics or [])
    )
    parts = [_get_field(values, m) for m in metrics]
    if any(p is None for p in parts):
        return None
    return sum(parts)


def _sbc_trap_triggered(values: dict, gt: dict) -> bool:
    sbc = gt["reference_constants"].get("sbc_expense_usd_m")
    if not sbc:
        return False
    consolidated_key = gt["schema"].get("consolidated_metric", "consolidated_net_sales")
    consolidated = _get_field(values, consolidated_key)
    consol_gt = gt["values"].get(consolidated_key)
    if consolidated is None or consol_gt is None:
        return False

    sig = gt["traps"].get("treat_sbc_as_segment_line_item", {})
    if sig and all(_get_field(values, k) == v for k, v in sig.items()):
        return True

    if consolidated == consol_gt + sbc:
        return True

    segment_metrics = gt["schema"].get("segment_metrics", [])
    additive_metrics = gt["schema"].get("additive_metrics") or []
    parts = [_get_field(values, m) for m in segment_metrics + additive_metrics]
    if all(p is not None for p in parts) and consolidated is not None:
        if sum(parts) + sbc == consolidated:
            return True
    return False


def classify_failure(values: dict, gt: dict) -> list[str]:
    if is_empty_agent_output(values):
        return ["submit_timeout"]

    schema = gt["schema"]
    consolidated_key = schema.get("consolidated_metric", "consolidated_net_sales")
    consolidated = _get_field(values, consolidated_key)

    wrong_period = gt["traps"].get("wrong_period", {})
    prior_key = wrong_period.get("consolidated_net_sales") or wrong_period.get("consolidated_net_revenues")
    if prior_key is not None and consolidated == prior_key:
        return ["wrong_period"]

    for mode_id, sigs in gt["traps"].items():
        if mode_id in ("wrong_period", "intl_fx_swap", "latin_fx_swap"):
            continue
        if sigs and all(_get_field(values, k) == v for k, v in sigs.items()):
            return [mode_id]

    if _sbc_trap_triggered(values, gt):
        return ["treat_sbc_as_segment_line_item"]

    fx = schema.get("fx_metrics") or {}
    rep_key = fx.get("reported")
    cc_key = fx.get("cc")
    if rep_key and cc_key:
        fx_trap = gt["traps"].get("intl_fx_swap") or gt["traps"].get("latin_fx_swap") or {}
        reported = _get_field(values, rep_key)
        cc = _get_field(values, cc_key)
        if fx_trap and reported is not None and cc is not None:
            rep_exp = fx_trap.get(rep_key)
            cc_exp = fx_trap.get(cc_key)
            if rep_exp is not None and cc_exp is not None:
                if _close(reported, rep_exp, 0.05) and _close(cc, cc_exp, 0.05):
                    return ["intl_fx_swap" if "intl_fx_swap" in gt["traps"] else "latin_fx_swap"]

    segment_metrics = schema.get("segment_metrics", [])
    additive_metrics = schema.get("additive_metrics") or []
    elimination_metrics = schema.get("elimination_metrics") or []
    segment_sum = _reconciliation_sum(
        values, segment_metrics, additive_metrics, elimination_metrics
    )
    if segment_sum is not None and consolidated is not None and segment_sum != consolidated:
        return ["segment_sum_mismatch"]

    return ["wrong_period"]


def verify(values: dict, gt: dict) -> dict:
    schema = gt["schema"]
    expected = gt["values"]
    segment_metrics = schema.get("segment_metrics", [])
    additive_metrics = schema.get("additive_metrics") or []
    elimination_metrics = schema.get("elimination_metrics") or []
    consolidated_key = schema.get("consolidated_metric", "consolidated_net_sales")
    fx = schema.get("fx_metrics") or {}

    segment_sum = _reconciliation_sum(
        values, segment_metrics, additive_metrics, elimination_metrics
    )
    consolidated = _get_field(values, consolidated_key)
    balanced = segment_sum is not None and consolidated is not None and segment_sum == consolidated

    checks: list[dict] = []

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

    for metric_id in segment_metrics + additive_metrics + elimination_metrics:
        add(metric_id, expected.get(metric_id), _get_field(values, metric_id))

    add(consolidated_key, expected.get(consolidated_key), consolidated, critical=True)

    for key in (fx.get("reported"), fx.get("cc")):
        if key and key in expected:
            add(
                key,
                expected[key],
                _get_field(values, key),
                tolerance=gt["tolerances"].get(key, 0.05),
            )

    add("segment_sum", expected.get(consolidated_key), segment_sum)
    add("reconciliation_balanced", True, balanced, critical=True)

    all_pass = all(c["pass"] for c in checks)
    critical_fail = any(not c["pass"] and c["critical"] for c in checks)
    failure_modes = [] if all_pass else classify_failure(values, gt)
    fracture_codes_list = resolve_fracture_codes(failure_modes, task_id=gt["task_id"], layer="L1")

    return {
        "task_id": gt["task_id"],
        "archetype": schema.get("archetype", "F_exact"),
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
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--agent-output", type=Path)
    args = parser.parse_args()

    gt = load_ground_truth(args.ground_truth)
    if not gt["schema"].get("segment_metrics"):
        print(json.dumps({"error": "verification_schema.segment_metrics missing"}), file=sys.stderr)
        return 2

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = gt["values"]

    report = verify(values, gt)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
