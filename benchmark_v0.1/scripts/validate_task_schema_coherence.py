#!/usr/bin/env python3
"""Task metric-schema coherence gate (P3-37).

Asserts that every artifact deriving from a task's implicit metric schema
(task structured_fields, GT metric_ids, gold-path L3 anchors/computed
citations, scripted plan submission) agrees. Catches rename drift of the
kind P3-35 had to fix by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent

sys.path.insert(0, str(SCRIPTS))

from agents.benchmark_tool_specs import validate_task_metrics  # noqa: E402
from archetype_roles import VERIFY_ONLY_METRICS, gt_metric_values  # noqa: E402
from task_registry import (  # noqa: E402
    load_gold_path,
    load_ground_truth,
    load_task,
    published_task_ids,
    scripted_plan_path,
)


def gt_metric_ids(gt_doc: dict) -> dict[str, str]:
    """metric_id -> GT section (extracted_values / computed_values)."""
    ids: dict[str, str] = {}
    for section in ("extracted_values", "computed_values"):
        for item in gt_doc.get(section, []):
            mid = item.get("metric_id")
            if mid:
                ids[mid] = section
    return ids


def validate_task_coherence(task_id: str) -> dict:
    checks: list[dict] = []

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": ok, "detail": detail})

    task = load_task(task_id)
    structured = list(task.get("expected_outputs", {}).get("structured_fields") or [])
    sf = set(structured)
    record("structured_fields_present", bool(sf), f"{len(sf)} fields")
    record(
        "structured_fields_unique",
        len(structured) == len(sf),
        "" if len(structured) == len(sf) else "duplicate entries",
    )

    gt_ids = gt_metric_ids(load_ground_truth(task_id))

    # Every scored structured_field must exist in GT (verify-only fields are
    # produced by the verify script, not extracted/computed GT values).
    missing_gt = sorted(sf - set(gt_ids) - VERIFY_ONLY_METRICS)
    record("structured_fields_have_gt", not missing_gt, f"missing in GT: {missing_gt}" if missing_gt else "")

    # Orphaned *extracted* GT metrics signal rename drift; computed
    # intermediates (e.g. AMZN segment_net_sales_sum) are allowed.
    orphans = {mid: sec for mid, sec in gt_ids.items() if mid not in sf and mid not in VERIFY_ONLY_METRICS}
    extracted_orphans = sorted(m for m, sec in orphans.items() if sec == "extracted_values")
    computed_orphans = sorted(m for m, sec in orphans.items() if sec == "computed_values")
    record(
        "no_orphan_extracted_gt_metrics",
        not extracted_orphans,
        f"extracted GT metrics not in structured_fields: {extracted_orphans}" if extracted_orphans else "",
    )
    if computed_orphans:
        record("computed_intermediates", True, f"unscored intermediates: {computed_orphans}")

    l3_rules = load_gold_path(task_id).get("l3_citation_rules", {})
    bad_anchors = sorted(set(l3_rules.get("metric_citation_anchors", {})) - sf)
    record(
        "l3_anchor_keys_in_schema",
        not bad_anchors,
        f"anchor keys not in structured_fields: {bad_anchors}" if bad_anchors else "",
    )

    computed_cites = l3_rules.get("computed_citations", {})
    bad_keys = sorted(set(computed_cites) - sf)
    record(
        "computed_citation_keys_in_schema",
        not bad_keys,
        f"computed_citations keys not in structured_fields: {bad_keys}" if bad_keys else "",
    )
    bad_targets = sorted(
        spec["cite_metric"]
        for spec in computed_cites.values()
        if spec.get("cite_metric") and spec["cite_metric"] not in sf
    )
    record(
        "computed_citation_targets_in_schema",
        not bad_targets,
        f"cite_metric not in structured_fields: {bad_targets}" if bad_targets else "",
    )

    plan_path = scripted_plan_path(task_id)
    if plan_path and plan_path.exists():
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        submits = [a for a in plan.get("actions", []) if a.get("type") == "submit_structured_output"]
        if submits:
            try:
                validate_task_metrics(submits[-1].get("structured_output") or {}, task_id)
                record("scripted_plan_submit_schema", True)
            except ValueError as exc:
                record("scripted_plan_submit_schema", False, str(exc))
        else:
            record("scripted_plan_submit_schema", False, "no submit_structured_output action")
    else:
        record("scripted_plan_submit_schema", False, "scripted plan missing")

    # GT scored values must resolve for every non-verify-only field.
    scored = gt_metric_values(task_id)
    unresolved = sorted((sf - VERIFY_ONLY_METRICS) - set(scored))
    record("gt_values_resolve", not unresolved, f"no GT value: {unresolved}" if unresolved else "")

    all_pass = all(c["pass"] for c in checks)
    return {"task_id": task_id, "all_pass": all_pass, "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Task metric-schema coherence (P3-37)")
    parser.add_argument("--task", help="Single task_id")
    parser.add_argument("--all", action="store_true", help="All published tasks")
    args = parser.parse_args()

    if args.all:
        task_ids = published_task_ids()
    elif args.task:
        task_ids = [args.task]
    else:
        parser.error("Specify --task or --all")

    reports = [validate_task_coherence(tid) for tid in task_ids]
    all_pass = all(r["all_pass"] for r in reports)
    print(json.dumps({"all_pass": all_pass, "tasks": reports}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
