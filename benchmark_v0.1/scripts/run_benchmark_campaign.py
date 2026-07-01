#!/usr/bin/env python3
"""
Score benchmark eval campaign runs via task verify scripts (P2-04).

Expects agent structured-output JSON files:
  runs/{campaign_id}/{model_slug}/{task_id}_run{01..N}.json

Usage:
  python run_benchmark_campaign.py --bootstrap-fixtures   # gold outputs for smoke test
  python run_benchmark_campaign.py --campaign ../campaigns/pilot_eval_campaign_v1.json
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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model_slug(model_id: str) -> str:
    return model_id.replace("/", "_").replace(".", "_")


def published_tasks(manifest: dict) -> dict[str, dict]:
    return {
        t["task_id"]: t
        for t in manifest.get("pilot_tasks", [])
        if t.get("status") == "published"
    }


def googl_gold_values() -> dict:
    return {
        "google_services_revenue": 89_637,
        "google_cloud_revenue": 20_028,
        "other_bets_revenue": 411,
        "hedging_gains_losses": -180,
        "consolidated_total_revenue": 109_896,
    }


def pep_gold_values(gt: dict) -> dict:
    values: dict = {}
    for section in ("extracted_values", "computed_values"):
        for item in gt.get(section, []):
            if isinstance(item.get("value"), bool):
                continue
            values[item["metric_id"]] = item["value"]
    return values


def bootstrap_fixtures(campaign: dict) -> list[Path]:
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    pep_gt = load_json(BENCH / "ground_truth" / "PEP_fx_organic_growth_gt.json")
    written: list[Path] = []

    for model_id in campaign["models"]:
        mdir = runs_dir / model_slug(model_id)
        mdir.mkdir(parents=True, exist_ok=True)
        for task_id in campaign["tasks"]:
            if task_id == "GOOGL_footnote_reconciliation":
                payload = googl_gold_values()
            elif task_id == "PEP_fx_organic_growth":
                payload = pep_gold_values(pep_gt)
            else:
                continue
            for run in range(1, campaign["runs_per_task"] + 1):
                path = mdir / f"{task_id}_run{run:02d}.json"
                path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                written.append(path)
    return written


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
                rec = {
                    "model_id": model_id,
                    "task_id": task_id,
                    "run_index": run,
                    "agent_output": str(agent_path.relative_to(BENCH.parent)),
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
    args = parser.parse_args()

    campaign_path = args.campaign if args.campaign.is_absolute() else BENCH / args.campaign
    campaign = load_json(campaign_path)
    manifest = load_json(BENCH / "manifest.json")

    if args.bootstrap_fixtures:
        paths = bootstrap_fixtures(campaign)
        print(f"Wrote {len(paths)} fixture agent outputs under {campaign['runs_dir']}")

    result = score_campaign(campaign, manifest)
    out_dir = (BENCH / campaign["runs_dir"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{campaign['campaign_id']}.json"
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"\nWrote {out_path.relative_to(BENCH.parent)}")
    return 0 if result["summary"]["missing"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
