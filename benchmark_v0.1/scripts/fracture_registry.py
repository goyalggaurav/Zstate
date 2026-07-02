"""Central failure_mode → fracture_code resolution for Track A (P3-08)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
REPO = BENCH.parent
LIBRARY_PATH = REPO / "schemas" / "fracture_library_v1.json"
TAXONOMY_PATH = REPO / "schemas" / "fracture_taxonomy_v1.json"
ARCHETYPE_PATH = BENCH / "schemas" / "archetype_roles_v1.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_library() -> dict:
    return load_json(LIBRARY_PATH)


@lru_cache(maxsize=1)
def taxonomy_codes() -> set[str]:
    doc = load_json(TAXONOMY_PATH)
    return {entry["code"] for entry in doc.get("codes", [])}


@lru_cache(maxsize=1)
def decoy_trap_modes() -> dict[str, str]:
    schema = load_json(ARCHETYPE_PATH)
    mapping: dict[str, str] = {}
    for trap in schema.get("decoy_traps", {}).values():
        mode = trap.get("failure_mode")
        code = trap.get("fracture_code")
        if mode and code:
            mapping[str(mode)] = str(code)
    return mapping


def gold_path_for_task(task_id: str) -> dict:
    from task_registry import load_gold_path

    return load_gold_path(task_id)


def ground_truth_for_task(task_id: str) -> dict:
    from task_registry import load_ground_truth

    return load_ground_truth(task_id)


def l1_map_for_task(task_id: str | None) -> dict[str, str]:
    library = load_library()
    mapping = dict(library.get("l1_global", {}))
    mapping.update(decoy_trap_modes())
    if not task_id:
        return mapping
    gold = gold_path_for_task(task_id)
    for entry in gold.get("failure_mode_map", []):
        mode_id = entry.get("failure_mode_id")
        code = entry.get("fracture_code")
        if mode_id and code:
            mapping[str(mode_id)] = str(code)
    gt = ground_truth_for_task(task_id)
    for entry in gt.get("failure_modes", []):
        mode_id = entry.get("id")
        code = entry.get("fracture_code")
        if mode_id and code:
            mapping[str(mode_id)] = str(code)
    return mapping


def layer_map(layer: str) -> dict[str, str]:
    library = load_library()
    key = layer.upper()
    if key not in ("L1", "L2", "L3"):
        raise ValueError(f"Unknown layer {layer!r}")
    if key == "L1":
        raise ValueError("Use l1_map_for_task() for L1 maps")
    return dict(library.get("layers", {}).get(key, {}))


def fracture_code(
    failure_mode: str,
    *,
    task_id: str | None = None,
    layer: str = "L1",
) -> str | None:
    layer_key = layer.upper()
    if layer_key == "L1":
        return l1_map_for_task(task_id).get(failure_mode)
    return layer_map(layer_key).get(failure_mode)


def fracture_codes(
    failure_modes: list[str],
    *,
    task_id: str | None = None,
    layer: str = "L1",
) -> list[str]:
    codes: list[str] = []
    for mode in failure_modes:
        code = fracture_code(mode, task_id=task_id, layer=layer)
        if code and code not in codes:
            codes.append(code)
    return codes


def all_registered_fracture_codes() -> set[str]:
    """Union of codes reachable from library + pilot gold paths + GT failure_modes."""
    codes: set[str] = set()
    library = load_library()
    for layer_map_val in library.get("layers", {}).values():
        codes.update(layer_map_val.values())
    codes.update(library.get("l1_global", {}).values())
    codes.update(decoy_trap_modes().values())
    manifest = load_json(BENCH / "manifest.json")
    for entry in manifest.get("pilot_tasks", []):
        task_id = entry["task_id"]
        codes.update(l1_map_for_task(task_id).values())
    return codes


def assert_codes_in_taxonomy(codes: list[str]) -> None:
    registry = taxonomy_codes()
    missing = set(codes) - registry
    if missing:
        raise ValueError(f"Fracture codes not in taxonomy: {sorted(missing)}")
