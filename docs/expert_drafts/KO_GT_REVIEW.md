# Expert Review — KO Footnote Reconciliation Ground Truth

**Reviewer:** _pending_  
**Artifact:** `benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json`  
**Task:** `KO_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P3-18 / LATER-06  
**Scored period:** FY2025  
**Status:** `draft`  
**EDGAR:** `0001628280-26-010047` · [10-K](https://www.sec.gov/Archives/edgar/data/21344/000162828026010047/ko-20251231.htm)

---

## Eng summary

Reconcile Note 20 **Total net operating revenues** by segment + **Corporate** + **Eliminations** = **Consolidated** ($47,941M). Universal `verification_schema` pattern: `segment_metrics` + `additive_metrics` + `elimination_metrics` (see CORPUS_BUNDLE_CONTRACT §1e).

**Global Ventures sunset 2025-01-01** — five reportable segments only.

### Pattern numbers (USD millions unless noted)

| Line | Value | Note 20 row / column |
|------|-------|----------------------|
| EMEA | 11,513 | Total net operating revenues |
| Latin America | 6,334 | Total net operating revenues |
| North America | 19,586 | Total net operating revenues |
| Asia Pacific | 5,638 | Total net operating revenues |
| Bottling Investments | 5,735 | Total net operating revenues |
| Operating segments subtotal | 48,806 | Operating Segments Total |
| Corporate | 144 | Corporate column |
| Eliminations | (1,009) | Eliminations column |
| **Consolidated** | **47,941** | Consolidated column |
| Income statement cross-check | 47,941 | `consolidated_primary` |

**Cross-check:** 11,513 + 6,334 + 19,586 + 5,638 + 5,735 + 144 − 1,009 = **47,941**.

### Trap → fracture map

| Failure mode | Behavior | Fracture |
|--------------|----------|----------|
| `wrong_period` | FY2024 consolidated 47,061 | `HALLUC_FILL` |
| `omit_eliminations` | Sums segments + Corporate, skips (1,009) | `RECON_OMIT` |
| `third_party_row_instead_of_total` | Uses Third party LatAm 6,331 not Total 6,334 | `RECON_OMIT` |
| `omit_corporate` | Skips Corporate 144 | `RECON_OMIT` |
| `omit_bottling_investments` | Skips Bottling segment | `RECON_OMIT` |
| `latin_fx_swap` | Swaps (2)% total vs (12)% FX | `CC_OMIT` |

---

## Expert checklist

- [ ] Note 20 Total row + Eliminations match filing screenshot
- [ ] Consolidated 47,941 matches Consolidated Statement of Income
- [ ] MD&A Latin America row: (2)% total / (12)% FX
- [ ] Global Ventures sunset acknowledged in policy

---

## Eng verification

```bash
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task KO_footnote_reconciliation
python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task KO_footnote_reconciliation
```

---

## Expert verdict

| Field | Value |
|-------|-------|
| Reviewer | _pending_ |
| Decision | ☐ Approve publish &nbsp; ☐ Revise &nbsp; ☐ Reject |
