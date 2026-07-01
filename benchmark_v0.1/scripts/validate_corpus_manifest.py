#!/usr/bin/env python3
"""Validate corpus manifest resolves task required_documents."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark_v0.1"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate() -> dict:
    manifest = load_json(BENCH / "corpus" / "corpus_manifest_v1.json")
    bench = load_json(BENCH / "manifest.json")
    doc_ids = {d["doc_id"] for d in manifest["documents"]}
    errors: list[str] = []

    for ticker in manifest["pilot_tickers"]:
        if ticker not in manifest["ticker_registry"]:
            errors.append(f"missing ticker_registry entry: {ticker}")

    for task in bench.get("pilot_tasks", []):
        task_path = BENCH / task["paths"]["task"]
        if not task_path.exists():
            continue
        task_json = load_json(task_path)
        for doc in task_json.get("required_documents", []):
            doc_id = doc["doc_id"]
            if doc_id not in doc_ids:
                errors.append(f"{task['task_id']}: required doc {doc_id} not in corpus manifest")

    return {
        "manifest_version": manifest["manifest_version"],
        "pilot_tickers": len(manifest["pilot_tickers"]),
        "documents": len(manifest["documents"]),
        "errors": errors,
        "all_pass": not errors,
    }


def main() -> int:
    report = validate()
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
