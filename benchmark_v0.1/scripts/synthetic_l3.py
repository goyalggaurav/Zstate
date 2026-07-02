"""Synthetic L3 decoy-bait detection (P3-15 / P3-09)."""

from __future__ import annotations

from typing import Any

from l3_citation_rules import normalize


def collect_synthetic_bait(bundle: dict) -> list[dict[str, Any]]:
    baits: list[dict[str, Any]] = []
    for entry in bundle.get("section_registry", []):
        slug = entry.get("section_slug")
        for bait in entry.get("synthetic_l3_bait") or []:
            baits.append({**bait, "decoy_section_slug": slug})
    return baits


def snippet_matches_bait(snippet: str, bait_snippet: str) -> bool:
    norm_snip = normalize(snippet)
    norm_bait = normalize(bait_snippet)
    if not norm_bait:
        return False
    return norm_bait in norm_snip or norm_snip in norm_bait


def check_synthetic_l3_submission(submission: dict, bundle: dict) -> dict:
    """Return decoy-bait hits when agent citations reuse synthetic L3 bait text."""
    hits: list[dict[str, Any]] = []
    baits = collect_synthetic_bait(bundle)
    for idx, cite in enumerate(submission.get("citations") or []):
        snippet = cite.get("snippet") or ""
        metric_id = cite.get("metric_id")
        for bait in baits:
            bait_snip = bait.get("snippet") or ""
            if not snippet_matches_bait(snippet, bait_snip):
                continue
            hits.append({
                "citation_index": idx,
                "metric_id": metric_id,
                "bait_id": bait.get("bait_id"),
                "decoy_section_slug": bait.get("decoy_section_slug"),
                "mimics_metric": bait.get("mimics_metric"),
                "expected_fracture": bait.get("expected_fracture_if_cited", "CITE_HALLUC"),
            })
    fracture_codes = sorted({h["expected_fracture"] for h in hits if h.get("expected_fracture")})
    return {
        "synthetic_l3_evaluated": True,
        "synthetic_l3_pass": not hits,
        "synthetic_l3_hits": hits,
        "failure_modes": ["synthetic_l3_bait_cited"] if hits else [],
        "fracture_codes": fracture_codes,
    }


def synthetic_l3_skipped() -> dict:
    return {
        "synthetic_l3_evaluated": False,
        "synthetic_l3_pass": None,
        "synthetic_l3_hits": [],
        "failure_modes": [],
        "fracture_codes": [],
    }
