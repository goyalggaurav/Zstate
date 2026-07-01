# Expert Review — PEP FX Organic Growth Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Task:** `PEP_fx_organic_growth` (Type M)  
**Scored period:** FY2025 (10-K filed 2026-02-18)  
**Status:** `draft_pending_expert_review`  
**Eng draft date:** 2026-07-01  
**Expert review date:** _pending_

---

## Eng summary

Compute constant-currency organic net revenue growth for **Europe** and **AMESA** using **weighted-average FX from Note 1** — not spot rates.

### Calculation vs MD&A extract (required methodology)

**Both — in sequence, not either/or:**

| Step | Agent must | Scored as |
|------|------------|-----------|
| 1 | Extract reported net revenue (Europe, AMESA) FY2025 vs FY2024 from Note 1 geographic table | L1 extraction |
| 2 | Extract **weighted-average** FX from Note 1 (not spot / year-end) | L1 + trap `spot_rate_method` |
| 3 | **Python:** compute organic CC growth from inputs (show work) | L1 — primary answer |
| 4 | Extract MD&A disclosed organic CC % for Europe and AMESA | L2 cross-check |
| 5 | Reconcile computed vs MD&A within tolerance; cite both in assumption log | L2 pass |

**Do not** allow MD&A copy-only as the sole answer — that bypasses Type M modeling and fails the Python requirement. **Do not** accept reported GAAP growth (3.9% / 8.2%) as organic CC — trap `reported_only`.

Preferred formula path for verify script (align GT to filing disclosure):

`organic_cc ≈ reported_growth − fx_impact` when MD&A discloses both, **or** CC revenue rebuild using WAE when footnote supports it.

### Traps

| Trap | Wrong behavior |
|------|----------------|
| `reported_only` | Europe CC = 3.9% or AMESA CC = 8.2% (reported, not organic) |
| `spot_rate_method` | Year-end EUR/USD 1.058 / 1.104 instead of WAE 1.024 / 1.081 |
| `wrong_region` | LATAM or North America substituted for AMESA/Europe |
| `wrong_period` | Wrong fiscal year column |

### FY2025 numbers (USD millions — **draft, verify against filing**)

| Region | FY2024 | FY2025 | Reported growth | FX impact | Organic CC |
|--------|--------|--------|-----------------|-----------|------------|
| Europe | 11,892 | 12,354 | 3.9% | -6.1% | **10.0%** |
| AMESA | 5,240 | 5,670 | 8.2% | -1.5% | **9.7%** |

WAE EUR/USD: FY2024 **1.081**, FY2025 **1.024**

**Verification today:** SEC URL in `corpus_manifest_v1.json` + manual 10-K review. Full EDGAR text index (LATER-01) not required to sign off GT numbers.

---

## Expert checklist (P2-02)

- [ ] **Methodology:** Task requires independent Python computation **and** MD&A cross-check — not MD&A extract alone
- [ ] All FY2025 figures match PepsiCo 10-K — correct columns (2025 vs 2024) *(verify via SEC filing; GT placeholders below are eng-authored until checked)*
- [ ] Europe and AMESA geographic definitions match company disclosure (not LATAM / North America)
- [ ] Weighted-average FX table cited correctly (not spot / year-end)
- [ ] MD&A organic CC percentages align with ground truth after independent calc
- [ ] Trap design is fair (`spot_rate_method`, `reported_only`, `wrong_region`)
- [ ] No investment recommendation required (Type M modeling / forensics)
- [ ] Verify script passes on approved ground truth JSON

---

## Scoring intent (Type M)

| Layer | Weight | What passes |
|-------|--------|-------------|
| L1 | 50% | Correct revenues, WAE rates, computed CC % |
| L2 | 30% | Assumption log + MD&A reconciliation cited |
| L3 | 20% | Table-level citations auditable |

Partial credit: correct MD&A extract but no Python → fail L1 methodology gate even if numbers match.

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

---

## Sign-off

**Approve when:** checklist complete, numbers replaced with filing-verified values, verify script passes.

| Reviewer | Date | Status |
|----------|------|--------|
| Gaurav Goyal (CFA L3 candidate) | | pending |
