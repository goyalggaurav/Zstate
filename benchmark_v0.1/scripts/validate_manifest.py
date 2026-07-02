#!/usr/bin/env python3
"""Validate benchmark manifest paths for published pilot tasks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark_v0.1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate() -> dict:
    manifest = load_json(BENCH / "manifest.json")
    checks: list[dict] = []

    for task in manifest.get("pilot_tasks", []):
        if task.get("status") != "published":
            continue
        task_id = task["task_id"]
        path_keys = ("task", "ground_truth", "gold_path", "grader_rubric", "corpus_bundle", "verify_script")
        for key in path_keys:
            rel_path = task.get("paths", {}).get(key)
            if not rel_path:
                checks.append(
                    {
                        "task_id": task_id,
                        "path_key": key,
                        "path": None,
                        "pass": False,
                    }
                )
                continue
            full_path = BENCH / rel_path
            ok = full_path.exists()
            checks.append(
                {
                    "task_id": task_id,
                    "path_key": key,
                    "path": rel_path,
                    "pass": ok,
                }
            )
        scripted = task.get("paths", {}).get("scripted_plan")
        if scripted:
            full_path = BENCH / scripted
            checks.append(
                {
                    "task_id": task_id,
                    "path_key": "scripted_plan",
                    "path": scripted,
                    "pass": full_path.exists(),
                }
            )

    return {
        "benchmark_version": manifest.get("benchmark_version"),
        "published_tasks": sum(
            1 for t in manifest.get("pilot_tasks", []) if t.get("status") == "published"
        ),
        "checks": checks,
        "all_pass": all(c["pass"] for c in checks),
    }


def main() -> int:
    report = validate()
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
