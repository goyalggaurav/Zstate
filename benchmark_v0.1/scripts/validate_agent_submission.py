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

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent
ROOT = BENCH.parent

sys.path.insert(0, str(SCRIPTS))

from benchmark_tool_backend import load_bundle  # noqa: E402

TASK_BUNDLES = {
    "GOOGL_footnote_reconciliation": "corpus/googl_q1_2026_bundle.json",
    "PEP_fx_organic_growth": "corpus/pep_fy2025_bundle.json",
}

FAILURE_FRACTURE = {
    "cite_halluc": "CITE_HALLUC",
    "cite_slug_err": "SECTION_MISS",
    "cite_doc_err": "CITE_BROAD",
    "cite_orphan_metric": "CITE_BROAD",
    "cite_incomplete": "CITE_BROAD",
    "cite_missing": "CITE_BROAD",
    "policy_omit": "POLICY_OMIT",
    "schema_invalid": "CITE_BROAD",
}


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


def load_task(task_id: str) -> dict:
    path = BENCH / "tasks" / f"{task_id}.json"
    return load_json(path)


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


def validate_submission(submission: dict, *, task_id: str, task: dict | None = None, bundle: dict | None = None) -> dict:
    task = task or load_task(task_id)
    bundle = bundle or load_bundle(task_id)
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

        if metric_id:
            metric_citation_ok[metric_id] = metric_citation_ok.get(metric_id, True) and cite_ok

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

    failure_modes = list(dict.fromkeys(failure_modes))
    fracture_codes = list(dict.fromkeys(FAILURE_FRACTURE[m] for m in failure_modes if m in FAILURE_FRACTURE))
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
        "fracture_codes": fracture_codes,
        "checks": checks,
        "citation_count": len(citations),
        "metrics_cited": sorted(cited_metrics),
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
    }
    expected_traps = {
        "GOOGL_footnote_reconciliation_submission_trap_fake_snippet.json",
        "GOOGL_footnote_reconciliation_submission_trap_wrong_slug.json",
        "PEP_fx_organic_growth_submission_trap_missing_policy.json",
        "PEP_fx_organic_growth_submission_trap_halluc_snippet.json",
    }
    found = {Path(r["submission_path"]).name for r in results}
    missing = (expected_gold | expected_traps) - found
    gold_ok = expected_gold <= {Path(r["submission_path"]).name for r in gold}
    traps_ok = expected_traps <= {Path(r["submission_path"]).name for r in traps}

    return {
        "all_pass": not missing and gold_ok and traps_ok and len(gold) >= 2 and len(traps) >= 4,
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
