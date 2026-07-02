# Expert Review — KO Footnote Reconciliation Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json`  
**Task:** `KO_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P3-18 / LATER-06 (EDGAR verbatim ingest deferred)  
**Scored period:** FY2025 (fiscal year ended 2025-12-31)  
**Status:** `expert_reviewed` — **signed off**  
**Expert review date:** 2026-07-02  
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

- [x] **Note 20 table anchoring:** Verified **Total net operating revenues** row figures for all five operating segments, **Corporate** allocation ($144M), and the **Eliminations** bridge line ($(1,009)M) against Note 20 (page ~116, accession above).
- [x] **Reconciliation identity:** 48,806M + 144M − 1,009M = **47,941M** (matches consolidated with ±0 tolerance).
- [x] **Consolidated cross-check:** **47,941M** verified on Consolidated Statement of Income face (`consolidated_primary`) — agrees with Note 20 Consolidated column.
- [x] **Latin America FX pair:** **(2)%** total net revenue change vs **(12)%** foreign-currency impact on the **same MD&A table row** (`narrative_fx`); `fx_pair_same_sentence` passes in bundle validator.

### II. Architecture & Decoy Integrity

- [x] **Global Ventures sunset:** Item 1 / MD&A confirms segment sunset **January 1, 2025**; Costa (ex-RTD), innocent, and doğadan into **EMEA**; no sixth reportable segment in Note 20 FY2025 column.
- [x] **Decoy validity:** Prior-year consolidated **47,061M** isolated to `segment_financials_prior_year` (required=false); scored metrics must not pull FY2024 column.
- [x] **Third-party vs Total trap:** Filing distinguishes LatAm third-party **6,331M** from Total segment **6,334M** — row confusion fractures via `third_party_row_instead_of_total` / `RECON_OMIT`.
- [x] **Eliminations trap:** Agent that sums 48,806 + 144 without eliminations reaches 48,950M ≠ 47,941M — `omit_eliminations` / `RECON_OMIT`.
- [x] **Universal slug check:** No `Note N` in task JSON, gold path, or GT citations; issuer note index only in bundle `filing_label` + excerpt.
- [x] **Sliding-drift guard:** `legacy_section_slugs: ["note_20"]` only; `validate_corpus_bundle.py` passes `legacy_note_aligned`.
- [x] **F_exact schema (§1e):** GT declares `elimination_metrics: ["intersegment_eliminations"]`; verifier sums bridge lines uniformly.
- [x] **Policy ack:** `global_ventures_sunset_2025` required in submission.

### III. Compliance & Governance

- [x] **Investment independence:** Type F — no Buy/Hold/Sell in prompt.
- [x] **Data pipeline maturity (P3-10 mitigation):** Full EDGAR verbatim ingest deferred (**LATER-06** / SH-06). **Mitigation in place:** each excerpt in `ko_fy2025_bundle.json` carries `excerpt_sha256` + `source_anchor.sec_accession` (`0001628280-26-010047`); filing metadata + `ingest_status: excerpt_vetted` in `corpus_manifest_v1.json`. Validator recomputes digests via `validate_excerpt_provenance`.

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

**Verdict:** approve  

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Date:** 2 July 2026  

**Sign-off:** KO fifth pilot task cleared for **published** benchmark use alongside GOOGL, PEP, AMZN, and NFLX. Elimination-bridge wedge (Note 20 Total row + Corporate + Eliminations) validated against EDGAR accession `0001628280-26-010047`.

### Reconciliation bridge & L3 citation (scale pass, 2026-07-02)

**Verdict:** approve with citation correction (expert-approved intent; eng fix applied)

Note 20 FY2025 **Total net operating revenues** row decomposes as:

| Line | USD M | Role |
|------|-------|------|
| Five operating segments | 48,806 | Operating Segments Total column |
| Corporate | 144 | Additive bridge line |
| Eliminations | (1,009) | Intersegment elimination |
| **Consolidated** | **47,941** | Face + Note 20 Consolidated column |

L1 `reconciliation_bridge_total` (computed) = **full Python bridge** (five segments + Corporate + Eliminations) = **47,941** — same as `consolidated_net_revenues`, **not** the 48,806 operating subtotal.

**L3 citation policy:** computed sum cites `(1,009) | 47,941` — anchors the **Eliminations → Consolidated** tail of the Total row, proving the agent bridged intersegment eliminations. Operating subtotal **48,806** remains visible in segment-line citations (e.g. Bottling → `48,806`).

`reconciliation_bridge_total` in task `structured_fields` approved (GOOGL `segment_sum` parity).

**Expert confirmation (2026-07-02):** Citation `(1,009) | 47,941` locked in — proves eliminations bridged to consolidated. Rename to `reconciliation_bridge_total` deferred → **P3-35** (v0.2 schema pass).
