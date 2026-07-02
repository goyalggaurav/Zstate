#!/usr/bin/env python3
"""
Unified Layer 1 verification — routes by task archetype (P2-14).

Usage:
  python verify_benchmark_l1.py --task GOOGL_footnote_reconciliation --agent-output run.json
  python verify_benchmark_l1.py --task AMZN_footnote_reconciliation
  python verify_benchmark_l1.py --task PEP_fx_organic_growth --agent-output run.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from archetype_roles import ground_truth_path, task_archetype  # noqa: E402

_FISCAL_PERIOD_MAP = {
    "2026Q1": "q1_2026",
    "FY2025": "fy2025",
}


def default_verify_period(task_id: str) -> str | None:
    """Map task GT fiscal_period to verifier --period token when applicable."""
    if task_archetype(task_id) != "F_adjustment":
        return None
    gt_path = ground_truth_path(task_id)
    doc = json.loads(gt_path.read_text(encoding="utf-8"))
    fiscal = doc.get("fiscal_period", "")
    return _FISCAL_PERIOD_MAP.get(fiscal)


def verify_task(task_id: str, values: dict, *, period: str | None = None) -> dict:
    archetype = task_archetype(task_id)
    gt_path = ground_truth_path(task_id)

    if archetype == "F_adjustment":
        from verify_googl_footnote_reconciliation import load_ground_truth, verify

        verify_period = period or default_verify_period(task_id) or "q1_2026"
        gt_doc = load_ground_truth(gt_path, period=verify_period)
        report = verify(values, gt_doc)
        report["task_id"] = task_id
        report["period"] = verify_period
        return report

    if archetype == "F_exact":
        from verify_amzn_footnote_reconciliation import load_ground_truth, verify

        gt_doc = load_ground_truth(gt_path)
        report = verify(values, gt_doc)
        report["task_id"] = task_id
        return report

    if archetype == "M_organic":
        from verify_fx_organic_growth import load_ground_truth, verify as verify_organic

        gt_doc = load_ground_truth(gt_path)
        report = verify_organic(values, gt_doc)
        report["task_id"] = task_id
        report["archetype"] = archetype
        return report

    if archetype == "F_guidance_drift":
        from verify_guidance_drift import load_ground_truth, verify as verify_guidance

        gt_doc = load_ground_truth(gt_path)
        report = verify_guidance(values, gt_doc)
        report["task_id"] = task_id
        report["archetype"] = archetype
        return report

    raise ValueError(f"No L1 verifier for archetype {archetype!r}")


def default_gold_values(task_id: str, *, period: str | None = None) -> dict:
    archetype = task_archetype(task_id)
    gt_path = ground_truth_path(task_id)

    if archetype == "F_adjustment":
        from verify_googl_footnote_reconciliation import load_ground_truth

        verify_period = period or default_verify_period(task_id) or "q1_2026"
        gt = load_ground_truth(gt_path, period=verify_period)
        return gt["values"]
    if archetype == "F_exact":
        from verify_amzn_footnote_reconciliation import load_ground_truth

        gt = load_ground_truth(gt_path)
        return gt["values"]
    if archetype == "M_organic":
        from verify_fx_organic_growth import load_ground_truth

        gt = load_ground_truth(gt_path)
        return gt["values"]
    if archetype == "F_guidance_drift":
        from verify_guidance_drift import load_ground_truth

        gt = load_ground_truth(gt_path)
        vals = {k: v for k, v in gt["values"].items() if not isinstance(v, bool)}
        if "guidance_pace_under" in gt["values"]:
            vals["guidance_pace_under"] = gt["values"]["guidance_pace_under"]
        return vals
    raise ValueError(f"No default values for {task_id!r}")


def l1_verify_argv(task_id: str, agent_output: Path, *, period: str | None = None) -> list[str]:
    """Build subprocess argv for unified L1 verify (P3-16 — no task_id sprawl)."""
    cmd = [
        sys.executable,
        str(SCRIPTS / "verify_benchmark_l1.py"),
        "--task",
        task_id,
        "--agent-output",
        str(agent_output),
    ]
    verify_period = period or default_verify_period(task_id)
    if verify_period:
        cmd.extend(["--period", verify_period])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified benchmark L1 verify (archetype router)")
    parser.add_argument("--task", required=True, help="Task id, e.g. GOOGL_footnote_reconciliation")
    parser.add_argument("--agent-output", type=Path, help="Agent structured-output JSON")
    parser.add_argument(
        "--period",
        choices=("q1_2026", "fy2025"),
        help="Optional period override for F_adjustment tasks",
    )
    args = parser.parse_args()

    if args.agent_output and args.agent_output.exists():
        values = json.loads(args.agent_output.read_text())
    else:
        values = default_gold_values(args.task, period=args.period)

    report = verify_task(args.task, values, period=args.period)
    print(json.dumps(report, indent=2))
    return 0 if report.get("all_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
