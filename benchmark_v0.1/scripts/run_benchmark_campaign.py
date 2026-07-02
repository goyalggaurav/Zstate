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
  python run_benchmark_campaign.py --execute --agent anthropic  # live eval (ANTHROPIC_API_KEY)
  python run_benchmark_campaign.py --execute --agent gemini     # live eval (GEMINI_API_KEY)
  python run_benchmark_campaign.py --execute --agent auto       # route by model id (P2-04h)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import median


def _task_weights(campaign: dict, task_list: list[str]) -> dict[str, float]:
    raw = campaign.get("task_weights") or {}
    weights = {tid: float(raw[tid]) for tid in task_list if tid in raw}
    if weights:
        return weights
    if len(task_list) <= 1:
        return {task_list[0]: 1.0} if task_list else {}
    return {tid: 1.0 for tid in task_list}


def _weighted_mean(values: dict[str, float], weights: dict[str, float]) -> float | None:
    pairs = [(values[tid], weights[tid]) for tid in weights if tid in values and values[tid] is not None]
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    if total_w <= 0:
        return None
    return sum(v * w for v, w in pairs) / total_w


def _campaign_summary(scored: list[dict], campaign: dict, task_list: list[str]) -> dict:
    l1_rates = [
        1.0 if r.get("l1_all_pass") else (0.5 if r.get("l1_pass") else 0.0)
        for r in scored
    ]
    composite_scores = [r["composite_score"] for r in scored if r.get("composite_score") is not None]
    l2_scores = [r["l2_score"] for r in scored if r.get("l2_score") is not None]
    l3_scores = [r["l3_score"] for r in scored if r.get("l3_score") is not None]
    fractures: dict[str, int] = {}
    for r in scored:
        for code in r.get("fracture_codes") or []:
            fractures[code] = fractures.get(code, 0) + 1

    by_task: dict[str, list[float]] = {}
    by_task_composite: dict[str, list[float]] = {}
    by_model_composite: dict[str, list[float]] = {}
    by_model_task_composite: dict[str, dict[str, list[float]]] = {}
    for r in scored:
        rate = 1.0 if r.get("l1_all_pass") else (0.5 if r.get("l1_pass") else 0.0)
        by_task.setdefault(r["task_id"], []).append(rate)
        if r.get("composite_score") is not None:
            by_task_composite.setdefault(r["task_id"], []).append(r["composite_score"])
            by_model_composite.setdefault(r["model_id"], []).append(r["composite_score"])
            by_model_task_composite.setdefault(r["model_id"], {}).setdefault(
                r["task_id"], []
            ).append(r["composite_score"])

    headline_tasks = resolve_campaign_headline_tasks(campaign, task_list)
    weights = _task_weights(campaign, headline_tasks)
    by_model_task_median = {
        model: {
            tid: median(rates) if rates else None
            for tid, rates in tasks.items()
        }
        for model, tasks in by_model_task_composite.items()
    }
    weighted_by_model = {
        model: _weighted_mean(
            {tid: score for tid, score in task_medians.items() if tid in headline_tasks},
            weights,
        )
        for model, task_medians in by_model_task_median.items()
        if weights
    }

    headline_scores = [
        r["composite_score"]
        for r in scored
        if r.get("composite_score") is not None and r["task_id"] in headline_tasks
    ]

    summary = {
        "run_slots": len(scored),
        "scored": len(scored),
        "missing": 0,
        "l1_all_pass_count": sum(1 for r in scored if r.get("l1_all_pass")),
        "l1_pass_rate_median": median(l1_rates) if l1_rates else None,
        "l2_score_median": median(l2_scores) if l2_scores else None,
        "l3_score_median": median(l3_scores) if l3_scores else None,
        "composite_score_median": median(composite_scores) if composite_scores else None,
        "by_task_l1_pass_rate_median": {
            tid: median(rates) if rates else None for tid, rates in by_task.items()
        },
        "by_task_composite_median": {
            tid: median(rates) if rates else None for tid, rates in by_task_composite.items()
        },
        "fracture_counts": fractures,
    }
    if headline_tasks != task_list and headline_scores:
        summary["headline_composite_score_median"] = median(headline_scores)
        summary["headline_tasks"] = list(headline_tasks)
    if by_model_composite:
        summary["by_model_composite_median"] = {
            model: median(rates) if rates else None for model, rates in by_model_composite.items()
        }
    if by_model_task_median:
        summary["by_model_task_composite_median"] = by_model_task_median
    if weighted_by_model:
        summary["weighted_composite_by_model"] = weighted_by_model
        summary["task_weights"] = weights
    return summary

BENCH = Path(__file__).resolve().parent.parent
SCRIPTS = BENCH / "scripts"

sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import (  # noqa: E402
    bootstrap_fixtures,
    load_json,
    model_slug,
    resolve_bench_path,
)
from score_benchmark_run import score_run  # noqa: E402
from agents.benchmark_tool_specs import is_anthropic_model, is_gemini_model, is_openai_model  # noqa: E402
from benchmark_eval_mode import eval_mode_enabled  # noqa: E402
from task_registry import resolve_campaign_headline_tasks  # noqa: E402


def published_tasks(manifest: dict) -> dict[str, dict]:
    return {
        t["task_id"]: t
        for t in manifest.get("pilot_tasks", [])
        if t.get("status") == "published"
    }


def verify_cmd(task_entry: dict, agent_path: Path) -> list[str]:
    from verify_benchmark_l1 import l1_verify_argv

    return l1_verify_argv(task_entry["task_id"], agent_path)


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
        resolve_output_paths,
        run_anthropic_task,
        run_gemini_task,
        run_live_task,
        run_mock_task,
        run_openai_task,
        run_scripted_task,
        write_outputs,
    )
    from task_registry import scripted_plan_path

    pub = published_tasks(manifest)
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    runs_dir.mkdir(parents=True, exist_ok=True)
    exec_records: list[dict] = []
    run_delay = float(os.environ.get("BENCHMARK_RUN_DELAY_SECONDS", "0"))
    eval_mode = eval_mode_enabled(campaign.get("eval_mode"))

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
                        plan = scripted_plan_path(task_id)
                        if not plan:
                            raise FileNotFoundError(f"No scripted plan for {task_id}")
                        trace, structured_output, agent_submission = run_scripted_task(
                            task_id, plan, model_id=model_id
                        )
                    elif agent_mode == "openai":
                        trace, structured_output, agent_submission = run_openai_task(
                            task_id, model_id=model_id, eval_mode=eval_mode
                        )
                    elif agent_mode == "anthropic":
                        trace, structured_output, agent_submission = run_anthropic_task(
                            task_id, model_id=model_id, eval_mode=eval_mode
                        )
                    elif agent_mode == "gemini":
                        trace, structured_output, agent_submission = run_gemini_task(
                            task_id, model_id=model_id, eval_mode=eval_mode
                        )
                    elif agent_mode == "auto":
                        trace, structured_output, agent_submission, routed = run_live_task(
                            task_id, model_id=model_id, eval_mode=eval_mode
                        )
                        rec["agent_mode"] = routed
                    elif agent_mode == "mock":
                        if task_id != "GOOGL_footnote_reconciliation":
                            raise NotImplementedError("mock execute supports GOOGL only")
                        trace, structured_output, agent_submission = run_mock_task(task_id)
                    else:
                        raise ValueError(f"Unknown agent mode {agent_mode!r}")
                    write_outputs(
                        structured_output,
                        trace,
                        agent_path,
                        trace_path,
                        agent_submission=agent_submission,
                    )
                    rec["status"] = "executed"
                    rec["termination"] = trace.get("termination")
                    if run_delay > 0:
                        time.sleep(run_delay)
                except Exception as e:
                    rec["status"] = "error"
                    rec["error"] = str(e)
                exec_records.append(rec)
    return exec_records


def score_campaign(
    campaign: dict,
    manifest: dict,
    *,
    models: list[str] | None = None,
    tasks: list[str] | None = None,
) -> dict:
    pub = published_tasks(manifest)
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    run_records: list[dict] = []

    model_list = models or campaign["models"]
    task_list = tasks or campaign["tasks"]

    for model_id in model_list:
        for task_id in task_list:
            if task_id not in pub:
                continue
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
                trace_path = agent_path.with_name(f"{task_id}_run{run:02d}_trace.json")
                submission_path = agent_path.with_name(f"{task_id}_run{run:02d}_submission.json")
                composite_report = score_run(
                    task_id,
                    agent_path,
                    trace_path=trace_path if trace_path.exists() else None,
                    submission_path=submission_path if submission_path.exists() else None,
                    manifest=manifest,
                )
                l1_report = composite_report["l1"]["report"]
                rec["composite"] = composite_report
                rec["composite_score"] = composite_report["composite_score"]
                rec["l2_pass"] = composite_report["l2"].get("l2_pass")
                rec["l2_score"] = composite_report["l2"].get("l2_score")
                rec["l3_pass"] = composite_report["l3"].get("l3_pass")
                rec["l3_score"] = composite_report["l3"].get("l3_score")
                rec["verify"] = l1_report
                rec["l1_all_pass"] = composite_report["l1"].get("all_pass")
                rec["l1_pass"] = composite_report["l1"].get("l1_pass")
                rec["failure_modes"] = composite_report.get("failure_modes", [])
                rec["fracture_codes"] = composite_report.get("fracture_codes", [])
                rec["status"] = "scored"
                run_records.append(rec)

    scored = [r for r in run_records if r.get("status") == "scored"]
    summary = _campaign_summary(scored, campaign, task_list)
    summary["run_slots"] = len(run_records)
    summary["scored"] = len(scored)
    summary["missing"] = sum(1 for r in run_records if r.get("status") == "missing")

    return {
        "campaign_id": campaign["campaign_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": campaign.get("status"),
        "models": model_list,
        "tasks": task_list,
        "runs_per_task": campaign["runs_per_task"],
        "execution": campaign.get("_execution"),
        "summary": summary,
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
        choices=("scripted", "mock", "openai", "anthropic", "gemini", "auto"),
        default="auto",
        help="Agent mode when --execute (default: auto — route by model id)",
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

    campaign_path = resolve_bench_path(args.campaign)
    if not campaign_path.exists():
        print(f"ERROR: campaign config not found: {campaign_path}", file=sys.stderr)
        return 1
    campaign = load_json(campaign_path)
    manifest = load_json(BENCH / "manifest.json")

    model_filter = [m.strip() for m in args.models.split(",")] if args.models else None
    task_filter = [t.strip() for t in args.tasks.split(",")] if args.tasks else None

    if args.bootstrap_fixtures:
        paths = bootstrap_fixtures(campaign)
        print(f"Wrote {len(paths)} fixture agent outputs under {campaign['runs_dir']}")

    if args.execute:
        models_to_run = model_filter or campaign["models"]
        needs_openai = args.agent in ("openai",) or (
            args.agent == "auto" and any(is_openai_model(m) for m in models_to_run)
        )
        needs_anthropic = args.agent in ("anthropic",) or (
            args.agent == "auto" and any(is_anthropic_model(m) for m in models_to_run)
        )
        needs_gemini = args.agent in ("gemini",) or (
            args.agent == "auto" and any(is_gemini_model(m) for m in models_to_run)
        )
        if needs_openai and not os.environ.get("OPENAI_API_KEY"):
            print("ERROR: OPENAI_API_KEY not set for OpenAI model slots", file=sys.stderr)
            return 1
        if needs_anthropic and not os.environ.get("ANTHROPIC_API_KEY"):
            print("ERROR: ANTHROPIC_API_KEY not set for Anthropic model slots", file=sys.stderr)
            return 1
        if needs_gemini and not (
            os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        ):
            print(
                "ERROR: GEMINI_API_KEY (or GOOGLE_API_KEY) not set for Gemini model slots",
                file=sys.stderr,
            )
            return 1
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
        skipped = sum(1 for r in exec_records if r.get("status") == "skipped_existing")
        print(f"Execute: {executed} runs, {skipped} skipped, {len(errors)} errors")
        for err in errors[:10]:
            print(f"  ERROR {err['task_id']} run {err['run_index']}: {err.get('error')}", file=sys.stderr)

    result = score_campaign(
        campaign,
        manifest,
        models=model_filter,
        tasks=task_filter,
    )
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
