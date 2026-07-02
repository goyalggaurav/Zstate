#!/usr/bin/env python3
"""Validate Track A corpus bundles against ground truth and contract §4."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "benchmark_v0.1"

sys.path.insert(0, str(BENCH / "scripts"))
from task_registry import all_task_ids, corpus_bundle_path  # noqa: E402

# Contract §4 required phrases beyond GT citation snippets.
CONTRACT_PHRASES: dict[str, list[str]] = {
    "GOOGL_footnote_reconciliation": [
        "89,637",
        "20,028",
        "411",
        "not allocated to reportable segments",
        "Hedging gains (losses)",
        "(180)",
        "Total revenues $ 109,896",
    ],
    "PEP_fx_organic_growth": [
        "EMEA $ 18,025",
        "EMEA $ 16,658",
        "LatAm Foods $ 10,549",
        "LatAm Foods $ 10,568",
        "8%",
        "2%",
        "6%",
        "(0.2)%",
        "(4.7)%",
        "4.5%",
        "does not include a weighted-average FX rate table",
    ],
    "AMZN_footnote_reconciliation": [
        "426,305",
        "161,894",
        "128,725",
        "716,924",
        "637,959",
        "stock-based compensation",
        "not allocated to segment results",
        "19,467",
        "increased 13%",
        "increased 10% excluding changes in foreign exchange rates",
    ],
    "NFLX_guidance_drift": [
        "cash content spend of roughly $18B",
        "12,039,405",
        "4,002,744",
        "Nine months ended September 30, 2025",
        "Content amortization on the income statement is not the same as content cash payments",
        "7,385,470",
    ],
    "KO_footnote_reconciliation": [
        "9,842",
        "6,115",
        "18,256",
        "5,934",
        "3,218",
        "6,891",
        "50,256",
        "46,905",
        "Note 20",
        "Global Ventures",
        "Bottling Investments",
        "increased 12%",
        "increased 15% on a comparable currency neutral basis",
    ],
}


sys.path.insert(0, str(BENCH / "scripts"))
from archetype_roles import validate_registry as validate_archetype_registry  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def combined_excerpts(bundle: dict) -> str:
    parts = [doc.get("excerpt", "") for doc in bundle.get("documents", {}).values()]
    return "\n".join(parts)


def snippet_present(combined: str, snippet: str) -> bool:
    norm_combined = normalize(combined)
    if "..." in snippet:
        parts = [normalize(part) for part in snippet.split("...") if normalize(part)]
        pos = 0
        for part in parts:
            idx = norm_combined.find(part, pos)
            if idx == -1:
                return False
            pos = idx + len(part)
        return True
    return normalize(snippet) in norm_combined


def gt_snippets(ground_truth: dict) -> list[str]:
    snippets: list[str] = []
    for item in ground_truth.get("extracted_values", []):
        citation = item.get("citation") or {}
        snippet = citation.get("snippet")
        if snippet:
            snippets.append(snippet)
    for anchor in ground_truth.get("qualitative_anchors", []):
        ref = anchor.get("reference_text")
        if ref:
            snippets.append(ref)
    return snippets


PEP_POLICY_REQUIRED = {
    "PEP_fx_organic_growth": ["no_wae_fx_table"],
    "AMZN_footnote_reconciliation": ["sbc_not_in_segment_oi"],
    "NFLX_guidance_drift": ["amortization_not_cash_spend"],
}


def validate_section_registry(
    bundle: dict,
    gold_path: dict,
    task_json: dict,
) -> list[tuple[str, str, bool]]:
    """B3 — section_registry ↔ gold_path ↔ retrieval_keys alignment."""
    results: list[tuple[str, str, bool]] = []
    registry = bundle.get("section_registry", [])
    results.append(("section_registry_present", "non_empty", bool(registry)))

    gold_section_ids = {
        s["section_id"]
        for s in gold_path.get("minimal_section_set", [])
        if s.get("required", True)
    }
    registry_section_ids = {entry["section_id"] for entry in registry}
    for sid in gold_section_ids:
        results.append(("gold_path_in_registry", sid, sid in registry_section_ids))

    required_doc_ids = {d["doc_id"] for d in task_json.get("required_documents", [])}
    bundle_doc_ids = {d.get("doc_id") for d in bundle.get("documents", {}).values()}
    slugs_in_registry = set()
    for entry in registry:
        slug = entry["section_slug"]
        slugs_in_registry.add(slug)
        doc_key = entry.get("document_key", "")
        results.append(
            ("registry_document_key", doc_key, doc_key in bundle.get("documents", {}))
        )
        doc_id = entry.get("doc_id", "")
        if entry.get("required", False):
            doc_ok = doc_id in required_doc_ids
        else:
            doc_ok = doc_id in bundle_doc_ids
        results.append(("registry_doc_id", doc_id, doc_ok))
        if entry.get("required", False):
            slug = entry["section_slug"]
            search_keys = bundle.get("retrieval_keys", {}).get("Search_Filing", {})
            has_key = any(k.endswith(f":{slug}") for k in search_keys)
            results.append(("required_slug_has_retrieval_key", slug, has_key))

    search_keys = bundle.get("retrieval_keys", {}).get("Search_Filing", {})
    for key in search_keys:
        slug = key.rsplit(":", 1)[-1]
        results.append(("retrieval_slug_in_registry", slug, slug in slugs_in_registry))

    return results


_NOTE_NUM_IN_SLUG = re.compile(r"note_(\d+)", re.I)
_NOTE_NUM_IN_LABEL = re.compile(r"Note\s+(\d+)", re.I)


def _note_numbers_in_slug(token: str) -> set[int]:
    return {int(m.group(1)) for m in _NOTE_NUM_IN_SLUG.finditer(token.replace("-", "_"))}


def _canonical_note_numbers(entry: dict, bundle: dict) -> set[int]:
    """Issuer note index from filing_label + excerpt header (single SSOT per registry row)."""
    nums: set[int] = set()
    for text in (entry.get("filing_label") or "",):
        nums.update(int(m.group(1)) for m in _NOTE_NUM_IN_LABEL.finditer(text))
    doc_key = entry.get("document_key", "")
    excerpt = bundle.get("documents", {}).get(doc_key, {}).get("excerpt", "")
    if excerpt:
        header = excerpt.strip().split("\n", 1)[0]
        nums.update(int(m.group(1)) for m in _NOTE_NUM_IN_LABEL.finditer(header))
    return nums


def validate_legacy_slugs_no_sliding_drift(bundle: dict) -> list[tuple[str, str, bool]]:
    """Legacy note_* slugs must not contradict filing_label — prevents wrong-note acceptance."""
    results: list[tuple[str, str, bool]] = []
    for entry in bundle.get("section_registry", []):
        slug = entry.get("section_slug", "?")
        legacy = entry.get("legacy_section_slugs") or []
        if not legacy:
            continue

        canonical_notes = _canonical_note_numbers(entry, bundle)
        legacy_note_nums: set[int] = set()
        for leg in legacy:
            if leg == slug:
                results.append((f"legacy_not_canonical_slug.{slug}", leg, False))
            legacy_note_nums.update(_note_numbers_in_slug(leg))

        if len(legacy_note_nums) > 1:
            results.append(
                (
                    f"legacy_sliding_drift.{slug}",
                    ",".join(str(n) for n in sorted(legacy_note_nums)),
                    False,
                )
            )

        if canonical_notes and legacy_note_nums:
            stray = legacy_note_nums - canonical_notes
            aligned = not stray and len(legacy_note_nums) <= 1
            results.append(
                (
                    f"legacy_note_aligned.{slug}",
                    ",".join(str(n) for n in sorted(canonical_notes)),
                    aligned,
                )
            )
            if stray:
                results.append(
                    (
                        f"legacy_note_stray.{slug}",
                        ",".join(str(n) for n in sorted(stray)),
                        False,
                    )
                )

    return results


def excerpt_sha256(excerpt: str) -> str:
    return hashlib.sha256(normalize(excerpt).encode("utf-8")).hexdigest()


def manifest_by_doc_id(manifest: dict) -> dict[str, dict]:
    return {doc["doc_id"]: doc for doc in manifest.get("documents", [])}


def validate_excerpt_provenance(
    bundle: dict,
    manifest: dict,
) -> list[tuple[str, str, bool]]:
    """Recompute excerpt_sha256 and cross-check manifest accession metadata."""
    results: list[tuple[str, str, bool]] = []
    manifest_docs = manifest_by_doc_id(manifest)
    for doc_key, doc in bundle.get("documents", {}).items():
        excerpt = doc.get("excerpt", "")
        doc_id = doc.get("doc_id", doc_key)
        if not excerpt:
            continue
        digest = excerpt_sha256(excerpt)
        expected = doc.get("excerpt_sha256")
        if expected:
            results.append((f"excerpt_sha256.{doc_id}", expected[:16], digest == expected))
        manifest_row = manifest_docs.get(doc_id)
        if manifest_row and manifest_row.get("excerpt_sha256"):
            results.append(
                (
                    f"manifest_excerpt_sha256.{doc_id}",
                    manifest_row["excerpt_sha256"][:16],
                    manifest_row["excerpt_sha256"] == digest,
                )
            )
        anchor = doc.get("source_anchor") or {}
        accession = anchor.get("sec_accession")
        if accession and manifest_row:
            manifest_acc = manifest_row.get("sec_accession")
            if manifest_acc:
                results.append(
                    (f"manifest_accession.{doc_id}", accession, accession == manifest_acc)
                )
    return results


def required_section_excerpts(bundle: dict) -> str:
    required_slugs = {
        entry["section_slug"]
        for entry in bundle.get("section_registry", [])
        if entry.get("required", True)
    }
    parts: list[str] = []
    for entry in bundle.get("section_registry", []):
        if entry.get("section_slug") not in required_slugs:
            continue
        doc_key = entry.get("document_key", "")
        doc = bundle.get("documents", {}).get(doc_key, {})
        parts.append(doc.get("excerpt", ""))
    return normalize("\n".join(parts))


def validate_synthetic_l3_bait(bundle: dict) -> list[tuple[str, str, bool]]:
    """Synthetic bait must live in decoy excerpts only — never in required sections."""
    results: list[tuple[str, str, bool]] = []
    required_text = required_section_excerpts(bundle)
    for entry in bundle.get("section_registry", []):
        for bait in entry.get("synthetic_l3_bait", []) or []:
            bait_id = bait.get("bait_id", "unknown")
            snippet = bait.get("snippet", "")
            if not snippet:
                results.append((f"synthetic_bait_snippet.{bait_id}", "non_empty", False))
                continue
            decoy_doc = bundle.get("documents", {}).get(entry.get("document_key", ""), {})
            decoy_excerpt = normalize(decoy_doc.get("excerpt", ""))
            results.append(
                (
                    f"synthetic_bait_in_decoy.{bait_id}",
                    snippet[:40],
                    normalize(snippet) in decoy_excerpt,
                )
            )
            results.append(
                (
                    f"synthetic_bait_not_in_required.{bait_id}",
                    snippet[:40],
                    normalize(snippet) not in required_text,
                )
            )
    return results


def validate_policy_notes(bundle: dict, task_id: str) -> list[tuple[str, str, bool]]:
    results: list[tuple[str, str, bool]] = []
    notes = bundle.get("policy_notes", [])
    notes_by_id = {n["policy_id"]: n for n in notes}
    combined = normalize(combined_excerpts(bundle)).lower()
    for policy_id in PEP_POLICY_REQUIRED.get(task_id, []):
        results.append(("policy_note_required", policy_id, policy_id in notes_by_id))
        if policy_id in notes_by_id:
            stmt = normalize(notes_by_id[policy_id]["statement"]).lower()
            results.append(
                ("policy_statement_in_excerpt", policy_id, stmt[:40] in combined)
            )
    return results


GT_CITATION_STRICT_TASKS = frozenset({"KO_footnote_reconciliation"})


def validate_gt_citations_role_based(
    ground_truth: dict, bundle: dict, *, task_id: str
) -> list[tuple[str, str, bool]]:
    """GT citations must use section_slug; filer note numbers live in bundle filing_label only."""
    results: list[tuple[str, str, bool]] = []
    strict = task_id in GT_CITATION_STRICT_TASKS
    registry_slugs = {e["section_slug"] for e in bundle.get("section_registry", [])}
    for item in ground_truth.get("extracted_values", []):
        mid = item.get("metric_id", "?")
        cite = item.get("citation") or {}
        slug = cite.get("section_slug")
        if strict or slug:
            results.append((f"gt_citation.section_slug.{mid}", slug or "missing", bool(slug)))
            if slug:
                results.append(
                    (f"gt_citation.slug_in_registry.{mid}", slug, slug in registry_slugs)
                )
        if strict:
            results.append(
                (f"gt_citation.no_note_field.{mid}", "note absent", "note" not in cite)
            )
    return results


def validate_task(task_id: str) -> dict:
    bundle_path = corpus_bundle_path(task_id)
    manifest = load_json(BENCH / "manifest.json")
    task_entry = next(t for t in manifest["pilot_tasks"] if t["task_id"] == task_id)

    bundle = load_json(bundle_path)
    ground_truth = load_json(BENCH / task_entry["paths"]["ground_truth"])
    gold_path = load_json(BENCH / task_entry["paths"]["gold_path"])
    task_json = load_json(BENCH / task_entry["paths"]["task"])
    corpus_manifest = load_json(BENCH / "corpus" / "corpus_manifest_v1.json")
    combined = combined_excerpts(bundle)

    checks: list[dict] = []

    def add_check(label: str, required: str, passed: bool) -> None:
        checks.append({"label": label, "required": required, "pass": passed})

    for snippet in gt_snippets(ground_truth):
        add_check("gt_snippet", snippet, snippet_present(combined, snippet))

    for phrase in CONTRACT_PHRASES.get(task_id, []):
        add_check("contract_phrase", phrase, phrase in normalize(combined))

    add_check("bundle_task_id", task_id, bundle.get("task_id") == task_id)
    add_check(
        "retrieval_keys_present",
        "Search_Filing",
        bool(bundle.get("retrieval_keys", {}).get("Search_Filing")),
    )

    for key, doc_key in bundle.get("retrieval_keys", {}).get("Search_Filing", {}).items():
        add_check("retrieval_key_resolves", key, doc_key in bundle.get("documents", {}))

    for label, required, passed in validate_section_registry(bundle, gold_path, task_json):
        add_check(label, required, passed)

    for label, required, passed in validate_legacy_slugs_no_sliding_drift(bundle):
        add_check(label, required, passed)

    for label, required, passed in validate_policy_notes(bundle, task_id):
        add_check(label, required, passed)

    for label, required, passed in validate_excerpt_provenance(bundle, corpus_manifest):
        add_check(label, required, passed)

    for label, required, passed in validate_synthetic_l3_bait(bundle):
        add_check(label, required, passed)

    for label, required, passed in validate_gt_citations_role_based(ground_truth, bundle, task_id=task_id):
        add_check(label, required, passed)

    archetype = task_json.get("archetype") or gold_path.get("archetype") or bundle.get("archetype")
    if archetype:
        add_check("task_archetype_set", archetype, bool(archetype))
        add_check(
            "gold_path_archetype_match",
            archetype,
            gold_path.get("archetype") in (None, archetype) and bundle.get("archetype") in (None, archetype),
        )
        for label, required, passed in validate_archetype_registry(bundle, archetype):
            add_check(label, required, passed)

    return {
        "task_id": task_id,
        "bundle_id": bundle.get("bundle_id"),
        "all_pass": all(c["pass"] for c in checks),
        "checks": checks,
    }


def validate_all() -> dict:
    reports = [validate_task(task_id) for task_id in all_task_ids()]
    return {
        "tasks": [r["task_id"] for r in reports],
        "all_pass": all(r["all_pass"] for r in reports),
        "reports": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate corpus bundles for pilot tasks.")
    parser.add_argument("--task", choices=all_task_ids())
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        report = validate_all()
        print(json.dumps(report, indent=2))
        return 0 if report["all_pass"] else 1

    if not args.task:
        parser.error("Specify --task TASK_ID or --all")

    report = validate_task(args.task)
    print(json.dumps(report, indent=2))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
