#!/usr/bin/env python3
"""
Score benchmark eval campaign runs via task verify scripts (P2-04).

Expects agent structured-output JSON files:
  runs/{campaign_id}/{model_slug}/{task_id}_run{01..N}.json

Usage:
  python run_benchmark_campaign.py --bootstrap-fixtures   # gold outputs for smoke test
  python run_benchmark_campaign.py --campaign ../campaigns/pilot_eval_campaign_v1.json
  python run_benchmark_campaign.py --execute --agent scripted   # CI smoke (no API key)
  python run_benchmark_campaign.py --execute --agent openai     # live eval (OPENAI_API_KEY)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

BENCH = Path(__file__).resolve().parent.parent
SCRIPTS = BENCH / "scripts"

sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import (  # noqa: E402
    bootstrap_fixtures,
    load_json,
    model_slug,
)


def published_tasks(manifest: dict) -> dict[str, dict]:
    return {
        t["task_id"]: t
        for t in manifest.get("pilot_tasks", [])
        if t.get("status") == "published"
    }


def verify_cmd(task_entry: dict, agent_path: Path) -> list[str]:
    task_id = task_entry["task_id"]
    paths = task_entry["paths"]
    if task_id == "GOOGL_footnote_reconciliation":
        script = BENCH / paths["verify_script"]
        return [
            sys.executable,
            str(script),
            "--period",
            "q1_2026",
            "--agent-output",
            str(agent_path),
        ]
    if task_id == "PEP_fx_organic_growth":
        script = BENCH / paths.get("verify_script_task_entry", paths["verify_script"])
        gt = BENCH / paths["ground_truth"]
        return [
            sys.executable,
            str(script),
            "--ground-truth",
            str(gt),
            "--agent-output",
            str(agent_path),
        ]
    raise ValueError(f"No verify command for task {task_id}")


def run_verify(task_entry: dict, agent_path: Path) -> dict:
    cmd = verify_cmd(task_entry, agent_path)
    proc = subprocess.run(cmd, cwd=BENCH, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        return {
            "error": proc.stderr.strip() or proc.stdout.strip(),
            "exit_code": proc.returncode,
        }
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"error": "invalid verify JSON", "raw": proc.stdout[:500]}
    report["verify_exit_code"] = proc.returncode
    return report


def execute_campaign(
    campaign: dict,
    manifest: dict,
    *,
    agent_mode: str,
    models: list[str] | None = None,
    tasks: list[str] | None = None,
    skip_existing: bool = False,
) -> list[dict]:
    """Run agent loop for each campaign slot; return execution records."""
    from benchmark_agent_loop import (
        TASK_SCRIPTED_PLANS,
        resolve_output_paths,
        run_mock_task,
        run_openai_task,
        run_scripted_task,
        write_outputs,
    )

    pub = published_tasks(manifest)
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)
    exec_records: list[dict] = []

    model_list = models or campaign["models"]
    task_list = tasks or campaign["tasks"]

    for model_id in model_list:
        for task_id in task_list:
            if task_id not in pub:
                exec_records.append({
                    "model_id": model_id,
                    "task_id": task_id,
                    "status": "skipped",
                    "reason": "task not published",
                })
                continue
            for run in range(1, campaign["runs_per_task"] + 1):
                agent_path, trace_path = resolve_output_paths(
                    task_id,
                    run,
                    out_dir=None,
                    campaign=campaign,
                    model_id=model_id,
                )
                rec = {
                    "model_id": model_id,
                    "task_id": task_id,
                    "run_index": run,
                    "agent_output": str(agent_path),
                    "agent_mode": agent_mode,
                }
                if skip_existing and agent_path.exists() and trace_path.exists():
                    rec["status"] = "skipped_existing"
                    exec_records.append(rec)
                    continue
                try:
                    if agent_mode == "scripted":
                        plan = TASK_SCRIPTED_PLANS.get(task_id)
                        if not plan or not plan.exists():
                            raise FileNotFoundError(f"No scripted plan for {task_id}")
                        trace, structured_output = run_scripted_task(
                            task_id, plan, model_id=model_id
                        )
                    elif agent_mode == "openai":
                        trace, structured_output = run_openai_task(task_id, model_id=model_id)
                    elif agent_mode == "mock":
                        if task_id != "GOOGL_footnote_reconciliation":
                            raise NotImplementedError("mock execute supports GOOGL only")
                        trace, structured_output = run_mock_task(task_id)
                    else:
                        raise ValueError(f"Unknown agent mode {agent_mode!r}")
                    write_outputs(structured_output, trace, agent_path, trace_path)
                    rec["status"] = "executed"
                    rec["termination"] = trace.get("termination")
                except Exception as e:
                    rec["status"] = "error"
                    rec["error"] = str(e)
                exec_records.append(rec)
    return exec_records


def score_campaign(campaign: dict, manifest: dict) -> dict:
    pub = published_tasks(manifest)
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    run_records: list[dict] = []

    for model_id in campaign["models"]:
        for task_id in campaign["tasks"]:
            if task_id not in pub:
                continue
            task_entry = pub[task_id]
            for run in range(1, campaign["runs_per_task"] + 1):
                agent_path = runs_dir / model_slug(model_id) / f"{task_id}_run{run:02d}.json"
                try:
                    agent_rel = str(agent_path.relative_to(BENCH.parent))
                except ValueError:
                    agent_rel = str(agent_path)
                rec = {
                    "model_id": model_id,
                    "task_id": task_id,
                    "run_index": run,
                    "agent_output": agent_rel,
                    "agent_output_exists": agent_path.exists(),
                }
                if not agent_path.exists():
                    rec["status"] = "missing"
                    run_records.append(rec)
                    continue
                report = run_verify(task_entry, agent_path)
                rec["verify"] = report
                rec["l1_all_pass"] = report.get("all_pass")
                rec["l1_pass"] = report.get("l1_pass", report.get("all_pass"))
                rec["failure_modes"] = report.get("failure_modes", [])
                rec["fracture_codes"] = report.get("fracture_codes", [])
                rec["status"] = "scored"
                run_records.append(rec)

    scored = [r for r in run_records if r.get("status") == "scored"]
    l1_rates = [
        1.0 if r.get("l1_all_pass") else (0.5 if r.get("l1_pass") else 0.0)
        for r in scored
    ]
    fractures: dict[str, int] = {}
    for r in scored:
        for code in r.get("fracture_codes") or []:
            fractures[code] = fractures.get(code, 0) + 1

    by_task: dict[str, list[float]] = {}
    for r in scored:
        rate = 1.0 if r.get("l1_all_pass") else (0.5 if r.get("l1_pass") else 0.0)
        by_task.setdefault(r["task_id"], []).append(rate)

    return {
        "campaign_id": campaign["campaign_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": campaign.get("status"),
        "models": campaign["models"],
        "tasks": campaign["tasks"],
        "runs_per_task": campaign["runs_per_task"],
        "execution": campaign.get("_execution"),
        "summary": {
            "run_slots": len(run_records),
            "scored": len(scored),
            "missing": sum(1 for r in run_records if r.get("status") == "missing"),
            "l1_all_pass_count": sum(1 for r in scored if r.get("l1_all_pass")),
            "l1_pass_rate_median": median(l1_rates) if l1_rates else None,
            "by_task_l1_pass_rate_median": {
                tid: median(rates) if rates else None for tid, rates in by_task.items()
            },
            "fracture_counts": fractures,
        },
        "runs": run_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score benchmark eval campaign (P2-04)")
    parser.add_argument(
        "--campaign",
        type=Path,
        default=BENCH / "campaigns" / "pilot_eval_campaign_v1.json",
    )
    parser.add_argument(
        "--bootstrap-fixtures",
        action="store_true",
        help="Write gold agent outputs for all model×task×run slots",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run agent loop for each campaign slot before scoring",
    )
    parser.add_argument(
        "--agent",
        choices=("scripted", "mock", "openai"),
        default="openai",
        help="Agent mode when --execute (default: openai)",
    )
    parser.add_argument(
        "--models",
        help="Comma-separated model ids to run (default: all in campaign config)",
    )
    parser.add_argument(
        "--tasks",
        help="Comma-separated task ids to run (default: all in campaign config)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip execute when agent output file already exists",
    )
    args = parser.parse_args()

    campaign_path = args.campaign if args.campaign.is_absolute() else BENCH / args.campaign
    campaign = load_json(campaign_path)
    manifest = load_json(BENCH / "manifest.json")

    if args.bootstrap_fixtures:
        paths = bootstrap_fixtures(campaign)
        print(f"Wrote {len(paths)} fixture agent outputs under {campaign['runs_dir']}")

    if args.execute:
        if args.agent == "openai" and not __import__("os").environ.get("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY not set for --execute --agent openai", file=sys.stderr)
            return 1
        model_filter = [m.strip() for m in args.models.split(",")] if args.models else None
        task_filter = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
        exec_records = execute_campaign(
            campaign,
            manifest,
            agent_mode=args.agent,
            models=model_filter,
            tasks=task_filter,
            skip_existing=args.skip_existing,
        )
        campaign = {**campaign, "_execution": exec_records}
        errors = [r for r in exec_records if r.get("status") == "error"]
        executed = sum(1 for r in exec_records if r.get("status") == "executed")
        print(f"Execute: {executed} runs, {len(errors)} errors")
        for err in errors[:5]:
            print(f"  ERROR {err['task_id']} run {err['run_index']}: {err.get('error')}", file=sys.stderr)
        if errors:
            return 1

    result = score_campaign(campaign, manifest)
    out_dir = (BENCH / campaign["runs_dir"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{campaign['campaign_id']}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    try:
        rel = out_path.relative_to(BENCH.parent)
    except ValueError:
        rel = out_path
    print(f"\nWrote {rel}")
    return 0 if result["summary"]["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
