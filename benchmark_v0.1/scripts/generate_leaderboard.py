#!/usr/bin/env python3
"""
Generate actionable leaderboard v0 from a scored benchmark campaign (P2-06).

Ranks by headline weighted composite; adds Fracture Intensity (FI), gap task,
layer-attributed fracture profiles, and fracture delta vs leader.

Usage:
  python generate_leaderboard.py \\
    --campaign ../campaigns/pilot_eval_4task_v1.json \\
    --report ../runs/pilot_eval_4task_v1/pilot_eval_4task_v1.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

BENCH = Path(__file__).resolve().parent.parent
REPO = BENCH.parent
TAXONOMY_PATH = REPO / "schemas" / "fracture_taxonomy_v1.json"
DOCS = BENCH / "docs"

SEVERITY_WEIGHT = {
    "critical": 1.0,
    "high": 0.6,
    "medium": 0.3,
    "low": 0.1,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def git_head() -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip() or None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def severity_map() -> dict[str, str]:
    taxonomy = load_json(TAXONOMY_PATH)
    return {entry["code"]: entry.get("severity", "medium") for entry in taxonomy["codes"]}


def code_label(code: str, labels: dict[str, str]) -> str:
    return labels.get(code, code)


def fracture_intensity(codes: list[str], severities: dict[str, str]) -> float:
    total = 0.0
    for code in codes:
        sev = severities.get(code, "medium")
        total += SEVERITY_WEIGHT.get(sev, 0.3)
    return round(total, 4)


def layer_fractures(composite: dict) -> dict[str, list[str]]:
    return {
        "L1": list(composite.get("l1", {}).get("fracture_codes") or []),
        "L2": list(composite.get("l2", {}).get("fracture_codes") or []),
        "L3": list(composite.get("l3", {}).get("fracture_codes") or []),
    }


def all_run_codes(composite: dict) -> list[str]:
    layers = layer_fractures(composite)
    merged: list[str] = []
    for layer in ("L1", "L2", "L3"):
        for code in layers[layer]:
            if code not in merged:
                merged.append(code)
    return merged


def task_median_scores(runs: list[dict], model_id: str, task_id: str) -> float | None:
    scores = [
        r["composite_score"]
        for r in runs
        if r.get("model_id") == model_id
        and r.get("task_id") == task_id
        and r.get("composite_score") is not None
    ]
    return round(median(scores), 4) if scores else None


def headline_weighted_composite(
    task_medians: dict[str, float | None],
    headline_tasks: list[str],
    weights: dict[str, float],
) -> float | None:
    pairs = [
        (task_medians[tid], weights.get(tid, 1.0))
        for tid in headline_tasks
        if task_medians.get(tid) is not None
    ]
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    if total_w <= 0:
        return None
    return round(sum(v * w for v, w in pairs) / total_w, 4)


def aggregate_layer_profile(headline_runs: list[dict]) -> dict[str, dict[str, int]]:
    profile: dict[str, Counter] = {"L1": Counter(), "L2": Counter(), "L3": Counter()}
    for rec in headline_runs:
        layers = layer_fractures(rec["composite"])
        for layer, codes in layers.items():
            for code in codes:
                profile[layer][code] += 1
    return {layer: dict(profile[layer]) for layer in profile}


def gap_task(
    model_id: str,
    leader_id: str,
    headline_tasks: list[str],
    task_medians_by_model: dict[str, dict[str, float | None]],
) -> dict | None:
    if model_id == leader_id:
        return None
    leader_tasks = task_medians_by_model.get(leader_id, {})
    model_tasks = task_medians_by_model.get(model_id, {})
    best_tid = None
    best_delta = 0.0
    for tid in headline_tasks:
        leader_score = leader_tasks.get(tid)
        model_score = model_tasks.get(tid)
        if leader_score is None or model_score is None:
            continue
        delta = leader_score - model_score
        if delta > best_delta:
            best_delta = delta
            best_tid = tid
    if best_tid is None:
        return None
    return {
        "task_id": best_tid,
        "leader_composite": leader_tasks[best_tid],
        "model_composite": model_tasks[best_tid],
        "delta": round(best_delta, 4),
    }


def fracture_delta_by_task(
    model_id: str,
    leader_id: str,
    headline_tasks: list[str],
    runs: list[dict],
) -> dict[str, list[str]]:
    delta: dict[str, list[str]] = {}
    for tid in headline_tasks:
        leader_codes: set[str] = set()
        model_codes: set[str] = set()
        for rec in runs:
            if rec.get("task_id") != tid:
                continue
            codes = all_run_codes(rec["composite"])
            if rec.get("model_id") == leader_id:
                leader_codes.update(codes)
            elif rec.get("model_id") == model_id:
                model_codes.update(codes)
        only_model = sorted(model_codes - leader_codes)
        if only_model:
            delta[tid] = only_model
    return delta


def build_leaderboard(campaign: dict, report: dict) -> dict:
    severities = severity_map()
    labels = {
        entry["code"]: entry.get("label", entry["code"])
        for entry in load_json(TAXONOMY_PATH)["codes"]
    }

    headline_tasks = campaign.get("headline_tasks") or campaign["tasks"]
    task_weights = campaign.get("task_weights") or {tid: 1.0 for tid in headline_tasks}
    models = report.get("models") or campaign["models"]
    runs = [r for r in report.get("runs", []) if r.get("status") == "scored" and r.get("composite")]

    task_medians_by_model: dict[str, dict[str, float | None]] = {}
    for model_id in models:
        task_medians_by_model[model_id] = {
            tid: task_median_scores(runs, model_id, tid) for tid in headline_tasks
        }

    model_rows: list[dict] = []
    for model_id in models:
        headline_runs = [
            r
            for r in runs
            if r.get("model_id") == model_id and r.get("task_id") in headline_tasks
        ]
        run_fi = [fracture_intensity(all_run_codes(r["composite"]), severities) for r in headline_runs]
        fi_value = round(median(run_fi), 4) if run_fi else 0.0
        task_medians = task_medians_by_model[model_id]
        headline_score = headline_weighted_composite(task_medians, headline_tasks, task_weights)
        summary_weighted = (report.get("summary") or {}).get("weighted_composite_by_model", {}).get(model_id)
        if headline_score is None and summary_weighted is not None:
            headline_score = round(float(summary_weighted), 4)

        model_rows.append({
            "model_id": model_id,
            "headline_composite": headline_score,
            "fracture_intensity": fi_value,
            "task_composites": task_medians,
            "headline_run_count": len(headline_runs),
            "fracture_profile": aggregate_layer_profile(headline_runs),
            "fracture_codes_union": sorted({
                code
                for rec in headline_runs
                for code in all_run_codes(rec["composite"])
            }),
        })

    model_rows.sort(
        key=lambda row: (row["headline_composite"] is not None, row["headline_composite"] or 0.0),
        reverse=True,
    )
    leader = model_rows[0]["model_id"] if model_rows else None
    for rank, row in enumerate(model_rows, start=1):
        row["rank"] = rank
        row["is_leader"] = row["model_id"] == leader
        if leader and not row["is_leader"]:
            row["gap_task"] = gap_task(
                row["model_id"], leader, headline_tasks, task_medians_by_model
            )
            row["fracture_delta_vs_leader"] = fracture_delta_by_task(
                row["model_id"], leader, headline_tasks, runs
            )
        else:
            row["gap_task"] = None
            row["fracture_delta_vs_leader"] = {}

    return {
        "schema_version": "leaderboard_v0",
        "campaign_id": report.get("campaign_id") or campaign["campaign_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_report": report.get("created_at"),
        "git_commit": git_head(),
        "methodology": {
            "primary_rank": "headline_weighted_composite",
            "headline_tasks": headline_tasks,
            "excluded_from_headline": [
                tid for tid in campaign["tasks"] if tid not in headline_tasks
            ],
            "runs_per_task": campaign.get("runs_per_task"),
            "task_aggregation": "median",
            "headline_aggregation": "task_weighted_mean_of_task_medians",
            "fracture_intensity": {
                "scope": "headline runs only",
                "formula": "median per-run sum of severity weights",
                "severity_weights": SEVERITY_WEIGHT,
                "diagnostic_only": True,
            },
        },
        "fracture_labels": labels,
        "leader_model_id": leader,
        "rankings": model_rows,
    }


def _fmt_profile(profile: dict[str, dict[str, int]]) -> str:
    lines: list[str] = []
    for layer in ("L1", "L2", "L3"):
        codes = profile.get(layer) or {}
        if not codes:
            continue
        parts = [f"`{code}`×{count}" for code, count in sorted(codes.items(), key=lambda x: -x[1])]
        lines.append(f"- **{layer}:** {', '.join(parts)}")
    return "\n".join(lines) if lines else "- *(none on headline runs)*"


def render_markdown(doc: dict) -> str:
    meth = doc["methodology"]
    lines = [
        "# Track A Leaderboard v0 — Actionable Fracture View",
        "",
        f"**Campaign:** `{doc['campaign_id']}`  ",
        f"**Generated:** {doc['generated_at']}  ",
    ]
    if doc.get("git_commit"):
        lines.append(f"**Git:** `{doc['git_commit']}`  ")
    if doc.get("source_report"):
        lines.append(f"**Source report:** {doc['source_report']}  ")
    lines.extend([
        "",
        "> **Primary rank:** headline weighted composite (PEP + AMZN + NFLX).  ",
        "> **Fracture Intensity (FI):** diagnostic only — severity-weighted fracture load on headline runs (lower is cleaner).",
        "",
        "---",
        "",
        "## Rankings",
        "",
        "| Rank | Model | Headline | FI ↓ | Gap task | Top fractures (headline) |",
        "|------|-------|----------|------|----------|---------------------------|",
    ])

    for row in doc["rankings"]:
        gap = row.get("gap_task")
        gap_cell = "—" if not gap else f"`{gap['task_id']}` (−{gap['delta']:.3f})"
        codes = row.get("fracture_codes_union") or []
        top = ", ".join(f"`{c}`" for c in codes[:4]) if codes else "—"
        if len(codes) > 4:
            top += f" +{len(codes) - 4}"
        lines.append(
            f"| {row['rank']} | `{row['model_id']}` | **{row['headline_composite']:.3f}** "
            f"| {row['fracture_intensity']:.3f} | {gap_cell} | {top} |"
        )

    lines.extend(["", "---", "", "## Per-model fracture profiles", ""])
    for row in doc["rankings"]:
        lines.append(f"### #{row['rank']} `{row['model_id']}`")
        lines.append("")
        lines.append(f"- **Headline composite:** {row['headline_composite']}")
        lines.append(f"- **Fracture Intensity:** {row['fracture_intensity']} *(diagnostic)*")
        if row.get("gap_task"):
            g = row["gap_task"]
            lines.append(
                f"- **Gap task vs leader:** `{g['task_id']}` "
                f"({g['model_composite']} vs leader {g['leader_composite']}, Δ {g['delta']})"
            )
        lines.append("")
        lines.append("**Layer profile (headline runs):**")
        lines.append(_fmt_profile(row.get("fracture_profile") or {}))
        delta = row.get("fracture_delta_vs_leader") or {}
        if delta:
            lines.append("")
            lines.append("**Fracture delta vs leader (by task):**")
            for tid, codes in delta.items():
                lines.append(f"- `{tid}`: {', '.join(f'`{c}`' for c in codes)}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## Methodology",
        "",
        f"- **Headline tasks:** {', '.join(f'`{t}`' for t in meth['headline_tasks'])}",
        f"- **Excluded from headline:** {', '.join(f'`{t}`' for t in meth['excluded_from_headline']) or '—'}",
        f"- **Runs per task:** {meth['runs_per_task']}; task score = median composite",
        "- **FI weights:** critical 1.0 · high 0.6 · medium 0.3 · low 0.1",
        "- **Expert sign-off:** all headline tasks published with CFA review docs",
        "",
        "See also: [PILOT_EVAL_JUL2026.md](./PILOT_EVAL_JUL2026.md)",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate actionable leaderboard v0 (P2-06)")
    parser.add_argument(
        "--campaign",
        type=Path,
        default=BENCH / "campaigns" / "pilot_eval_4task_v1.json",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Scored campaign JSON (default: runs/{campaign_id}/{campaign_id}.json)",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=DOCS / "LEADERBOARD_v0.json",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=DOCS / "LEADERBOARD_v0.md",
    )
    args = parser.parse_args()

    campaign_path = args.campaign if args.campaign.is_absolute() else BENCH / args.campaign
    campaign = load_json(campaign_path)
    report_path = args.report
    if report_path is None:
        report_path = BENCH / campaign["runs_dir"] / f"{campaign['campaign_id']}.json"
    elif not report_path.is_absolute():
        report_path = BENCH / report_path
    if not report_path.exists():
        print(f"ERROR: report not found: {report_path}", file=sys.stderr)
        return 1

    report = load_json(report_path)
    doc = build_leaderboard(campaign, report)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(doc), encoding="utf-8")

    print(json.dumps({
        "campaign_id": doc["campaign_id"],
        "leader": doc["leader_model_id"],
        "rankings": [
            {
                "rank": r["rank"],
                "model_id": r["model_id"],
                "headline_composite": r["headline_composite"],
                "fracture_intensity": r["fracture_intensity"],
            }
            for r in doc["rankings"]
        ],
    }, indent=2))
    print(f"\nWrote {args.out_json.relative_to(REPO)}")
    print(f"Wrote {args.out_md.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
