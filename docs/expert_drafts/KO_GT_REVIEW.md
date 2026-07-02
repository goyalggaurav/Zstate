# Expert Review — KO Footnote Reconciliation Ground Truth

**Reviewer:** _pending_  
**Artifact:** `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json`  
**Task:** `KO_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P3-18 / LATER-06 (EDGAR verbatim ingest deferred)  
**Scored period:** FY2025 (fiscal year ended 2025-12-31)  
**Status:** `draft` — **not published** until sign-off below  
**Template:** P3-18 hardened task (GT-native L1 + `submission_from_gt`)

---

## Eng summary

Reconcile **six operating segment net revenues** to **consolidated net operating revenues** for FY2025 from KO Form 10-K (filed **2026-02-20**). Archetype `F_exact`; path roles: `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

**Scored wedge:** six-segment sum must equal consolidated **$50,256M**. **Secondary scored pair:** Latin America reported growth **12%** vs comparable currency-neutral **15%**.

**Issuer note index (bundle SSOT only):** operating segment table is **Note 20** in KO FY2025 10-K — mapped to universal slug `segment_financials`. Task JSON, gold path, and GT citations use slugs only (see [CORPUS_BUNDLE_CONTRACT §1d](../../benchmark_v0.1/docs/CORPUS_BUNDLE_CONTRACT.md)).

**Prior draft error:** Note 19 referenced throughout; corrected to Note 20. `legacy_section_slugs` accepts `note_20` only; `validate_corpus_bundle.py` rejects **sliding drift** (multiple conflicting `note_N` tokens on one registry row).

### Pattern numbers (USD millions unless noted)

| Line | Value | Source (path role · slug) |
|------|-------|---------------------------|
| EMEA net revenues | 9,842 | `segment_financials` |
| Latin America net revenues | 6,115 | `segment_financials` |
| North America net revenues | 18,256 | `segment_financials` |
| Asia Pacific net revenues | 5,934 | `segment_financials` |
| Global Ventures net revenues | 3,218 | `segment_financials` |
| Bottling Investments net revenues | 6,891 | `segment_financials` |
| **Six-segment sum** | **50,256** | computed (L1) |
| Consolidated net operating revenues | 50,256 | `consolidated_primary` |
| Latin America reported growth | 12.0% | `narrative_fx` |
| Latin America CC growth | 15.0% | `narrative_fx` |

**Cross-check:** 9,842 + 6,115 + 18,256 + 5,934 + 3,218 + 6,891 = **50,256** (matches consolidated).

### Trap → fracture map

| Failure mode | Trap value / behavior | Filing source (path role) | Fracture |
|--------------|----------------------|---------------------------|----------|
| `wrong_period` | Consolidated **46,905** | `segment_financials_prior_year` (FY2024 column decoy) | `HALLUC_FILL` |
| `omit_global_ventures` | Skips Global Ventures line; sum ≠ consolidated | `segment_financials` — Costa / innocent brands | `RECON_OMIT` |
| `omit_bottling_investments` | Skips Bottling Investments line | `segment_financials` — majority-owned bottlers | `RECON_OMIT` |
| `latin_fx_swap` | 15% reported / 12% CC (swapped) | `narrative_fx` | `CC_OMIT` |
| `cite_duplicate_snippet` | — | L3 | `CITE_BROAD` |

Decoy slug `segment_financials_prior_year` is **required=false** in bundle; agents must not use it for scored FY2025 metrics.

---

## Expert checklist

### I. Mathematical & Financial Baseline

- [ ] **Segment table anchoring:** All six FY2025 net revenue lines verified against Note 20 operating segment table in KO 10-K FY2025 (`segment_financials` excerpt).
- [ ] **Reconciliation identity:** Six-segment sum equals consolidated **$50,256M** (±0 tolerance in L1).
- [ ] **Consolidated cross-check:** **$50,256M** net operating revenues on Consolidated Statement of Income (`consolidated_primary`).
- [ ] **Latin America FX pair:** **12%** reported vs **15%** CC growth verified in MD&A (`narrative_fx`).

### II. Architecture & Decoy Integrity

- [ ] **KO-specific traps:** Global Ventures omission and Bottling Investments omission are realistic (not a GOOGL hedging clone).
- [ ] **Decoy validity:** FY2024 consolidated **$46,905M** available only via `segment_financials_prior_year`.
- [x] **Universal slug check:** No `Note N` in task JSON, gold path, or GT citations; only in bundle `filing_label` + excerpt header.
- [x] **Sliding-drift guard:** `legacy_section_slugs` for `segment_financials` is `["note_20"]` only; `validate_corpus_bundle.py --task KO_footnote_reconciliation` passes `legacy_note_aligned`.
- [x] **Role-based pathing:** Gold path order `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.
- [x] **Policy ack:** `global_ventures_is_reportable_segment` required in submission.

### III. Compliance & Governance

- [x] **Investment independence:** Type F — no Buy/Hold/Sell in prompt.
- [ ] **Data pipeline maturity:** Full EDGAR verbatim ingest deferred (**LATER-06**). **Mitigation:** Bundle excerpts are SHA-256 hash-linked in `ko_fy2025_bundle.json` / `corpus_manifest_v1.json`; expert must verify numbers against filing before publish.

---

## Source breadcrumbs (audit trail)

| Document | doc_id | Filing date | SEC URL |
|----------|--------|-------------|---------|
| FY2025 Form 10-K | `KO_10K_2025` | 2026-02-20 | [10-K](https://www.sec.gov/Archives/edgar/data/21344/000002134426000008/ko-20251231.htm) |

**Bundle excerpt headers to verify:** `Note 20 — Operating Segments` (FY2025 and FY2024 decoy columns).

---

## Artifact paths

| Role | Path |
|------|------|
| Ground truth | `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json` |
| Corpus bundle | `benchmark_v0.1/corpus/ko_fy2025_bundle.json` |
| Gold path | `benchmark_v0.1/gold_paths/KO_footnote_reconciliation.json` |
| Task | `benchmark_v0.1/tasks/KO_footnote_reconciliation.json` |
| L1 verifier | `benchmark_v0.1/scripts/verify_footnote_exact.py` |
| GT-derived fixture | `benchmark_v0.1/contract_fixtures/KO_footnote_reconciliation_submission_gold.json` |

---

## Eng verification

```bash
python3 benchmark_v0.1/scripts/verify_footnote_exact.py \
  --ground-truth benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json

python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task KO_footnote_reconciliation

python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task KO_footnote_reconciliation
```

**Wrong-period trap** — set `"consolidated_net_revenues": 46905` → `wrong_period` / `HALLUC_FILL`.

**Global Ventures omit** — null `global_ventures_net_revenues` with consolidated 50,256 → `omit_global_ventures` / `RECON_OMIT`.

**Contract fixture (GT-derived — labels from bundle registry):**

```bash
python3 -c "
import sys
sys.path.insert(0, 'benchmark_v0.1/scripts')
from agent_output_contract import submission_from_gt
sub = submission_from_gt('KO_footnote_reconciliation')
assert sub['citations'][0]['section_slug'] == 'segment_financials'
assert 'Note 20' in sub['citations'][0]['filing_label']
print('OK', sub['citations'][0]['filing_label'])
"
```

---

## Expert verdict

| Field | Value |
|-------|-------|
| Reviewer | _pending_ |
| Review date | _pending_ |
| Decision | ☐ Approve publish &nbsp; ☐ Revise wedge &nbsp; ☐ Reject task |

**Blockers:** Expert must verify **Note 20** segment table numbers against KO 10-K FY2025 before changing manifest status to `published`. Confirm excerpt header reads `Note 20 — Operating Segments`.
