#!/usr/bin/env python3
"""
Composite benchmark run scoring — L1 verify + L2 section recall + L3 submission (P2-04e).

Usage:
  python score_benchmark_run.py \\
    --task GOOGL_footnote_reconciliation \\
    --agent-output ../contract_fixtures/GOOGL_footnote_reconciliation_gold.json \\
    --trace /tmp/GOOGL_footnote_reconciliation_run01_trace.json \\
    --submission ../contract_fixtures/GOOGL_footnote_reconciliation_submission_gold.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent

sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import load_json  # noqa: E402
from benchmark_tool_backend import load_bundle, normalize_section_slug  # noqa: E402
from validate_agent_submission import validate_submission  # noqa: E402

L2_FAILURE_FRACTURE = {
    "section_miss": "SECTION_MISS",
    "section_partial": "SECTION_MISS",
}


def load_task(task_id: str) -> dict:
    return load_json(BENCH / "tasks" / f"{task_id}.json")


def load_gold_path(task_id: str) -> dict:
    manifest = load_json(BENCH / "manifest.json")
    for entry in manifest.get("pilot_tasks", []):
        if entry["task_id"] == task_id:
            return load_json(BENCH / entry["paths"]["gold_path"])
    raise ValueError(f"No gold path for task {task_id!r}")


def run_l1_verify(task_id: str, agent_path: Path, manifest: dict) -> dict:
    for entry in manifest.get("pilot_tasks", []):
        if entry["task_id"] != task_id:
            continue
        paths = entry["paths"]
        if task_id == "GOOGL_footnote_reconciliation":
            script = BENCH / paths["verify_script"]
            cmd = [
                sys.executable,
                str(script),
                "--period",
                "q1_2026",
                "--agent-output",
                str(agent_path),
            ]
        elif task_id == "PEP_fx_organic_growth":
            script = BENCH / paths.get("verify_script_task_entry", paths["verify_script"])
            gt = BENCH / paths["ground_truth"]
            cmd = [
                sys.executable,
                str(script),
                "--ground-truth",
                str(gt),
                "--agent-output",
                str(agent_path),
            ]
        else:
            raise ValueError(f"No verify script for {task_id!r}")
        proc = subprocess.run(cmd, cwd=BENCH, capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            return {"error": proc.stderr.strip() or proc.stdout.strip(), "exit_code": proc.returncode}
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return {"error": "invalid verify JSON", "raw": proc.stdout[:500]}
        report["verify_exit_code"] = proc.returncode
        return report
    raise ValueError(f"Task {task_id!r} not in manifest")


def required_section_slugs(bundle: dict) -> list[str]:
    slugs = [
        entry["section_slug"]
        for entry in bundle.get("section_registry", [])
        if entry.get("required", True)
    ]
    return slugs


def sections_accessed_from_trace(trace: dict) -> set[str]:
    accessed: set[str] = set()
    for entry in trace.get("tool_log", []):
        if entry.get("tool") not in ("Search_Filing", "PDF_Parser"):
            continue
        slug = entry.get("section_slug")
        if slug:
            accessed.add(slug)
            continue
        section = entry.get("input", {}).get("section")
        if section and not str(entry.get("output", "")).startswith("NOT FOUND"):
            accessed.add(normalize_section_slug(section))
    for step in trace.get("steps", []):
        if step.get("type") != "tool_call":
            continue
        if step.get("tool") not in ("Search_Filing", "PDF_Parser"):
            continue
        out = step.get("output", "")
        if str(out).startswith("NOT FOUND"):
            continue
        slug = step.get("section_slug")
        if slug:
            accessed.add(slug)
            continue
        section = step.get("input", {}).get("section")
        if section:
            accessed.add(normalize_section_slug(section))
    return accessed


def score_l2_section_recall(trace: dict | None, *, task_id: str, gold_path: dict, bundle: dict) -> dict:
    required = required_section_slugs(bundle)
    if not required:
        return {
            "l2_pass": True,
            "l2_score": 1.0,
            "required_sections": [],
            "accessed_sections": [],
            "failure_modes": [],
            "fracture_codes": [],
            "status": "skipped",
        }
    if trace is None:
        return {
            "l2_pass": False,
            "l2_score": 0.0,
            "required_sections": required,
            "accessed_sections": [],
            "failure_modes": ["section_miss"],
            "fracture_codes": ["SECTION_MISS"],
            "status": "missing_trace",
        }

    accessed = sorted(sections_accessed_from_trace(trace))
    accessed_set = set(accessed)
    missing = [s for s in required if s not in accessed_set]
    recall_cfg = gold_path.get("section_recall_scoring", {})

    if not missing:
        l2_score = 1.0
        failure_modes: list[str] = []
    elif (
        len(missing) == len(required) - 1
        and "note_15" in accessed_set
        and recall_cfg.get("partial_credit_if_note_15_only") is not None
        and "note_15" in required
    ):
        l2_score = float(recall_cfg["partial_credit_if_note_15_only"])
        failure_modes = ["section_partial"]
    else:
        l2_score = (len(required) - len(missing)) / len(required)
        failure_modes = ["section_miss"] if missing else []

    l2_pass = l2_score >= 1.0
    fracture_codes = list(dict.fromkeys(
        L2_FAILURE_FRACTURE[m] for m in failure_modes if m in L2_FAILURE_FRACTURE
    ))

    return {
        "l2_pass": l2_pass,
        "l2_score": round(l2_score, 4),
        "required_sections": required,
        "accessed_sections": accessed,
        "missing_sections": missing,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
        "status": "scored",
    }


def score_l3_submission(submission: dict | None, *, task_id: str) -> dict:
    if submission is None:
        return {
            "l3_pass": False,
            "l3_score": 0.0,
            "failure_modes": ["submission_missing"],
            "fracture_codes": ["CITE_BROAD"],
            "status": "missing_submission",
        }
    report = validate_submission(submission, task_id=task_id)
    l3_score = 1.0 if report["l3_pass"] else 0.0
    return {
        "l3_pass": report["l3_pass"],
        "l3_score": l3_score,
        "failure_modes": report.get("failure_modes", []),
        "fracture_codes": report.get("fracture_codes", []),
        "status": "scored",
        "validation": report,
    }


def l1_normalized_score(l1_report: dict) -> float:
    if l1_report.get("error"):
        return 0.0
    if l1_report.get("all_pass"):
        return 1.0
    if l1_report.get("l1_pass", l1_report.get("all_pass")):
        return 0.5
    return 0.0


def layer_weights(task: dict) -> dict[str, float]:
    weights = (task.get("scoring") or {}).get("task_type_weights") or {}
    return {
        "layer1": float(weights.get("layer1", 0.55)),
        "layer2": float(weights.get("layer2", 0.25)),
        "layer3": float(weights.get("layer3", 0.20)),
    }


def composite_score(
    l1_score: float,
    l2_score: float,
    l3_score: float,
    weights: dict[str, float],
    *,
    l1_report: dict,
) -> float:
    if "sign_error" in l1_report.get("failure_modes", []):
        return 0.0
    if l1_report.get("critical_fail"):
        return 0.0
    total_w = weights["layer1"] + weights["layer2"] + weights["layer3"]
    if total_w <= 0:
        return 0.0
    raw = (
        weights["layer1"] * l1_score
        + weights["layer2"] * l2_score
        + weights["layer3"] * l3_score
    ) / total_w
    return round(raw, 4)


def score_run(
    task_id: str,
    agent_output_path: Path,
    *,
    trace_path: Path | None = None,
    submission_path: Path | None = None,
    manifest: dict | None = None,
) -> dict:
    manifest = manifest or load_json(BENCH / "manifest.json")
    task = load_task(task_id)
    gold_path = load_gold_path(task_id)
    bundle = load_bundle(task_id)
    weights = layer_weights(task)

    l1_report = run_l1_verify(task_id, agent_output_path, manifest)
    l1_score = l1_normalized_score(l1_report)

    trace = load_json(trace_path) if trace_path and trace_path.exists() else None
    submission = load_json(submission_path) if submission_path and submission_path.exists() else None

    l2_report = score_l2_section_recall(trace, task_id=task_id, gold_path=gold_path, bundle=bundle)
    l3_report = score_l3_submission(submission, task_id=task_id)

    composite = composite_score(
        l1_score,
        l2_report["l2_score"],
        l3_report["l3_score"],
        weights,
        l1_report=l1_report,
    )

    fracture_codes = list(dict.fromkeys(
        (l1_report.get("fracture_codes") or [])
        + l2_report.get("fracture_codes", [])
        + l3_report.get("fracture_codes", [])
    ))
    failure_modes = list(dict.fromkeys(
        (l1_report.get("failure_modes") or [])
        + l2_report.get("failure_modes", [])
        + l3_report.get("failure_modes", [])
    ))

    return {
        "task_id": task_id,
        "layer_weights": weights,
        "l1": {
            "score": l1_score,
            "all_pass": l1_report.get("all_pass"),
            "l1_pass": l1_report.get("l1_pass", l1_report.get("all_pass")),
            "failure_modes": l1_report.get("failure_modes", []),
            "fracture_codes": l1_report.get("fracture_codes", []),
            "report": l1_report,
        },
        "l2": l2_report,
        "l3": l3_report,
        "composite_score": composite,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
        "paths": {
            "agent_output": str(agent_output_path),
            "trace": str(trace_path) if trace_path else None,
            "submission": str(submission_path) if submission_path else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score single benchmark run (L1+L2+L3 composite)")
    parser.add_argument("--task", required=True)
    parser.add_argument("--agent-output", type=Path, required=True)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--submission", type=Path)
    args = parser.parse_args()

    agent_path = args.agent_output if args.agent_output.is_absolute() else BENCH.parent / args.agent_output
    trace_path = None
    if args.trace:
        trace_path = args.trace if args.trace.is_absolute() else BENCH.parent / args.trace
    submission_path = None
    if args.submission:
        submission_path = args.submission if args.submission.is_absolute() else BENCH.parent / args.submission

    report = score_run(args.task, agent_path, trace_path=trace_path, submission_path=submission_path)
    print(json.dumps(report, indent=2))
    ok = report["l1"].get("all_pass") is not False or report["composite_score"] >= 0
    return 0 if "error" not in report["l1"].get("report", {}) else 1


if __name__ == "__main__":
    sys.exit(main())
