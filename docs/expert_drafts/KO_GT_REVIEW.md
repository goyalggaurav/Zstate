# Expert Review — KO Footnote Reconciliation Ground Truth

**Reviewer:** _pending_  
**Artifact:** `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json`  
**Task:** `KO_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P3-18 / LATER-06 (EDGAR verbatim ingest deferred)  
**Scored period:** FY2025 (fiscal year ended 2025-12-31)  
**Status:** `draft` — **not published** until sign-off below  
**EDGAR:** `0001628280-26-010047` · [10-K](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm)  
**Schema:** [CORPUS_BUNDLE_CONTRACT §1e](../../benchmark_v0.1/docs/CORPUS_BUNDLE_CONTRACT.md) (`segment_metrics` + `additive_metrics` + `elimination_metrics`)

---

## Eng summary

Reconcile Note 20 **Total net operating revenues** by segment + **Corporate** + **Eliminations** = **Consolidated** ($47,941M). Five reportable segments after **Global Ventures sunset (2025-01-01)**. Path roles: `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

### Pattern numbers (USD millions unless noted)

| Line | Value | Source (path role · Note 20 / face) |
|------|-------|-------------------------------------|
| EMEA total net operating revenues | 11,513 | `segment_financials` — Total row |
| Latin America total net operating revenues | 6,334 | `segment_financials` — Total row |
| North America total net operating revenues | 19,586 | `segment_financials` — Total row |
| Asia Pacific total net operating revenues | 5,638 | `segment_financials` — Total row |
| Bottling Investments total net operating revenues | 5,735 | `segment_financials` — Total row |
| Operating segments subtotal | 48,806 | `segment_financials` — Operating Segments Total |
| Corporate | 144 | `segment_financials` — Corporate column |
| Eliminations | (1,009) | `segment_financials` — Eliminations column |
| **Consolidated** | **47,941** | `segment_financials` — Consolidated column |
| Income statement cross-check | 47,941 | `consolidated_primary` — Net Operating Revenues |
| Latin America total net revenue change | (2.0)% | `narrative_fx` — MD&A decomposition Total |
| Latin America FX impact | (12.0)% | `narrative_fx` — Foreign Currency column |

**Reconciliation identity:** 48,806 + 144 − 1,009 = **47,941** (±0 L1 tolerance).

**Third-party decoy (not scored):** Latin America third-party **6,331M** vs Total **6,334M** — lazy column selection triggers `third_party_row_instead_of_total` / `RECON_OMIT`.

### Trap → fracture map

| Failure mode | Trap value / behavior | Filing source | Fracture |
|--------------|----------------------|---------------|----------|
| `wrong_period` | Consolidated **47,061** | `segment_financials_prior_year` / FY2024 | `HALLUC_FILL` |
| `omit_eliminations` | Skips **(1,009)** eliminations line | Note 20 Eliminations column | `RECON_OMIT` |
| `third_party_row_instead_of_total` | LatAm **6,331** (Third party) not **6,334** (Total) | Note 20 row selection | `RECON_OMIT` |
| `omit_corporate` | Skips Corporate **144** | Note 20 Corporate column | `RECON_OMIT` |
| `omit_bottling_investments` | Skips Bottling segment | Note 20 Total row | `RECON_OMIT` |
| `latin_fx_swap` | Swaps **(2)%** total vs **(12)%** FX | MD&A percent-change table | `CC_OMIT` |
| `legacy_global_ventures_segment` | Treats Global Ventures as FY2025 segment | Item 1 sunset disclosure | L3 policy |

---

## Expert checklist

### I. Mathematical & Financial Baseline

- [ ] **Note 20 table anchoring:** Verified **Total net operating revenues** row figures for all five operating segments, **Corporate** allocation ($144M), and the **Eliminations** bridge line ($(1,009)M) against Note 20 (page ~116, accession above).
- [ ] **Reconciliation identity:** 48,806M + 144M − 1,009M = **47,941M** (matches consolidated with ±0 tolerance).
- [ ] **Consolidated cross-check:** **47,941M** verified on Consolidated Statement of Income face (`consolidated_primary`) — must agree with Note 20 Consolidated column.
- [ ] **Latin America FX pair:** **(2)%** total net revenue change vs **(12)%** foreign-currency impact on the **same MD&A table row** (`narrative_fx`); confirm `fx_pair_same_sentence` passes in bundle validator.

### II. Architecture & Decoy Integrity

- [ ] **Global Ventures sunset:** Item 1 / MD&A confirms segment sunset **January 1, 2025**; Costa (ex-RTD), innocent, and doğadan into **EMEA**; no sixth reportable segment in Note 20 FY2025 column.
- [ ] **Decoy validity:** Prior-year consolidated **47,061M** isolated to `segment_financials_prior_year` (required=false); scored metrics must not pull FY2024 column.
- [ ] **Third-party vs Total trap:** Filing distinguishes LatAm third-party **6,331M** from Total segment **6,334M** — omission or row confusion must fracture (`third_party_row_instead_of_total` or `segment_sum_mismatch`).
- [ ] **Eliminations trap:** Agent that sums 48,806 + 144 without eliminations reaches 48,950M ≠ 47,941M — `omit_eliminations` / `RECON_OMIT`.
- [x] **Universal slug check:** No `Note N` in task JSON, gold path, or GT citations; issuer note index only in bundle `filing_label` + excerpt.
- [x] **Sliding-drift guard:** `legacy_section_slugs: ["note_20"]` only; `validate_corpus_bundle.py` passes `legacy_note_aligned`.
- [x] **F_exact schema (§1e):** GT declares `elimination_metrics: ["intersegment_eliminations"]`; verifier sums bridge lines uniformly.
- [x] **Policy ack:** `global_ventures_sunset_2025` required in submission.

### III. Compliance & Governance

- [x] **Investment independence:** Type F — no Buy/Hold/Sell in prompt.
- [ ] **Data pipeline maturity:** Full EDGAR verbatim ingest deferred (**LATER-06**). **Mitigation:** Bundle excerpts expert-vetted against accession `0001628280-26-010047`; SHA-256 linkage in `ko_fy2025_bundle.json` / `corpus_manifest_v1.json` when ingest lands.

---

## Eng verification

```bash
python3 benchmark_v0.1/scripts/verify_footnote_exact.py \
  --ground-truth benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json

python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task KO_footnote_reconciliation

python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task KO_footnote_reconciliation
```

**Wrong-period trap** — `"consolidated_net_revenues": 47061` → `wrong_period` / `HALLUC_FILL`.

**Eliminations omit** — null `intersegment_eliminations` with consolidated 47,941 → `omit_eliminations` / `RECON_OMIT`.

**Third-party row trap** — `"latin_america_net_revenues": 6331` → `third_party_row_instead_of_total` / `RECON_OMIT`.

**FX swap** — total **−12**, FX **−2** → `latin_fx_swap` / `CC_OMIT`.

---

## Expert verdict

| Field | Value |
|-------|-------|
| Reviewer | _pending_ |
| Review date | _pending_ |
| Decision | ☐ Approve publish &nbsp; ☐ Revise wedge &nbsp; ☐ Reject task |

**Blockers:** Complete all **unchecked** items in §I and §II against live 10-K before changing manifest status to `published`.
