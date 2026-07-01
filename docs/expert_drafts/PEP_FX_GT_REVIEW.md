# CFA Review — PEP FX Organic Growth Ground Truth

**Artifact:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Task:** `PEP_fx_organic_growth` (Type M)  
**Scored period:** FY2025 (10-K filed 2026-02-18)  
**Status:** `draft_pending_cfa`  
**Eng draft date:** 2026-07-01  
**CFA review date:** _pending_

---

## Eng summary

Compute constant-currency organic net revenue growth for **Europe** and **AMESA** using weighted-average FX from Note 1 — not spot rates. Trap: agents report GAAP/reported growth (3.9% / 8.2%) as organic CC, or use year-end EUR/USD instead of WAE.

### FY2025 numbers (USD millions — **draft, verify against filing**)

| Region | FY2024 | FY2025 | Reported growth | FX impact | Organic CC |
|--------|--------|--------|-----------------|-----------|------------|
| Europe | 11,892 | 12,354 | 3.9% | -6.1% | **10.0%** |
| AMESA | 5,240 | 5,670 | 8.2% | -1.5% | **9.7%** |

WAE EUR/USD: FY2024 **1.081**, FY2025 **1.024**

---

## CFA checklist

- [ ] All FY2025 figures match PepsiCo 10-K — correct columns (2025 vs 2024)
- [ ] Europe and AMESA geographic definitions match company disclosure
- [ ] Weighted-average FX table cited correctly (not spot / year-end)
- [ ] MD&A organic CC percentages align with ground truth
- [ ] Trap design is fair (`spot_rate_method`, `reported_only`)
- [ ] No investment recommendation required (Type M forensics/modeling)

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

---

## Notes for reviewer

This is the **third MVD archetype** (Type M — modeling). Numbers are eng-authored placeholders aligned to the benchmark's 2026 filing timeline; replace with filing-verified values before `published` status.

**Approve when:** checklist complete and verify script passes on ground truth JSON.
