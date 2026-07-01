"""Universal archetype + path_role helpers for Track A benchmark (P2-13+)."""

from __future__ import annotations

import json
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BENCH / "schemas" / "archetype_roles_v1.json"


def load_archetype_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def archetype_def(archetype_id: str) -> dict:
    schema = load_archetype_schema()
    if archetype_id not in schema.get("archetypes", {}):
        raise ValueError(f"Unknown archetype {archetype_id!r}")
    return schema["archetypes"][archetype_id]


def allowed_path_roles(archetype_id: str) -> set[str]:
    spec = archetype_def(archetype_id)
    roles = set(spec.get("default_path_order", []))
    roles.update(spec.get("optional_roles", []))
    roles.add("segment_financials_prior_year")
    return roles


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def task_json_path(task_id: str) -> Path:
    return BENCH / "tasks" / f"{task_id}.json"


def ground_truth_path(task_id: str) -> Path:
    manifest = load_json(BENCH / "manifest.json")
    for entry in manifest.get("pilot_tasks", []):
        if entry["task_id"] == task_id:
            return BENCH / entry["paths"]["ground_truth"]
    raise ValueError(f"No ground truth for task {task_id!r}")


def gold_path_path(task_id: str) -> Path:
    manifest = load_json(BENCH / "manifest.json")
    for entry in manifest.get("pilot_tasks", []):
        if entry["task_id"] == task_id:
            return BENCH / entry["paths"]["gold_path"]
    raise ValueError(f"No gold path for task {task_id!r}")


def task_archetype(task_id: str) -> str:
    task = load_json(task_json_path(task_id))
    if task.get("archetype"):
        return task["archetype"]
    gold = load_json(gold_path_path(task_id))
    if gold.get("archetype"):
        return gold["archetype"]
    raise ValueError(f"No archetype on task or gold path for {task_id!r}")


def gt_metric_values(task_id: str) -> dict:
    from agent_output_contract import amzn_gold_values, googl_gold_values, pep_gold_values

    archetype = task_archetype(task_id)
    if archetype == "F_adjustment":
        return googl_gold_values()
    if archetype == "F_exact":
        return amzn_gold_values()
    if archetype == "M_organic":
        return pep_gold_values(load_json(ground_truth_path(task_id)))
    raise ValueError(f"No metric loader for archetype {archetype!r}")


def legacy_slug_map(bundle: dict) -> dict[str, str]:
    """Map legacy trace/citation slugs to canonical path_role section_slug."""
    mapping: dict[str, str] = {}
    for entry in registry_entries(bundle):
        canonical = entry["section_slug"]
        mapping[canonical] = canonical
        for legacy in entry.get("legacy_section_slugs", []):
            mapping[str(legacy).strip().lower()] = canonical
    return mapping


def canonicalize_section_slug(bundle: dict, raw: str) -> str:
    from benchmark_tool_backend import normalize_section_slug

    slug = normalize_section_slug(raw)
    return legacy_slug_map(bundle).get(slug, slug)


def registry_entries(bundle: dict) -> list[dict]:
    return list(bundle.get("section_registry", []))


def required_slugs(bundle: dict) -> list[str]:
    return [e["section_slug"] for e in registry_entries(bundle) if e.get("required", False)]


def decoy_slugs(bundle: dict) -> list[str]:
    return [e["section_slug"] for e in registry_entries(bundle) if e.get("decoy_trap")]


def validate_registry(bundle: dict, archetype_id: str) -> list[tuple[str, str, bool]]:
    results: list[tuple[str, str, bool]] = []
    allowed = allowed_path_roles(archetype_id)
    traps = load_archetype_schema().get("decoy_traps", {})
    for entry in registry_entries(bundle):
        slug = entry.get("section_slug", "")
        role = entry.get("path_role", slug)
        results.append(("path_role_equals_slug", slug, role == slug))
        if entry.get("required", False):
            results.append(("required_role_allowed", slug, role in allowed))
        if entry.get("decoy_trap"):
            results.append(("decoy_not_required", slug, not entry.get("required", False)))
            results.append(("decoy_trap_known", entry["decoy_trap"], entry["decoy_trap"] in traps))
        results.append(("registry_has_filing_label", slug, bool(entry.get("filing_label") or entry.get("name"))))
    return results


def registry_prompt_lines(bundle: dict) -> str:
    lines: list[str] = []
    for entry in registry_entries(bundle):
        slug = entry["section_slug"]
        label = entry.get("filing_label") or entry.get("name", slug)
        suffix = " [decoy]" if entry.get("decoy_trap") else ""
        req = "required" if entry.get("required", False) else "optional"
        lines.append(f"  - {slug} ({req}): {label}{suffix}")
    return "\n".join(lines)


def dev_citation_guidance(bundle: dict, gold_path: dict) -> str:
    order = (gold_path.get("l2_gold_path") or {}).get("expected_section_order") or []
    acks = [
        note["policy_id"]
        for note in bundle.get("policy_notes", [])
        if note.get("agent_ack_required")
    ]
    decoys = decoy_slugs(bundle)
    lines = [
        "CITATION RULES:",
        "- Each citation snippet must be a verbatim substring from Search_Filing/PDF_Parser output.",
        "- Each metric must use a distinct snippet — never reuse the same substring.",
    ]
    if order:
        lines.append(f"- Preferred retrieval order: {' → '.join(order)}.")
    if decoys:
        lines.append(f"- Decoy slugs: {', '.join(decoys)} — do not use for scored-period metrics.")
    if acks:
        lines.append(f"- Include policy_acknowledgements: {json.dumps(acks)}.")
    return "\n".join(lines)
