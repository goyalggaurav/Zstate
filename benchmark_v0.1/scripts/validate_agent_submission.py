#!/usr/bin/env python3
"""
Layer 3 validation — agent submission citations and policy acknowledgements (P2-04d).

Usage:
  python validate_agent_submission.py --task GOOGL_footnote_reconciliation \\
    --submission ../contract_fixtures/GOOGL_footnote_reconciliation_submission_gold.json
  python validate_agent_submission.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent
ROOT = BENCH.parent

sys.path.insert(0, str(SCRIPTS))

from archetype_roles import canonicalize_section_slug  # noqa: E402
from benchmark_tool_backend import load_bundle  # noqa: E402 — re-export for tests
from fracture_registry import fracture_codes as resolve_fracture_codes, layer_map  # noqa: E402
from l3_citation_rules import (  # noqa: E402
    anchor_ok,
    build_metric_units,
    infer_metric_unit,
    is_note_number_only,
    merge_l3_rules,
    numeric_in_snippet,
    numeric_optional,
    resolve_metric_anchors,
)
from synthetic_l3 import check_synthetic_l3_submission, synthetic_l3_skipped  # noqa: E402
from task_registry import load_bundle, load_gold_path, load_task  # noqa: E402

FAILURE_FRACTURE = layer_map("L3")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def snippet_present(excerpt: str, snippet: str) -> bool:
    norm_excerpt = normalize(excerpt)
    if "..." in snippet:
        parts = [normalize(part) for part in snippet.split("...") if normalize(part)]
        pos = 0
        for part in parts:
            idx = norm_excerpt.find(part, pos)
            if idx == -1:
                return False
            pos = idx + len(part)
        return True
    return normalize(snippet) in norm_excerpt


def excerpt_for_slug(bundle: dict, section_slug: str) -> str | None:
    for entry in bundle.get("section_registry", []):
        if entry.get("section_slug") == section_slug:
            doc_key = entry.get("document_key")
            if doc_key and doc_key in bundle.get("documents", {}):
                return bundle["documents"][doc_key].get("excerpt", "")
    return None


def allowed_doc_ids(task: dict) -> set[str]:
    return {doc["doc_id"] for doc in task.get("required_documents", []) if doc.get("doc_id")}


def registry_slugs(bundle: dict) -> set[str]:
    return {entry["section_slug"] for entry in bundle.get("section_registry", [])}


def required_policy_ids(bundle: dict) -> list[str]:
    return [
        note["policy_id"]
        for note in bundle.get("policy_notes", [])
        if note.get("agent_ack_required")
    ]


def l3_citation_rules_for_task(task_id: str, gold_path: dict | None = None, task: dict | None = None) -> dict:
    gold_path = gold_path if gold_path is not None else load_gold_path(task_id)
    task = task or load_task(task_id)
    archetype = gold_path.get("archetype") or task.get("archetype", "")
    return merge_l3_rules(archetype, gold_path.get("l3_citation_rules"))


def _apply_citation_hardening(
    *,
    metric_id: str | None,
    snippet: str,
    section_slug: str | None,
    metric_value: Any,
    l3_rules: dict,
    metric_units: dict[str, str],
    prefix: str,
    checks: list[dict],
    failure_modes: list[str],
) -> bool:
    ok = True
    max_chars = l3_rules.get("max_snippet_chars")
    if max_chars and len(snippet) > int(max_chars):
        failure_modes.append("cite_broad")
        checks.append({
            "check": f"{prefix}.snippet_length",
            "pass": False,
            "max_chars": max_chars,
            "actual_chars": len(snippet),
        })
        ok = False

    if l3_rules.get("forbid_note_number_only") and is_note_number_only(snippet):
        failure_modes.append("cite_broad")
        checks.append({"check": f"{prefix}.note_only", "pass": False})
        ok = False

    if l3_rules.get("require_numeric_in_snippet") and metric_id and not numeric_optional(metric_id, l3_rules):
        unit = infer_metric_unit(metric_id, metric_units) if metric_id else None
        if not numeric_in_snippet(metric_value, snippet, unit=unit):
            failure_modes.append("cite_halluc")
            checks.append({"check": f"{prefix}.numeric_anchor", "pass": False, "metric_id": metric_id})
            ok = False

    anchors = l3_rules.get("metric_citation_anchors") or {}
    if metric_id and metric_id in anchors:
        anchor_pass, reason = anchor_ok(snippet, anchors[metric_id], section_slug=section_slug)
        if not anchor_pass:
            failure_modes.append("cite_broad")
            checks.append({
                "check": f"{prefix}.{reason}",
                "pass": False,
                "metric_id": metric_id,
            })
            ok = False
        else:
            checks.append({"check": f"{prefix}.citation_anchor", "pass": True, "metric_id": metric_id})

    return ok


def validate_submission(
    submission: dict,
    *,
    task_id: str,
    task: dict | None = None,
    bundle: dict | None = None,
    synthetic_l3_eval: bool = False,
) -> dict:
    task = task or load_task(task_id)
    bundle = bundle or load_bundle(task_id)
    gold_path = load_gold_path(task_id)
    l3_rules = l3_citation_rules_for_task(task_id, gold_path, task)
    from task_registry import load_ground_truth as registry_load_gt

    try:
        gt_doc = registry_load_gt(task_id)
    except ValueError:
        gt_doc = {}
    l3_rules = dict(l3_rules)
    l3_rules["metric_citation_anchors"] = resolve_metric_anchors(
        gt_doc, l3_rules.get("metric_citation_anchors")
    )
    metric_units = build_metric_units(gt_doc, l3_rules)
    checks: list[dict] = []
    failure_modes: list[str] = []

    if submission.get("schema_version") != "agent_submission_v1":
        failure_modes.append("schema_invalid")
        checks.append({"check": "schema_version", "pass": False, "expected": "agent_submission_v1"})
    else:
        checks.append({"check": "schema_version", "pass": True})

    metrics = submission.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        failure_modes.append("schema_invalid")
        checks.append({"check": "metrics_present", "pass": False})
        metrics = {}
    else:
        checks.append({"check": "metrics_present", "pass": True})

    citations = submission.get("citations")
    if not isinstance(citations, list) or not citations:
        failure_modes.append("cite_missing")
        checks.append({"check": "citations_non_empty", "pass": False})
        citations = []
    else:
        checks.append({"check": "citations_non_empty", "pass": True})

    doc_ids = allowed_doc_ids(task)
    slugs = registry_slugs(bundle)
    cited_metrics: set[str] = set()
    metric_citation_ok: dict[str, bool] = {}

    for idx, cite in enumerate(citations):
        prefix = f"citation[{idx}]"
        metric_id = cite.get("metric_id")
        doc_id = cite.get("doc_id")
        section_slug = cite.get("section_slug")
        if section_slug:
            section_slug = canonicalize_section_slug(bundle, section_slug)
        snippet = cite.get("snippet")
        cite_ok = True

        if metric_id and metric_id not in metrics:
            failure_modes.append("cite_orphan_metric")
            checks.append({"check": f"{prefix}.metric_id", "pass": False, "metric_id": metric_id})
            cite_ok = False
        elif metric_id:
            cited_metrics.add(metric_id)
            checks.append({"check": f"{prefix}.metric_id", "pass": True, "metric_id": metric_id})

        if doc_id not in doc_ids:
            failure_modes.append("cite_doc_err")
            checks.append({"check": f"{prefix}.doc_id", "pass": False, "doc_id": doc_id})
            cite_ok = False
        else:
            checks.append({"check": f"{prefix}.doc_id", "pass": True, "doc_id": doc_id})

        if section_slug not in slugs:
            failure_modes.append("cite_slug_err")
            checks.append({"check": f"{prefix}.section_slug", "pass": False, "section_slug": section_slug})
            excerpt = None
            cite_ok = False
        else:
            checks.append({"check": f"{prefix}.section_slug", "pass": True, "section_slug": section_slug})
            excerpt = excerpt_for_slug(bundle, section_slug)

        if not snippet:
            failure_modes.append("cite_halluc")
            checks.append({"check": f"{prefix}.snippet", "pass": False, "reason": "missing snippet"})
            cite_ok = False
        elif excerpt is None:
            failure_modes.append("cite_halluc")
            checks.append({"check": f"{prefix}.snippet", "pass": False, "reason": "no excerpt for slug"})
            cite_ok = False
        elif not snippet_present(excerpt, snippet):
            failure_modes.append("cite_halluc")
            checks.append({"check": f"{prefix}.snippet", "pass": False, "reason": "not in section excerpt"})
            cite_ok = False
        else:
            checks.append({"check": f"{prefix}.snippet", "pass": True})
            if not _apply_citation_hardening(
                metric_id=metric_id,
                snippet=snippet,
                section_slug=section_slug,
                metric_value=metrics.get(metric_id) if metric_id else None,
                l3_rules=l3_rules,
                metric_units=metric_units,
                prefix=prefix,
                checks=checks,
                failure_modes=failure_modes,
            ):
                cite_ok = False

        if metric_id:
            metric_citation_ok[metric_id] = metric_citation_ok.get(metric_id, True) and cite_ok

    if l3_rules.get("distinct_snippets_required") and citations:
        norm_by_metric: dict[str, str] = {}
        for cite in citations:
            metric_id = cite.get("metric_id")
            snippet = cite.get("snippet")
            if not metric_id or not snippet:
                continue
            norm = normalize(snippet)
            norm_by_metric[metric_id] = norm
        seen: dict[str, str] = {}
        for metric_id, norm in norm_by_metric.items():
            if norm in seen:
                failure_modes.append("cite_duplicate_snippet")
                checks.append({
                    "check": f"metric_cited.{metric_id}.distinct_snippet",
                    "pass": False,
                    "duplicate_of": seen[norm],
                    "snippet_norm": norm[:80],
                })
                metric_citation_ok[metric_id] = False
                if seen[norm] in metric_citation_ok:
                    metric_citation_ok[seen[norm]] = False
            else:
                seen[norm] = metric_id
                checks.append({
                    "check": f"metric_cited.{metric_id}.distinct_snippet",
                    "pass": True,
                })

    for metric_id in metrics:
        if metric_id not in cited_metrics:
            failure_modes.append("cite_incomplete")
            checks.append({"check": f"metric_cited.{metric_id}", "pass": False})
            metric_citation_ok[metric_id] = False

    acks = submission.get("policy_acknowledgements") or []
    if not isinstance(acks, list):
        acks = []
    required_policies = required_policy_ids(bundle)
    policy_pass = 0
    for policy_id in required_policies:
        ok = policy_id in acks
        checks.append({"check": f"policy_ack.{policy_id}", "pass": ok, "required": True})
        if ok:
            policy_pass += 1
        else:
            failure_modes.append("policy_omit")

    if synthetic_l3_eval:
        synthetic_report = check_synthetic_l3_submission(submission, bundle)
        if not synthetic_report["synthetic_l3_pass"]:
            failure_modes.extend(synthetic_report["failure_modes"])
    else:
        synthetic_report = synthetic_l3_skipped()

    failure_modes = list(dict.fromkeys(failure_modes))
    fracture_codes_list = resolve_fracture_codes(failure_modes, layer="L3")
    l3_pass = not failure_modes

    metric_ids = list(metrics.keys())
    citation_pass = sum(1 for mid in metric_ids if metric_citation_ok.get(mid)) if metric_ids else 0
    citation_fraction = citation_pass / len(metric_ids) if metric_ids else 0.0
    policy_fraction = policy_pass / len(required_policies) if required_policies else 1.0
    l3_score = round(0.85 * citation_fraction + 0.15 * policy_fraction, 4)

    return {
        "task_id": task_id,
        "layer": "L3",
        "l3_pass": l3_pass,
        "l3_score": l3_score,
        "all_pass": l3_pass,
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes_list,
        "checks": checks,
        "citation_count": len(citations),
        "metrics_cited": sorted(cited_metrics),
        "synthetic_l3": synthetic_report,
        "components": {
            "citation_fraction": round(citation_fraction, 4),
            "policy_fraction": round(policy_fraction, 4),
            "metrics_with_valid_citation": citation_pass,
            "metric_count": len(metric_ids),
        },
    }


def validate_fixture(path: Path) -> dict:
    name = path.stem
    if "_submission_" not in name:
        raise ValueError(f"Not a submission fixture: {path.name}")
    task_id = name.split("_submission_", 1)[0]
    submission = load_json(path)
    report = validate_submission(submission, task_id=task_id)
    report["submission_path"] = str(path)
    return report


def validate_all_fixtures() -> dict:
    fixture_dir = BENCH / "contract_fixtures"
    results: list[dict] = []
    for path in sorted(fixture_dir.glob("*_submission_*.json")):
        results.append(validate_fixture(path))

    gold = [r for r in results if r["l3_pass"]]
    traps = [r for r in results if not r["l3_pass"]]
    expected_gold = {
        "GOOGL_footnote_reconciliation_submission_gold.json",
        "PEP_fx_organic_growth_submission_gold.json",
        "AMZN_footnote_reconciliation_submission_gold.json",
        "NFLX_guidance_drift_submission_gold.json",
        "KO_footnote_reconciliation_submission_gold.json",
    }
    expected_traps = {
        "GOOGL_footnote_reconciliation_submission_trap_fake_snippet.json",
        "GOOGL_footnote_reconciliation_submission_trap_wrong_slug.json",
        "PEP_fx_organic_growth_submission_trap_missing_policy.json",
        "PEP_fx_organic_growth_submission_trap_halluc_snippet.json",
        "PEP_fx_organic_growth_submission_trap_duplicate_snippet.json",
        "KO_footnote_reconciliation_submission_trap_note_only.json",
    }
    found = {Path(r["submission_path"]).name for r in results}
    missing = (expected_gold | expected_traps) - found
    gold_ok = expected_gold <= {Path(r["submission_path"]).name for r in gold}
    traps_ok = expected_traps <= {Path(r["submission_path"]).name for r in traps}

    return {
        "all_pass": not missing and gold_ok and traps_ok and len(gold) >= 4 and len(traps) >= 6,
        "fixtures_checked": len(results),
        "gold_pass_count": len([r for r in results if Path(r["submission_path"]).name in expected_gold and r["l3_pass"]]),
        "trap_fail_count": len([r for r in results if Path(r["submission_path"]).name in expected_traps and not r["l3_pass"]]),
        "missing_fixtures": sorted(missing),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark agent submission (L3)")
    parser.add_argument("--task", help="Task id, e.g. GOOGL_footnote_reconciliation")
    parser.add_argument("--submission", type=Path, help="Path to agent_submission_v1 JSON")
    parser.add_argument("--all", action="store_true", help="Validate contract_fixtures submission set")
    args = parser.parse_args()

    if args.all:
        report = validate_all_fixtures()
        print(json.dumps(report, indent=2))
        return 0 if report["all_pass"] else 1

    if not args.task or not args.submission:
        parser.error("--task and --submission required unless --all")

    submission_path = args.submission if args.submission.is_absolute() else ROOT / args.submission
    submission = load_json(submission_path)
    report = validate_submission(submission, task_id=args.task)
    report["submission_path"] = str(submission_path)
    print(json.dumps(report, indent=2))
    return 0 if report["l3_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
