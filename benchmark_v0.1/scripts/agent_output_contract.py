#!/usr/bin/env python3
"""Agent structured-output contract — paths, gold payloads, and trap fixtures (SH-07 stub)."""

from __future__ import annotations

import json
import re
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
PEP_GT_PATH = BENCH / "ground_truth" / "PEP_fx_organic_growth_gt.json"

SLOT_RE = re.compile(r"^(.+)_run(\d+)\.json$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model_slug(model_id: str) -> str:
    return model_id.replace("/", "_").replace(".", "_")


def slug_to_model_id(slug: str, campaign: dict) -> str:
    for model_id in campaign["models"]:
        if model_slug(model_id) == slug:
            return model_id
    raise ValueError(f"Unknown model slug {slug!r}; expected one of {[model_slug(m) for m in campaign['models']]}")


def parse_slot(slot: str, campaign: dict) -> tuple[str, str, int]:
    """Parse `{model_slug}/{task_id}_run{NN}.json`."""
    if "/" not in slot:
        raise ValueError(f"Slot must be model_slug/task_id_runNN.json, got {slot!r}")
    slug, filename = slot.split("/", 1)
    match = SLOT_RE.match(filename)
    if not match:
        raise ValueError(f"Bad filename {filename!r}; expected {{task_id}}_run{{NN}}.json")
    task_id = match.group(1)
    run_index = int(match.group(2))
    model_id = slug_to_model_id(slug, campaign)
    if task_id not in campaign["tasks"]:
        raise ValueError(f"Task {task_id!r} not in campaign tasks")
    return model_id, task_id, run_index


def agent_output_path(campaign: dict, model_id: str, task_id: str, run_index: int) -> Path:
    runs_dir = (BENCH / campaign["runs_dir"]).resolve()
    return runs_dir / model_slug(model_id) / f"{task_id}_run{run_index:02d}.json"


def googl_gold_values() -> dict:
    return {
        "google_services_revenue": 89_637,
        "google_cloud_revenue": 20_028,
        "other_bets_revenue": 411,
        "hedging_gains_losses": -180,
        "consolidated_total_revenue": 109_896,
    }


def pep_gold_values(gt: dict | None = None) -> dict:
    doc = gt if gt is not None else load_json(PEP_GT_PATH)
    values: dict = {}
    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            if isinstance(item.get("value"), bool):
                continue
            values[item["metric_id"]] = item["value"]
    return values


def payload_for_mode(mode: str, task_id: str, gt: dict | None = None) -> dict | None:
    if mode == "gold":
        if task_id == "GOOGL_footnote_reconciliation":
            return googl_gold_values()
        if task_id == "PEP_fx_organic_growth":
            return pep_gold_values(gt)
        raise ValueError(f"No gold payload for task {task_id!r}")

    if mode == "trap_googl_sign":
        if task_id != "GOOGL_footnote_reconciliation":
            raise ValueError("trap_googl_sign applies to GOOGL_footnote_reconciliation only")
        values = googl_gold_values()
        values["hedging_gains_losses"] = 180
        return values

    if mode == "trap_googl_blind_sum":
        if task_id != "GOOGL_footnote_reconciliation":
            raise ValueError("trap_googl_blind_sum applies to GOOGL_footnote_reconciliation only")
        values = googl_gold_values()
        values["consolidated_total_revenue"] = 110_076
        values["hedging_gains_losses"] = None
        return values

    if mode == "trap_pep_reported_only":
        if task_id != "PEP_fx_organic_growth":
            raise ValueError("trap_pep_reported_only applies to PEP_fx_organic_growth only")
        pep_gt = gt if gt is not None else load_json(PEP_GT_PATH)
        values = pep_gold_values(pep_gt)
        trap = next(
            fm["wrong_signatures"]
            for fm in pep_gt["failure_modes"]
            if fm["id"] == "reported_only"
        )
        values.update(trap)
        return values

    if mode == "trap_pep_wrong_region":
        if task_id != "PEP_fx_organic_growth":
            raise ValueError("trap_pep_wrong_region applies to PEP_fx_organic_growth only")
        values = pep_gold_values(gt)
        values["emea_net_revenue_fy2025"] = 25_000
        return values

    if mode in ("malformed", "missing"):
        return None

    raise ValueError(f"Unknown mode {mode!r}")


CONTRACT_MODES: dict[str, dict] = {
    "gold": {"tasks": ["GOOGL_footnote_reconciliation", "PEP_fx_organic_growth"], "expect_fractures": []},
    "trap_googl_sign": {
        "tasks": ["GOOGL_footnote_reconciliation"],
        "expect_fractures": ["SIGN_ERR"],
        "expect_failure_modes": ["sign_error"],
    },
    "trap_googl_blind_sum": {
        "tasks": ["GOOGL_footnote_reconciliation"],
        "expect_fractures": ["RECON_OMIT"],
        "expect_failure_modes": ["blind_sum"],
    },
    "trap_pep_reported_only": {
        "tasks": ["PEP_fx_organic_growth"],
        "expect_fractures": ["CC_OMIT"],
        "expect_failure_modes": ["reported_only"],
    },
    "trap_pep_wrong_region": {
        "tasks": ["PEP_fx_organic_growth"],
        "expect_fractures": ["SCOPE_ERR"],
        "expect_failure_modes": ["wrong_region"],
    },
}


def write_agent_output(path: Path, mode: str, task_id: str, gt: dict | None = None) -> None:
    if mode == "missing":
        path.unlink(missing_ok=True)
        return
    if mode == "malformed":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not valid json\n", encoding="utf-8")
        return
    payload = payload_for_mode(mode, task_id, gt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def bootstrap_fixtures(campaign: dict) -> list[Path]:
    pep_gt = load_json(PEP_GT_PATH)
    written: list[Path] = []
    for model_id in campaign["models"]:
        for task_id in campaign["tasks"]:
            for run in range(1, campaign["runs_per_task"] + 1):
                path = agent_output_path(campaign, model_id, task_id, run)
                write_agent_output(path, "gold", task_id, pep_gt)
                written.append(path)
    return written
