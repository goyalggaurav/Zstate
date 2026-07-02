# Expert Review — KO Footnote Reconciliation Ground Truth

**Reviewer:** _pending_  
**Artifact:** `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json`  
**Task:** `KO_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P3-18 / LATER-06 (EDGAR verbatim ingest deferred)  
**Scored period:** FY2025 (fiscal year ended 2025-12-31)  
**Status:** `draft` — **not published** until sign-off below  
**EDGAR:** `0001628280-26-010047` · [10-K](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm)

---

## Eng summary

Reconcile **five operating segments' third-party net operating revenues plus Corporate** to **consolidated net operating revenues** for FY2025. Archetype `F_exact`; path roles: `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

**Structural change (FY2025):** Global Ventures **sunset effective 2025-01-01** — Costa/innocent/doğadan rolled into EMEA. Do not score a sixth Global Ventures line.

**Scored wedge:** third-party segment sum + Corporate = consolidated **$47,941M**. **Secondary pair:** Latin America total net revenue change **(2)%** vs FX impact **(12)%** from MD&A decomposition table (same row).

**Issuer note index (bundle SSOT only):** segment table is **Note 20** — universal slug `segment_financials`.

### Pattern numbers (USD millions unless noted)

| Line | Value | Source (path role) |
|------|-------|-------------------|
| EMEA third-party net revenues | 10,833 | `segment_financials` — Third party row |
| Latin America third-party | 6,331 | `segment_financials` |
| North America third-party | 19,579 | `segment_financials` |
| Asia Pacific third-party | 5,328 | `segment_financials` |
| Bottling Investments third-party | 5,726 | `segment_financials` |
| Corporate third-party | 144 | `segment_financials` |
| **Five segments + Corporate** | **47,941** | computed (L1) |
| Consolidated net operating revenues | 47,941 | `consolidated_primary` |
| Latin America total net revenue change | (2.0)% | `narrative_fx` |
| Latin America FX impact | (12.0)% | `narrative_fx` |

**Cross-check:** 10,833 + 6,331 + 19,579 + 5,328 + 5,726 + 144 = **47,941**.

**Do not use** the Note 20 **Total net operating revenues** row (includes intersegment) — sum would be **$48,806M** before eliminations, not equal to consolidated.

### Trap → fracture map

| Failure mode | Trap behavior | Filing source | Fracture |
|--------------|---------------|---------------|----------|
| `wrong_period` | Consolidated **47,061** | `segment_financials_prior_year` / FY2024 column | `HALLUC_FILL` |
| `omit_bottling_investments` | Skips Bottling Investments | Note 20 third-party row | `RECON_OMIT` |
| `omit_corporate` | Omits Corporate **$144M** bridge | Note 20 Corporate column | `RECON_OMIT` |
| `total_column_not_third_party` | Uses Total row LatAm **6,334** not third-party **6,331** | Note 20 intersegment vs third-party | `RECON_OMIT` |
| `latin_fx_swap` | Swaps **(2)%** total with **(12)%** FX | MD&A percent-change table row | `CC_OMIT` |
| `legacy_global_ventures_segment` | Treats Global Ventures as FY2025 segment | Item 1 sunset disclosure | L3 policy / narrative |

**`latin_fx_swap` pre-flight:** Both percentages sit on the **same MD&A table row**:

> Latin America | (1) | 11 | **(12)** | — | **(2)**

Validator: `fx_pair_same_sentence` + `fx_pair_adjacency_gap` in `validate_corpus_bundle.py`.

---

## Expert checklist

### I. Mathematical & Financial Baseline

- [ ] **Third-party row anchoring:** All five FY2025 third-party lines + Corporate verified in Note 20 (`segment_financials`).
- [ ] **Reconciliation identity:** Five segments + Corporate = **$47,941M** consolidated.
- [ ] **Consolidated cross-check:** **$47,941M** on Consolidated Statement of Income (`consolidated_primary`).
- [ ] **Latin America FX pair:** **(2)%** total change vs **(12)%** FX impact in MD&A table (`narrative_fx`).

### II. Architecture & Decoy Integrity

- [ ] **Global Ventures sunset:** Item 1 confirms five segments for FY2025; no sixth segment line in Note 20.
- [ ] **Decoy validity:** FY2024 consolidated **$47,061M** only via `segment_financials_prior_year`.
- [ ] **Third-party vs Total trap:** Total row LatAm **6,334** ≠ third-party **6,331** — realistic column confusion.
- [x] **Universal slug check:** No `Note N` in task JSON, gold path, or GT citations.
- [x] **Sliding-drift guard:** `legacy_section_slugs: ["note_20"]` only.
- [x] **Policy ack:** `global_ventures_sunset_2025` required.

### III. Compliance & Governance

- [x] **Investment independence:** Type F — no Buy/Hold/Sell in prompt.
- [ ] **Data pipeline maturity:** LATER-06 deferred; bundle excerpts expert-vetted against EDGAR accession above.

---

## Eng verification

```bash
python3 benchmark_v0.1/scripts/verify_footnote_exact.py \
  --ground-truth benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json

python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task KO_footnote_reconciliation

python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task KO_footnote_reconciliation
```

**Wrong-period trap** — `"consolidated_net_revenues": 47061` → `wrong_period` / `HALLUC_FILL`.

**Bottling omit** — null `bottling_investments_net_revenues` with consolidated 47,941 → `omit_bottling_investments` / `RECON_OMIT`.

**FX swap** — total **-12**, FX **-2** → `latin_fx_swap` / `CC_OMIT`.

---

## Expert verdict

| Field | Value |
|-------|-------|
| Reviewer | _pending_ |
| Review date | _pending_ |
| Decision | ☐ Approve publish &nbsp; ☐ Revise wedge &nbsp; ☐ Reject task |

**Blockers:** Expert spot-check Note 20 third-party row and MD&A Latin America table row against live 10-K before `published` status.
