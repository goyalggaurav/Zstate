#!/usr/bin/env python3
"""Agent structured-output contract — paths, gold payloads, and trap fixtures (SH-07 stub)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent
PEP_GT_PATH = BENCH / "ground_truth" / "PEP_fx_organic_growth_gt.json"

# All published tasks use GT-derived gold/trap bases (P3-17b).
def gt_derived_task_ids() -> frozenset[str]:
    from task_registry import published_task_ids

    return frozenset(published_task_ids())


# Back-compat alias
GT_DERIVED_TASKS = gt_derived_task_ids()

SLOT_RE = re.compile(r"^(.+)_run(\d+)\.json$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_bench_path(path: Path) -> Path:
    """Resolve config paths from repo root, benchmark_v0.1/, or cwd."""
    if path.is_absolute():
        return path
    for candidate in (Path.cwd() / path, BENCH / path, BENCH.parent / path):
        if candidate.exists():
            return candidate.resolve()
    if path.parts and path.parts[0] == BENCH.name:
        return (BENCH.parent / path).resolve()
    return (BENCH / path).resolve()


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


def ground_truth_path_for_task(task_id: str) -> Path:
    scripts = BENCH / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    from task_registry import bench_path

    return bench_path(task_id, "ground_truth")


def load_ground_truth_doc(task_id: str, gt_path: Path | None = None) -> dict:
    path = gt_path or ground_truth_path_for_task(task_id)
    return load_json(path)


def _values_from_gt_doc(doc: dict, allowed: set[str]) -> dict:
    values: dict = {}
    for section in ("extracted_values", "computed_values"):
        for item in doc.get(section, []):
            mid = item.get("metric_id")
            if mid in allowed:
                values[mid] = item["value"]
    return values


def l1_values_from_gt(task_id: str, gt_path: Path | None = None) -> dict:
    """Build L1 agent-output dict from GT extracted + computed values (P3-17)."""
    from agents.benchmark_tool_specs import metric_keys

    allowed = metric_keys(task_id)
    doc = load_ground_truth_doc(task_id, gt_path)
    return _values_from_gt_doc(doc, allowed)


def filing_label_for_slug(bundle: dict, section_slug: str) -> str | None:
    for entry in bundle.get("section_registry", []):
        if entry.get("section_slug") == section_slug:
            return entry.get("filing_label")
    return None


def _default_section_slug(cite: dict, metric_id: str) -> str:
    if cite.get("section_slug"):
        return cite["section_slug"]
    if "guidance" in metric_id or "annual" in metric_id:
        return "narrative_guidance"
    if "amortization" in metric_id or "ytd" in metric_id or "cash" in metric_id:
        return "quantitative_actuals"
    if "growth" in metric_id or "fx" in metric_id or "pct" in metric_id:
        return "narrative_fx"
    if "consolidated" in metric_id:
        return "consolidated_primary"
    return "segment_financials"


def _build_citation_entry(
    metric_id: str,
    cite: dict,
    bundle: dict,
) -> dict:
    section_slug = _default_section_slug(cite, metric_id)
    entry: dict = {
        "metric_id": metric_id,
        "doc_id": cite.get("doc_id", ""),
        "section_slug": section_slug,
        "snippet": cite["snippet"],
    }
    label = filing_label_for_slug(bundle, section_slug)
    if label:
        entry["filing_label"] = label
        entry["note"] = cite.get("note") or label
    return entry


def _section_slug_for_doc(bundle: dict, doc_id: str) -> str | None:
    for entry in bundle.get("section_registry", []):
        if entry.get("doc_id") == doc_id:
            return entry.get("section_slug")
    return None


def _computed_citation(
    metric_id: str,
    policy: dict,
    extracted_map: dict[str, dict],
    bundle: dict,
) -> dict | None:
    if policy.get("cite_metric"):
        base = extracted_map.get(policy["cite_metric"])
        if not base:
            return None
        entry = dict(base)
        entry["metric_id"] = metric_id
        if policy.get("snippet"):
            entry["snippet"] = policy["snippet"]
        if policy.get("section_slug"):
            entry["section_slug"] = policy["section_slug"]
            label = filing_label_for_slug(bundle, entry["section_slug"])
            if label:
                entry["filing_label"] = label
                entry["note"] = label
        return entry
    if policy.get("cite_policy_id"):
        policy_id = policy["cite_policy_id"]
        for note in bundle.get("policy_notes", []):
            if note.get("policy_id") != policy_id:
                continue
            doc_id = note.get("doc_id", "")
            section_slug = policy.get("section_slug") or _section_slug_for_doc(bundle, doc_id) or "quantitative_actuals"
            return {
                "metric_id": metric_id,
                "doc_id": doc_id,
                "section_slug": section_slug,
                "snippet": policy.get("snippet") or note.get("statement", ""),
            }
    return None


def submission_from_gt(task_id: str, gt_path: Path | None = None) -> dict:
    """Build agent_submission_v1 from GT citations + gold_path computed_citations (P3-32)."""
    doc = load_ground_truth_doc(task_id, gt_path)
    metrics = l1_values_from_gt(task_id, gt_path)
    from task_registry import load_bundle, load_gold_path

    bundle = load_bundle(task_id)
    gold_path = load_gold_path(task_id)
    computed_policy = (gold_path.get("l3_citation_rules") or {}).get("computed_citations") or {}

    extracted_map: dict[str, dict] = {}
    citations: list[dict] = []
    for item in doc.get("extracted_values", []):
        cite = item.get("citation") or {}
        snippet = cite.get("snippet")
        if not snippet:
            continue
        entry = _build_citation_entry(item["metric_id"], cite, bundle)
        extracted_map[item["metric_id"]] = entry
        citations.append(entry)

    for item in doc.get("computed_values", []):
        mid = item["metric_id"]
        policy = computed_policy.get(mid)
        if not policy:
            continue
        entry = _computed_citation(mid, policy, extracted_map, bundle)
        if entry:
            citations.append(entry)

    cite_by_metric = {c["metric_id"]: c for c in citations}
    ordered_citations = [cite_by_metric[mid] for mid in metrics if mid in cite_by_metric]
    seen = {c["metric_id"] for c in ordered_citations}
    for c in citations:
        if c["metric_id"] not in seen:
            ordered_citations.append(c)
            seen.add(c["metric_id"])

    policy_ids = doc.get("required_policy_acknowledgements") or []
    for note in bundle.get("policy_notes", []):
        if note.get("agent_ack_required") and note.get("policy_id") not in policy_ids:
            policy_ids.append(note["policy_id"])
    return {
        "schema_version": "agent_submission_v1",
        "metrics": metrics,
        "citations": ordered_citations,
        "policy_acknowledgements": list(dict.fromkeys(policy_ids)),
    }


def googl_gold_values() -> dict:
    doc = load_ground_truth_doc("GOOGL_footnote_reconciliation")
    return _values_from_gt_doc(
        doc,
        {
            "google_services_revenue",
            "google_cloud_revenue",
            "other_bets_revenue",
            "segment_sum",
            "hedging_gains_losses",
            "reconciling_item_amount",
            "consolidated_total_revenue",
        },
    )


def amzn_gold_values() -> dict:
    return l1_values_from_gt("AMZN_footnote_reconciliation")


def pep_gold_values(gt: dict | None = None) -> dict:
    if gt is not None:
        values: dict = {}
        for section in ("extracted_values", "computed_values"):
            for item in gt.get(section, []):
                if isinstance(item.get("value"), bool):
                    continue
                values[item["metric_id"]] = item["value"]
        return values
    return l1_values_from_gt("PEP_fx_organic_growth")


def submission_fixture(task_id: str, name: str) -> dict:
    path = BENCH / "contract_fixtures" / f"{task_id}_{name}.json"
    return load_json(path)


def googl_gold_submission() -> dict:
    return submission_fixture("GOOGL_footnote_reconciliation", "submission_gold")


def pep_gold_submission(gt: dict | None = None) -> dict:
    if gt is not None:
        return submission_from_gt("PEP_fx_organic_growth")
    return submission_from_gt("PEP_fx_organic_growth")


def amzn_gold_submission() -> dict:
    return submission_from_gt("AMZN_footnote_reconciliation")


SUBMISSION_TRAP_MODES: dict[str, dict] = {
    "submission_gold": {"expect_l3_pass": True},
    "trap_l3_fake_snippet": {
        "tasks": ["GOOGL_footnote_reconciliation"],
        "expect_fractures": ["CITE_HALLUC"],
        "expect_failure_modes": ["cite_halluc"],
    },
    "trap_l3_wrong_slug": {
        "tasks": ["GOOGL_footnote_reconciliation"],
        "expect_fractures": ["SECTION_MISS"],
        "expect_failure_modes": ["cite_slug_err"],
    },
    "trap_l3_missing_policy": {
        "tasks": ["PEP_fx_organic_growth"],
        "expect_fractures": ["POLICY_OMIT"],
        "expect_failure_modes": ["policy_omit"],
    },
    "trap_l3_halluc_snippet": {
        "tasks": ["PEP_fx_organic_growth"],
        "expect_fractures": ["CITE_HALLUC"],
        "expect_failure_modes": ["cite_halluc"],
    },
    "trap_l3_duplicate_snippet": {
        "tasks": ["PEP_fx_organic_growth"],
        "expect_fractures": ["CITE_BROAD"],
        "expect_failure_modes": ["cite_duplicate_snippet"],
    },
}


def submission_for_mode(mode: str, task_id: str, gt: dict | None = None) -> dict:
    if mode in ("submission_gold", "gold"):
        return submission_from_gt(task_id)

    if mode == "trap_l3_fake_snippet":
        sub = googl_gold_submission()
        sub["citations"][0]["snippet"] = "Microsoft Azure revenue $ 99,999"
        return sub

    if mode == "trap_l3_wrong_slug":
        sub = googl_gold_submission()
        sub["citations"][0]["section_slug"] = "note_99"
        return sub

    if mode == "trap_l3_missing_policy":
        sub = pep_gold_submission(gt)
        sub["policy_acknowledgements"] = []
        return sub

    if mode == "trap_l3_halluc_snippet":
        sub = pep_gold_submission(gt)
        sub["citations"][-1]["snippet"] = "Bloomberg spot EUR/USD 1.12"
        return sub

    if mode == "trap_l3_duplicate_snippet":
        sub = pep_gold_submission(gt)
        dup = "EMEA                            8%"
        for cite in sub["citations"]:
            if cite["metric_id"] in (
                "emea_reported_growth_pct",
                "emea_fx_impact_pct",
                "emea_organic_cc_growth_pct",
            ):
                cite["snippet"] = dup
        return sub

    raise ValueError(f"Unknown submission mode {mode!r}")


def write_submission_fixture(path: Path, mode: str, task_id: str, gt: dict | None = None) -> None:
    payload = submission_for_mode(mode, task_id, gt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_contract_submission_fixtures() -> list[Path]:
    contract_dir = BENCH / "contract_fixtures"
    pep_gt = load_json(PEP_GT_PATH)
    written: list[Path] = []

    specs = [
        ("GOOGL_footnote_reconciliation", "submission_gold", "GOOGL_footnote_reconciliation_submission_gold.json"),
        ("PEP_fx_organic_growth", "submission_gold", "PEP_fx_organic_growth_submission_gold.json"),
        ("GOOGL_footnote_reconciliation", "trap_l3_fake_snippet", "GOOGL_footnote_reconciliation_submission_trap_fake_snippet.json"),
        ("GOOGL_footnote_reconciliation", "trap_l3_wrong_slug", "GOOGL_footnote_reconciliation_submission_trap_wrong_slug.json"),
        ("PEP_fx_organic_growth", "trap_l3_missing_policy", "PEP_fx_organic_growth_submission_trap_missing_policy.json"),
        ("PEP_fx_organic_growth", "trap_l3_halluc_snippet", "PEP_fx_organic_growth_submission_trap_halluc_snippet.json"),
        ("PEP_fx_organic_growth", "trap_l3_duplicate_snippet", "PEP_fx_organic_growth_submission_trap_duplicate_snippet.json"),
        ("AMZN_footnote_reconciliation", "submission_gold", "AMZN_footnote_reconciliation_submission_gold.json"),
        ("KO_footnote_reconciliation", "submission_gold", "KO_footnote_reconciliation_submission_gold.json"),
    ]
    for task_id, mode, filename in specs:
        path = contract_dir / filename
        gt = pep_gt if task_id == "PEP_fx_organic_growth" else None
        write_submission_fixture(path, mode, task_id, gt)
        written.append(path)
    return written


def submission_output_path(agent_output_path: Path) -> Path:
    return agent_output_path.with_name(f"{agent_output_path.stem}_submission.json")


def payload_for_mode(mode: str, task_id: str, gt: dict | None = None) -> dict | None:
    if mode == "gold":
        return l1_values_from_gt(task_id)

    if mode == "trap_googl_sign":
        if task_id != "GOOGL_footnote_reconciliation":
            raise ValueError("trap_googl_sign applies to GOOGL_footnote_reconciliation only")
        values = l1_values_from_gt(task_id)
        values["hedging_gains_losses"] = 180
        if "reconciling_item_amount" in values:
            values["reconciling_item_amount"] = 180
        return values

    if mode == "trap_googl_blind_sum":
        if task_id != "GOOGL_footnote_reconciliation":
            raise ValueError("trap_googl_blind_sum applies to GOOGL_footnote_reconciliation only")
        values = l1_values_from_gt(task_id)
        values["consolidated_total_revenue"] = 110_076
        values["hedging_gains_losses"] = None
        if "reconciling_item_amount" in values:
            values["reconciling_item_amount"] = None
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

    if mode == "trap_ko_omit_bottling":
        if task_id != "KO_footnote_reconciliation":
            raise ValueError("trap_ko_omit_bottling applies to KO_footnote_reconciliation only")
        doc = load_ground_truth_doc(task_id)
        values = l1_values_from_gt(task_id)
        trap = next(
            fm["wrong_signatures"]
            for fm in doc["failure_modes"]
            if fm["id"] == "omit_bottling_investments"
        )
        values.update(trap)
        return values

    if mode in ("malformed", "missing"):
        return None

    raise ValueError(f"Unknown mode {mode!r}")


CONTRACT_MODES: dict[str, dict] = {
    "gold": {
        "tasks": [
            "GOOGL_footnote_reconciliation",
            "PEP_fx_organic_growth",
            "AMZN_footnote_reconciliation",
            "KO_footnote_reconciliation",
        ],
        "expect_fractures": [],
    },
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
    "trap_ko_omit_bottling": {
        "tasks": ["KO_footnote_reconciliation"],
        "expect_fractures": ["RECON_OMIT"],
        "expect_failure_modes": ["omit_bottling_investments"],
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
