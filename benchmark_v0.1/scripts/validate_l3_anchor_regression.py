#!/usr/bin/env python3
"""L3 anchor regression — GT + submission-gold citations vs bundle excerpts (P3-36)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent
ROOT = BENCH.parent

sys.path.insert(0, str(SCRIPTS))

from l3_citation_rules import anchor_ok, derive_row_label_from_snippet  # noqa: E402
from task_registry import (  # noqa: E402
    load_bundle,
    load_ground_truth,
    published_task_ids,
)
from validate_agent_submission import (  # noqa: E402
    excerpt_for_slug,
    snippet_present,
    validate_submission,
)


def check_gt_citations(task_id: str) -> list[dict]:
    gt_doc = load_ground_truth(task_id)
    bundle = load_bundle(task_id)
    results: list[dict] = []

    for item in gt_doc.get("extracted_values", []):
        mid = item.get("metric_id", "?")
        cite = item.get("citation") or {}
        snippet = cite.get("snippet")
        section_slug = cite.get("section_slug")
        if not snippet:
            results.append({
                "task_id": task_id,
                "metric_id": mid,
                "check": "gt_snippet_present",
                "pass": False,
            })
            continue
        if not section_slug:
            results.append({
                "task_id": task_id,
                "metric_id": mid,
                "check": "gt_section_slug",
                "pass": True,
                "detail": "optional for non-strict tasks",
            })
            excerpt_ok = True
        else:
            excerpt = excerpt_for_slug(bundle, section_slug)
            excerpt_ok = bool(excerpt and snippet_present(excerpt, snippet))
            results.append({
                "task_id": task_id,
                "metric_id": mid,
                "check": "gt_snippet_in_excerpt",
                "pass": excerpt_ok,
                "section_slug": section_slug,
            })
        if not excerpt_ok:
            continue
        derived = derive_row_label_from_snippet(snippet)
        if derived:
            anchor = {"row_label": derived}
            if section_slug:
                anchor["section_slug"] = section_slug
            ok, reason = anchor_ok(snippet, anchor, section_slug=section_slug)
            results.append({
                "task_id": task_id,
                "metric_id": mid,
                "check": f"gt_anchor.{reason or 'ok'}",
                "pass": ok,
            })
    return results


def check_submission_gold(task_id: str) -> dict | None:
    path = BENCH / "contract_fixtures" / f"{task_id}_submission_gold.json"
    if not path.exists():
        return None
    submission = json.loads(path.read_text(encoding="utf-8"))
    report = validate_submission(submission, task_id=task_id)
    return {
        "task_id": task_id,
        "submission_path": str(path),
        "l3_pass": report.get("l3_pass"),
        "failure_modes": report.get("failure_modes", []),
    }


def validate_task(task_id: str) -> dict:
    gt_checks = check_gt_citations(task_id)
    sub_report = check_submission_gold(task_id)
    gt_pass = all(c.get("pass") for c in gt_checks)
    sub_pass = sub_report is None or sub_report.get("l3_pass") is True
    return {
        "task_id": task_id,
        "all_pass": gt_pass and sub_pass,
        "gt_checks": gt_checks,
        "submission_gold": sub_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="L3 anchor regression (P3-36)")
    parser.add_argument("--task", help="Single task_id")
    parser.add_argument("--all", action="store_true", help="All published tasks")
    args = parser.parse_args()

    if args.all:
        task_ids = published_task_ids()
    elif args.task:
        task_ids = [args.task]
    else:
        parser.error("Specify --task or --all")

    reports = [validate_task(tid) for tid in task_ids]
    all_pass = all(r["all_pass"] for r in reports)
    print(json.dumps({"all_pass": all_pass, "tasks": reports}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
