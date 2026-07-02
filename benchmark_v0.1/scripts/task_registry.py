"""Manifest-driven task wiring SSOT for Track A (P3-11)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
MANIFEST_PATH = BENCH / "manifest.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    return load_json(MANIFEST_PATH)


def pilot_tasks(*, published_only: bool = False) -> list[dict]:
    tasks = load_manifest().get("pilot_tasks", [])
    if published_only:
        return [t for t in tasks if t.get("status") == "published"]
    return list(tasks)


def published_task_ids() -> list[str]:
    return [t["task_id"] for t in pilot_tasks(published_only=True)]


def all_task_ids() -> list[str]:
    return [t["task_id"] for t in pilot_tasks()]


def manifest_entry(task_id: str) -> dict:
    for entry in pilot_tasks():
        if entry["task_id"] == task_id:
            return entry
    raise ValueError(f"No manifest entry for task {task_id!r}")


def bench_path(task_id: str, path_key: str) -> Path:
    rel = manifest_entry(task_id)["paths"][path_key]
    return BENCH / rel


def corpus_bundle_rel(task_id: str) -> str:
    return manifest_entry(task_id)["paths"]["corpus_bundle"]


def corpus_bundle_path(task_id: str) -> Path:
    return BENCH / corpus_bundle_rel(task_id)


def corpus_bundle_filename(task_id: str) -> str:
    return corpus_bundle_path(task_id).name


def scripted_plan_path(task_id: str) -> Path | None:
    rel = manifest_entry(task_id)["paths"].get("scripted_plan")
    if not rel:
        return None
    path = BENCH / rel
    return path if path.exists() else None


def load_bundle(task_id: str) -> dict:
    path = corpus_bundle_path(task_id)
    if not path.exists():
        raise FileNotFoundError(f"Corpus bundle not found: {path}")
    return load_json(path)


def load_task(task_id: str) -> dict:
    return load_json(bench_path(task_id, "task"))


def load_ground_truth(task_id: str) -> dict:
    return load_json(bench_path(task_id, "ground_truth"))


def load_gold_path(task_id: str) -> dict:
    return load_json(bench_path(task_id, "gold_path"))


def headline_eligible(task_id: str) -> bool:
    return bool(manifest_entry(task_id).get("headline_eligible", True))


def headline_task_ids(task_ids: list[str] | None = None) -> list[str]:
    ids = task_ids if task_ids is not None else published_task_ids()
    return [tid for tid in ids if headline_eligible(tid)]


def resolve_campaign_headline_tasks(campaign: dict, task_list: list[str] | None = None) -> list[str]:
    """Headline tasks: explicit campaign override, else manifest headline_eligible filter."""
    if campaign.get("headline_tasks"):
        return list(campaign["headline_tasks"])
    tasks = task_list if task_list is not None else campaign.get("tasks") or published_task_ids()
    return headline_task_ids(list(tasks))


def default_campaign_path() -> Path:
    rel = load_manifest().get("default_campaign", "campaigns/pilot_eval_5task_v1.json")
    return BENCH / rel


def pinned_campaign_report_path() -> Path | None:
    rel = load_manifest().get("pinned_campaign_report")
    if not rel:
        return None
    return BENCH / rel
