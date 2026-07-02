# Expert Review — NFLX Guidance Drift Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/NFLX_guidance_drift_gt.json`  
**Task:** `NFLX_guidance_drift` (Type F, archetype `F_guidance_drift`)  
**Backlog ref:** P2-19 / LATER-06 (EDGAR verbatim ingest deferred)  
**Scored period:** FY2025 guidance vs YTD through 2025Q3  
**Status:** `expert_reviewed` — **signed off**  
**Eng Pattern 1 rebuild:** 2026-07-02  
**Expert review date:** 2026-07-02  
**Checklist revision (grouped audit):** 2026-07-02  

---

## Eng summary

Compare **FY2025 annual cash content spend guidance** (Q4 2024 shareholder letter, filing **2025-01-21**) to **nine-month YTD actual** content cash payments (Q3 2025 10-Q, filing **2025-10-17**). Archetype `F_guidance_drift`; path roles: `narrative_guidance` → `quantitative_actuals`.

**Guidance grain:** annual (~$18B). **Actual grain:** nine months ended September 30, 2025. **Implied pace:** `18,000 × 9/12 = 13,500` USD M — standardized L1 pro-rata baseline (expert-approved).

**Drift:** YTD cash **below** implied annual pace (−10.8%); `guidance_pace_under: true`.

### Pattern 1 numbers (USD millions)

| Line | Value | Source (path role · period) |
|------|-------|----------------------------|
| Annual cash content spend guidance | 18,000 | `narrative_guidance` · 2024Q4 |
| YTD period (months) | 9 | `quantitative_actuals` · 2025Q3 |
| YTD content cash payments | 12,039 | `quantitative_actuals` — additions (12,039,405) |
| Q3 content amortization | 4,003 | `quantitative_actuals` — supplemental (4,002,744) |
| **Implied YTD pace** | **13,500** | `18,000 × 9/12` (L1 computed) |
| Pace variance % | −10.8 | `(12,039 − 13,500) / 13,500 × 100` |
| Below implied pace | true | YTD cash < implied pace |

Cash flow additions are `(12,039,405)` outflow in the filing; GT stores **12,039** USD M absolute (benchmark convention).

### Trap → fracture map

| Failure mode | Trap value | Filing source | Fracture |
|--------------|------------|---------------|----------|
| `wrong_ytd_window` | 7,385 | Q2 2025 10-Q (2025-07-17) six-month additions (7,385,470) | `GUIDANCE_PERIOD_ERR` |
| `amortization_as_cash` | 11,658 | Q3 2025 10-Q (2025-10-17) nine-month amort (11,657,930) | `CASH_VS_AMORT_ERR` |
| `cite_duplicate_snippet` | — | L3 | `CITE_BROAD` |

Decoy slug `quantitative_wrong_ytd_window` maps to **Q2 2025 10-Q** (`period=2025Q2`), not Q3 — six-month column is absent from Q3 cash flow face.

**Cross-check:** 12,039 − 4,654 = 7,385 (nine-month minus Q3 single quarter) — same numeric trap, different retrieval error path.

---

## Expert checklist

### I. Mathematical & Financial Baseline

- [x] **Annual Guidance Anchoring:** $18B annual guide verified against Q4 2024 shareholder letter (filing **2025-01-21**).
- [x] **YTD Actuals Anchoring:** $12,039M nine-month additions verified against Q3 2025 10-Q Cash Flow Statement (filing **2025-10-17**, accession `0001065280-25-000406`).
- [x] **Temporal Reconciliation:** 9/12 pro-rata baseline ($13,500M) confirmed as the standardized L1 reasoning baseline for pace analysis.
- [x] **Metric Accuracy:** Pace variance (−10.8%) and `guidance_pace_under: true` validated against ground truth derivation.

### II. Architecture & Decoy Integrity

- [x] **Trap Validity:** `wrong_ytd_window` (6-mo decoy **7,385M** from Q2 10-Q) and `amortization_as_cash` (9-mo **11,658M** amort from Q3 10-Q) mapped to actual filing lines; cross-contamination prevented via `failure_mode_map` → fracture codes in `verify_guidance_drift.py`.
- [x] **Role-Based Pathing:** Path roles (`narrative_guidance` → `quantitative_actuals`) enforced; `retrieval_period` per slug (2024Q4 vs 2025Q3) eliminates ticker-specific note-number drift.
- [x] **Archetype Alignment:** Verified as `F_guidance_drift` pattern (YTD actuals vs annualized guidance pace).

### III. Compliance & Governance

- [x] **Investment Independence:** Type F classification confirmed; benchmark remains strictly extractive/reconciliatory (no forward-looking sentiment analysis).
- [ ] **Data Pipeline Maturity:** Full EDGAR verbatim ingest and automated filing-level checksums deferred (**LATER-06**). **Mitigation:** Bundle excerpts are **SHA-256 hash-linked** to SEC accession URLs in `nflx_q2q3_2025_bundle.json` and `corpus_manifest_v1.json` (`excerpt_sha256`); expert-vetted until SH-06 ingest.

---

## Source breadcrumbs (2027 audit trail)

| Document | doc_id | Filing date | SEC accession / URL |
|----------|--------|-------------|---------------------|
| Q4 2024 shareholder letter | `NFLX_shareholder_letter_2024Q4` | 2025-01-21 | [Letter PDF](https://cdn.arstechnica.net/wp-content/uploads/2025/01/FINAL-Q4-24-Shareholder-Letter.pdf) |
| Q3 2025 10-Q (actuals) | `NFLX_10Q_2025Q3` | 2025-10-17 | `0001065280-25-000406` · [10-Q](https://www.sec.gov/Archives/edgar/data/1065280/000106528025000406/nflx-20250930.htm) |
| Q2 2025 10-Q (6-mo decoy) | `NFLX_10Q_2025Q2` | 2025-07-17 | `0001065280-25-000323` · [10-Q](https://www.sec.gov/Archives/edgar/data/1065280/000106528025000323.htm) |

---

## Eng verification

```bash
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task NFLX_guidance_drift
python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task NFLX_guidance_drift
```

**YTD window trap** — set `"ytd_content_cash_payments_usd_m": 7385` → `wrong_ytd_window` / `GUIDANCE_PERIOD_ERR`.

**Amort-as-cash trap** — set `"ytd_content_cash_payments_usd_m": 11658` → `amortization_as_cash` / `CASH_VS_AMORT_ERR`.

---

## Expert verdict

**Verdict:** approve  

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Date:** 2 July 2026  

**Sign-off:** NFLX fourth pilot task cleared for **published** benchmark use alongside GOOGL, PEP, and AMZN. Checklist groups Math / Architecture / Governance for auditor navigation; trap provenance corrected to Q2 10-Q for six-month decoy.

### L3 computed-citation policy (scale pass, 2026-07-02)

**Verdict:** approve (expert-delegated; no GT numeric changes)

| Computed metric | Citation policy | Rationale |
|-----------------|-----------------|-----------|
| `implied_ytd_pace_usd_m` | Guidance snippet `"roughly $18B"` | Anchors pro-rata baseline to annual guide |
| `cash_vs_guidance_pace_variance_pct` | Inherits YTD cash citation; numeric optional | Derived metric — variance not verbatim in filing |
| `guidance_pace_under` | Policy note on cash vs amortization | Boolean conclusion requires policy acknowledgment |

Source: `gold_paths/NFLX_guidance_drift.json` → `l3_citation_rules.computed_citations`.
