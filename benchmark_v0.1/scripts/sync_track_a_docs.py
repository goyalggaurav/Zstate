#!/usr/bin/env python3
"""Regenerate manifest-driven doc blocks in Track A READMEs (P3-28)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
ROOT = BENCH.parent

MARKER_START = "<!-- MANIFEST:SYNC:START {name} -->"
MARKER_END = "<!-- MANIFEST:SYNC:END {name} -->"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def replace_block(text: str, name: str, body: str) -> str:
    start = MARKER_START.format(name=name)
    end = MARKER_END.format(name=name)
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    replacement = f"{start}\n{body.rstrip()}\n{end}"
    if not pattern.search(text):
        raise ValueError(f"Missing sync markers for {name!r}")
    return pattern.sub(replacement, text, count=1)


def task_type_label(task_type: str) -> str:
    return {
        "F": "F — Forensics",
        "M": "M — Modeling",
    }.get(task_type, task_type)


def published_tasks_table(manifest: dict) -> str:
    rows = [
        "| Task | Type | Period | Status |",
        "|------|------|--------|--------|",
    ]
    for entry in manifest.get("pilot_tasks", []):
        if entry.get("status") != "published":
            continue
        task_id = entry["task_id"]
        task = load_json(BENCH / entry["paths"]["task"])
        period = task.get("required_documents", [{}])[0].get("fiscal_period", "—")
        cfa = entry.get("cfa_review")
        if cfa:
            status = f"**Published** ([expert review](../{cfa}))"
        else:
            status = "**Published**"
        link = f"[{task_id}](./tasks/{task_id}.json)"
        rows.append(f"| {link} | {task_type_label(entry.get('task_type', 'F'))} | **{period}** | {status} |")
    return "\n".join(rows)


def pilot_summary(manifest: dict) -> str:
    published = [e for e in manifest.get("pilot_tasks", []) if e.get("status") == "published"]
    tickers = ", ".join(e["task_id"].split("_", 1)[0] for e in published)
    n = len(published)
    return f"| **A — Eval benchmark** | [benchmark_v0.1/](benchmark_v0.1/) | **{n} published tasks** ({tickers}) — expert-reviewed Jul 2026 |"


def architecture_status(manifest: dict) -> str:
    published = [e for e in manifest.get("pilot_tasks", []) if e.get("status") == "published"]
    tickers = ", ".join(e["task_id"].split("_", 1)[0] for e in published)
    return f"**Status:** Active — {len(published)} published Track A tasks ({tickers}); pilot eval + leaderboard v0 live"


def sync_files(*, dry_run: bool = False) -> list[str]:
    manifest = load_json(BENCH / "manifest.json")
    changed: list[str] = []

    root_readme = ROOT / "README.md"
    root_text = root_readme.read_text(encoding="utf-8")
    new_root = replace_block(root_text, "pilot_summary", pilot_summary(manifest))
    if new_root != root_text:
        changed.append(str(root_readme))
        if not dry_run:
            root_readme.write_text(new_root, encoding="utf-8")

    bench_readme = BENCH / "README.md"
    bench_text = bench_readme.read_text(encoding="utf-8")
    new_bench = replace_block(bench_text, "published_tasks_table", published_tasks_table(manifest))
    if new_bench != bench_text:
        changed.append(str(bench_readme))
        if not dry_run:
            bench_readme.write_text(new_bench, encoding="utf-8")

    arch = ROOT / "docs" / "ARCHITECTURE.md"
    arch_text = arch.read_text(encoding="utf-8")
    new_arch = replace_block(arch_text, "architecture_status", architecture_status(manifest))
    if new_arch != arch_text:
        changed.append(str(arch))
        if not dry_run:
            arch.write_text(new_arch, encoding="utf-8")

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync manifest-driven doc blocks (P3-28)")
    parser.add_argument("--check", action="store_true", help="Exit 1 if docs would change")
    args = parser.parse_args()
    try:
        changed = sync_files(dry_run=args.check)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.check:
        if changed:
            print("Doc sync drift:", *changed, sep="\n  ")
            return 1
        print("Doc sync OK — no drift")
        return 0
    if changed:
        print("Updated:")
        for path in changed:
            print(f"  {path}")
    else:
        print("No doc changes needed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
