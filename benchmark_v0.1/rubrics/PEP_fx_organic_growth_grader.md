# Grader Brief — PEP FX Organic Growth

**Task ID:** `PEP_fx_organic_growth` (Type M)  
**Status:** Draft — pending CFA sign-off  
**Canonical prompt:** `benchmark_v0.1/tasks/PEP_fx_organic_growth.json` → `prompt.text`  
**Ground truth:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Verify script:** `benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py`  
**CFA review:** `docs/expert_drafts/PEP_FX_GT_REVIEW.md`

---

## Agent prompt (summary)

Using PepsiCo FY2025 Form 10-K (filed 2026-02-18), compute constant-currency organic net revenue growth for **Europe** and **AMESA** vs FY2024. Extract geographic revenues, **weighted-average FX** from Note 1, Python-verify CC growth, cross-check MD&A disclosed organic percentages. No investment recommendation.

---

## Scoring layers (Type M weights)

| Layer | Weight | What it measures |
|-------|--------|------------------|
| **L1** | 50% | Revenue extraction + CC growth math |
| **L2** | 30% | Assumption log + MD&A cross-check |
| **L3** | 20% | Citation quality (table-level, auditable) |

---

## Failure modes (primary traps)

| ID | Label | Wrong output signature | Fracture code |
|----|-------|------------------------|---------------|
| `spot_rate_method` | Spot rate method | Uses year-end EUR/USD 1.058 / 1.104 instead of WAE 1.024 / 1.081 | `FX_METHOD_ERR` |
| `reported_only` | Reported growth only | Europe CC = 3.9% or AMESA CC = 8.2% (reported, not organic) | `CC_OMIT` |
| `wrong_region` | Wrong geography | LATAM or North America substituted for AMESA/Europe | `SCOPE_ERR` |
| `wrong_period` | Wrong fiscal year | FY2024 10-K as primary or quarterly slice | `HALLUC_FILL` |

---

## Source anchors (human reviewer — draft)

| Metric | Section | Column |
|--------|---------|--------|
| Europe / AMESA net revenue | Note 1 — geographic segment table | FY2025 vs FY2024 |
| Weighted-average EUR/USD | Note 1 — Financial Instruments | FY2025 vs FY2024 |
| Organic CC growth | MD&A — Results of Operations | Europe, AMESA |

---

## FY2025 numbers (USD millions, draft)

| Region | FY2024 | FY2025 | Reported growth | FX impact | Organic CC |
|--------|--------|--------|-----------------|-----------|------------|
| Europe | 11,892 | 12,354 | 3.9% | -6.1% | **10.0%** |
| AMESA | 5,240 | 5,670 | 8.2% | -1.5% | **9.7%** |

WAE EUR/USD: FY2024 **1.081**, FY2025 **1.024**

**CFA action required:** Verify all figures against actual PEP 10-K before changing status to `published`.

---

## Verify command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
```
