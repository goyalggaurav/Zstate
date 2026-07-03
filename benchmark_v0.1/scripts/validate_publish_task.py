#!/usr/bin/env python3
"""Publish gate for Track A tasks (P3-23) — run before setting status: published."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parent
SCRIPTS = BENCH / "scripts"

sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import l1_values_from_gt, submission_from_gt  # noqa: E402
from agents.benchmark_tool_specs import parse_submission_args, validate_task_metrics  # noqa: E402
from task_registry import (  # noqa: E402
    headline_eligible,
    load_task,
    manifest_entry,
    published_task_ids,
)


def run_json(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "command failed").strip())
    return json.loads(proc.stdout)


def validate_publish_task(task_id: str) -> dict:
    checks: list[dict] = []
    entry = manifest_entry(task_id)
    status = entry.get("status")
    paths = entry.get("paths", {})

    def record(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": ok, "detail": detail})

    for key in ("task", "ground_truth", "gold_path", "grader_rubric", "corpus_bundle", "verify_script"):
        rel = paths.get(key)
        ok = bool(rel and (BENCH / rel).exists())
        record(f"path:{key}", ok, rel or "missing")

    cfa = entry.get("cfa_review")
    if cfa:
        cfa_path = ROOT / cfa
        record("cfa_review_doc", cfa_path.exists(), str(cfa))

    try:
        manifest_report = run_json([sys.executable, str(SCRIPTS / "validate_manifest.py")])
        task_checks = [c for c in manifest_report.get("checks", []) if c.get("task_id") == task_id]
        record("validate_manifest", all(c.get("pass") for c in task_checks), f"{len(task_checks)} paths")
    except RuntimeError as exc:
        record("validate_manifest", False, str(exc))

    try:
        bundle_report = run_json([
            sys.executable,
            str(SCRIPTS / "validate_corpus_bundle.py"),
            "--task",
            task_id,
        ])
        record("validate_corpus_bundle", bundle_report.get("all_pass", False))
    except RuntimeError as exc:
        record("validate_corpus_bundle", False, str(exc))

    metrics = l1_values_from_gt(task_id)
    record("gt_l1_metrics", bool(metrics), f"{len(metrics)} metrics")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(metrics, tmp)
        agent_path = tmp.name
    try:
        l1_report = run_json([
            sys.executable,
            str(SCRIPTS / "verify_benchmark_l1.py"),
            "--task",
            task_id,
            "--agent-output",
            agent_path,
        ])
        record("l1_verify_gt_metrics", l1_report.get("all_pass", False), str(l1_report.get("fracture_codes")))
    except RuntimeError as exc:
        record("l1_verify_gt_metrics", False, str(exc))
    finally:
        Path(agent_path).unlink(missing_ok=True)

    task = load_task(task_id)
    try:
        validate_task_metrics(metrics, task_id)
        record("submit_schema_keys", True)
    except ValueError as exc:
        record("submit_schema_keys", False, str(exc))

    submission = submission_from_gt(task_id)
    try:
        parse_submission_args(
            {
                "metrics": submission["metrics"],
                "citations": submission.get("citations") or [],
                "policy_acknowledgements": submission.get("policy_acknowledgements", []),
            },
            task,
        )
        record("parse_submission_args", True)
    except ValueError as exc:
        record("parse_submission_args", False, str(exc))

    gold_fixture = BENCH / "contract_fixtures" / f"{task_id}_gold.json"
    if gold_fixture.exists():
        fixture = json.loads(gold_fixture.read_text(encoding="utf-8"))
        record("contract_gold_l1_parity", fixture == metrics, str(gold_fixture.name))
    else:
        record("contract_gold_l1_parity", False, "missing contract fixture")

    sub_fixture = BENCH / "contract_fixtures" / f"{task_id}_submission_gold.json"
    if sub_fixture.exists():
        fixture = json.loads(sub_fixture.read_text(encoding="utf-8"))
        fixture_metrics = fixture.get("metrics") or {}
        record(
            "contract_submission_metrics_parity",
            all(metrics.get(k) == v for k, v in fixture_metrics.items()),
            str(sub_fixture.name),
        )
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
            json.dump(fixture, tmp)
            sub_path = tmp.name
        try:
            l3_report = run_json([
                sys.executable,
                str(SCRIPTS / "validate_agent_submission.py"),
                "--task",
                task_id,
                "--submission",
                sub_path,
            ])
            record("l3_submission_fixture", l3_report.get("l3_pass", False))
        except RuntimeError as exc:
            record("l3_submission_fixture", False, str(exc))
        finally:
            Path(sub_path).unlink(missing_ok=True)
    else:
        record("contract_submission_metrics_parity", status != "published", "missing submission fixture")

    try:
        anchor_report = run_json([
            sys.executable,
            str(SCRIPTS / "validate_l3_anchor_regression.py"),
            "--task",
            task_id,
        ])
        record("l3_anchor_regression", anchor_report.get("all_pass", False))
    except RuntimeError as exc:
        record("l3_anchor_regression", False, str(exc))

    try:
        coherence_report = run_json([
            sys.executable,
            str(SCRIPTS / "validate_task_schema_coherence.py"),
            "--task",
            task_id,
        ])
        failed = [
            c["check"]
            for t in coherence_report.get("tasks", [])
            for c in t.get("checks", [])
            if not c.get("pass")
        ]
        record("schema_coherence", coherence_report.get("all_pass", False), ", ".join(failed))
    except RuntimeError as exc:
        record("schema_coherence", False, str(exc))

    scripted = paths.get("scripted_plan")
    if status == "published":
        record("scripted_plan", bool(scripted and (BENCH / scripted).exists()), scripted or "required for published")
    elif scripted:
        record("scripted_plan", (BENCH / scripted).exists(), scripted)

    record(
        "headline_eligible_flag",
        "headline_eligible" in entry,
        f"headline_eligible={headline_eligible(task_id)}",
    )

    all_pass = all(c["pass"] for c in checks)
    return {
        "task_id": task_id,
        "status": status,
        "checks": checks,
        "all_pass": all_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate task is ready to publish (P3-23)")
    parser.add_argument("--task", required=True, help="Task id (e.g. KO_footnote_reconciliation)")
    args = parser.parse_args()

    try:
        report = validate_publish_task(args.task)
    except ValueError as exc:
        print(json.dumps({"task_id": args.task, "error": str(exc), "all_pass": False}, indent=2))
        return 1

    print(json.dumps(report, indent=2))
    if not report["all_pass"]:
        failed = [c for c in report["checks"] if not c["pass"]]
        print(f"\nFAILED {len(failed)} check(s):", file=sys.stderr)
        for item in failed:
            print(f"  - {item['check']}: {item.get('detail', '')}", file=sys.stderr)
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
