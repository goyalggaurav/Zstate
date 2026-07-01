# Grader Brief — PEP FX Organic Growth

**Task ID:** `PEP_fx_organic_growth` (Type M)  
**Archetype:** `fx_organic_growth`  
**Status:** Draft — pending expert sign-off  
**Canonical prompt:** `benchmark_v0.1/tasks/PEP_fx_organic_growth.json` → `prompt.text`  
**Ground truth:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Verify script:** `benchmark_v0.1/scripts/verify_fx_organic_growth.py` (PEP entry: `verify_pep_fx_organic_growth.py`)  
**Schema:** `benchmark_v0.1/schemas/fx_organic_growth_verification_v1.json`  
**CFA review:** `docs/expert_drafts/PEP_FX_GT_REVIEW.md`

---

## Agent prompt (summary)

Using PepsiCo FY2025 Form 10-K (filed 2026-02-03), compute constant-currency organic net revenue growth for **EMEA** and **LatAm Foods** vs FY2024. Extract segment revenues from Note 1; extract reported %, FX translation impact %, and organic % from MD&A **Net Revenue and Organic Revenue Performance**; Python-verify additive identity `organic ≈ reported − fx`. The filing does **not** publish weighted-average FX rate tables — do not invent or import external rates. No investment recommendation.

---

## Scoring layers (Type M weights)

| Layer | Weight | What it measures |
|-------|--------|------------------|
| **L1** | 50% | Revenue extraction + MD&A CC decomposition math |
| **L2** | 30% | Assumption log + MD&A cross-check + section recall |
| **L3** | 20% | Citation quality (table-level, auditable) |

Full scoring intent (pass rules, partial credit, automation boundary): **`docs/expert_drafts/PEP_FX_GT_REVIEW.md` → Scoring intent (Type M)**.

Report **layer sub-scores**, not a single pass/fail.

---

## Failure modes (primary traps)

| ID | Label | Wrong output signature | Fracture code |
|----|-------|------------------------|---------------|
| `reported_only` | Reported growth only | EMEA CC = 8.0% or LatAm CC = −0.2% (reported, not organic) | `CC_OMIT` |
| `wrong_region` | Wrong segment | PFNA / PBNA / Asia Pacific substituted for scored segments | `SCOPE_ERR` |
| `wrong_period` | Wrong fiscal year | FY2024 10-K as primary or quarterly slice | `HALLUC_FILL` |

---

## Source anchors (human reviewer)

| Metric | Section | Column |
|--------|---------|--------|
| EMEA / LatAm Foods net revenue | Note 1 — Segment Reporting | FY2025 vs FY2024 |
| Reported growth / FX translation / organic % | MD&A — Net Revenue and Organic Revenue Performance | EMEA, LatAm Foods |

**Not in filing:** Weighted-average EUR/USD (or any currency-pair rate table). Task re-scoped 2026-07-01 to MD&A additive decomposition.

---

## FY2025 numbers (USD millions — Gate B verified 2026-07-01)

| Segment | FY2024 | FY2025 | Reported | FX impact | Organic CC |
|---------|--------|--------|----------|-----------|------------|
| EMEA | 16,658 | 18,025 | 8.0% (MD&A; revenue-implied 8.2%) | 2.0% | **6.0%** |
| LatAm Foods | 10,568 | 10,549 | −0.2% | −4.7% | **4.5%** |

**Reported % convention:** MD&A table uses whole percentage points; revenue-implied EMEA growth is 8.2%. GT anchors 8.0% for additive FX decomposition (8.0 − 6.0 = 2.0). Agents may cite either within ±0.2 pp.

**CFA action remaining:** Complete checklist → set `review_status: expert_reviewed` in GT JSON.

---

## Verify command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/verify_fx_organic_growth.py --ground-truth benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json
```
