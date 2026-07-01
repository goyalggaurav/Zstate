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


def verify_task(task_id: str, values: dict, *, period: str | None = None) -> dict:
    archetype = task_archetype(task_id)

    if archetype == "F_adjustment":
        from verify_googl_footnote_reconciliation import GT_FY2025, GT_Q1_2026, verify

        gt = GT_FY2025 if period == "fy2025" else GT_Q1_2026
        report = verify(values, gt)
        report["task_id"] = task_id
        report["archetype"] = archetype
        if period:
            report["period"] = period
        return report

    if archetype == "F_exact":
        from verify_amzn_footnote_reconciliation import GT_FY2025, verify

        report = verify(values, GT_FY2025)
        report["task_id"] = task_id
        report["archetype"] = archetype
        return report

    if archetype == "M_organic":
        from verify_fx_organic_growth import load_ground_truth, verify as verify_organic

        gt_doc = load_ground_truth(ground_truth_path(task_id))
        report = verify_organic(values, gt_doc)
        report["task_id"] = task_id
        report["archetype"] = archetype
        return report

    raise ValueError(f"No L1 verifier for archetype {archetype!r}")


def default_gold_values(task_id: str, *, period: str | None = None) -> dict:
    archetype = task_archetype(task_id)
    if archetype == "F_adjustment":
        from verify_googl_footnote_reconciliation import GT_FY2025, GT_Q1_2026

        return GT_FY2025 if period == "fy2025" else GT_Q1_2026
    if archetype == "F_exact":
        from verify_amzn_footnote_reconciliation import GT_FY2025

        return GT_FY2025
    if archetype == "M_organic":
        from verify_fx_organic_growth import load_ground_truth

        gt = load_ground_truth(ground_truth_path(task_id))
        return gt["values"]
    raise ValueError(f"No default values for {task_id!r}")


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
