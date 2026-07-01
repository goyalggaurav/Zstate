#!/usr/bin/env python3
"""Run multiple frontier model episodes and write campaign summary."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "env_v1" / "runs" / "frontier"
ENV_MANIFEST = ROOT / "env_v1" / "manifest.json"


def episode_version(episode_id: str) -> str:
    manifest = json.loads(ENV_MANIFEST.read_text())
    for ep in manifest.get("episodes", []):
        if ep.get("episode_id") == episode_id:
            return ep.get("version", "unknown")
    return "unknown"


def run_one(model_id: str, episode: str, out_path: Path, *, run_retries: int = 2) -> dict:
    cmd = [
        sys.executable,
        str(ROOT / "env_v1" / "scripts" / "agent_loop.py"),
        "--agent", "openai",
        "--model-id", model_id,
        "--episode", episode,
        "--out", str(out_path),
    ]
    last_err: subprocess.CalledProcessError | None = None
    for attempt in range(run_retries):
        try:
            subprocess.run(cmd, cwd=ROOT, check=True)
            break
        except subprocess.CalledProcessError as e:
            last_err = e
            if attempt < run_retries - 1:
                wait = 5 * (attempt + 1)
                print(
                    f"Run failed (exit {e.returncode}), retry {attempt + 2}/{run_retries} in {wait}s...",
                    file=sys.stderr,
                )
                time.sleep(wait)
            else:
                raise last_err from e
    trace = json.loads(out_path.read_text())
    scores = json.loads(out_path.with_name(out_path.stem + "_scores.json").read_text())
    return {
        "trace_path": str(out_path.relative_to(ROOT)),
        "trajectory_id": trace.get("trajectory_id"),
        "model_id": trace.get("model_id"),
        "termination": trace.get("termination"),
        "composite_reward": scores.get("composite_reward"),
        "components": scores.get("components"),
        "failure_modes": scores.get("failure_modes"),
        "fracture_codes": scores.get("fracture_codes"),
        "adjusted_eps": trace.get("submission", {}).get("adjusted_eps"),
    }


def summarize(runs: list[dict]) -> dict:
    composites = [r["composite_reward"] for r in runs if r.get("composite_reward") is not None]
    fractures: dict[str, int] = {}
    for r in runs:
        for code in r.get("fracture_codes") or []:
            fractures[code] = fractures.get(code, 0) + 1
    return {
        "run_count": len(runs),
        "composite_median": sorted(composites)[len(composites) // 2] if composites else None,
        "composite_min": min(composites) if composites else None,
        "composite_max": max(composites) if composites else None,
        "fracture_counts": fractures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch frontier model runs")
    parser.add_argument("--model-id", default="gpt-4o")
    parser.add_argument("--episode", default="solaris_adj_eps_dispute_v1")
    parser.add_argument("--seeds", type=int, default=3, help="Number of runs")
    parser.add_argument("--start-index", type=int, default=1, help="First run file index")
    parser.add_argument("--out-dir", type=Path, default=RUNS_DIR)
    parser.add_argument("--campaign-id", default="frontier_campaign_v1")
    parser.add_argument(
        "--run-retries",
        type=int,
        default=2,
        help="Retries per episode if agent_loop exits non-zero (default: 2)",
    )
    args = parser.parse_args()

    if not __import__("os").environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    slug = args.model_id.replace("/", "_").replace(".", "_")
    runs: list[dict] = []

    for i in range(args.seeds):
        idx = args.start_index + i
        out_path = args.out_dir / f"frontier_{slug}_{idx:03d}.json"
        print(f"\n=== Run {idx}/{args.start_index + args.seeds - 1} → {out_path.name} ===")
        runs.append(run_one(args.model_id, args.episode, out_path, run_retries=args.run_retries))

    campaign = {
        "campaign_id": args.campaign_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "episode_id": args.episode,
        "episode_version": episode_version(args.episode),
        "model_id": args.model_id,
        "summary": summarize(runs),
        "runs": runs,
    }
    campaign_path = args.out_dir / f"{args.campaign_id}.json"
    campaign_path.write_text(json.dumps(campaign, indent=2), encoding="utf-8")
    print(f"\nWrote campaign summary: {campaign_path}")
    print(json.dumps(campaign["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
