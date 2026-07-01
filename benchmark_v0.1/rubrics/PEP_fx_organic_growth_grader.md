# Grader Brief — PEP FX Organic Growth (Type M)

**Task ID:** `PEP_fx_organic_growth`  
**Archetype:** `fx_organic_growth`  
**Status:** Expert-reviewed — see `docs/expert_drafts/PEP_FX_GT_REVIEW.md`  
**Canonical prompt:** `benchmark_v0.1/tasks/PEP_fx_organic_growth.json` → `prompt.text`  
**Ground truth:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Verify script:** `benchmark_v0.1/scripts/verify_fx_organic_growth.py` (PEP entry: `verify_pep_fx_organic_growth.py`)  
**Schema:** `benchmark_v0.1/schemas/fx_organic_growth_verification_v1.json`

---

## Agent prompt (summary)

Using PepsiCo FY2025 Form 10-K (filed 2026-02-03), compute constant-currency organic net revenue growth for **EMEA** and **LatAm Foods** vs FY2024. Extract segment revenues from Note 1; extract reported %, FX translation impact %, and organic % from MD&A **Net Revenue and Organic Revenue Performance**; Python-verify additive identity `organic ≈ reported − fx`. The filing does **not** publish weighted-average FX rate tables — do not invent or import external rates. No investment recommendation.

---

## Scoring intent (weights)

Weights from `tasks/PEP_fx_organic_growth.json` → `scoring.task_type_weights` (**do not reweight** without task JSON change):

| Layer | Weight | Focus |
|-------|--------|--------|
| **L1 — Data fidelity** | **50%** | Note 1 revenues + MD&A % extraction + additive CC math |
| **L2 — Forensic rigor** | **30%** | Python verification, assumption log, MD&A reconcile, section recall |
| **L3 — Traceability** | **20%** | Table-level citations (≥90%), no external FX, no reco veto |

Full pass rules, partial credit, L3 material-claim inventory: **`docs/expert_drafts/PEP_FX_GT_REVIEW.md` → Scoring intent (Type M)**.

Report **layer sub-scores**, not a single pass/fail.

---

## Pass / fail calibration

| Scenario | Result |
|----------|--------|
| Note 1 revenues + MD&A anchors correct; additive formula accurate | **Pass L1/L2** |
| Correct MD&A extract; **no Python** additive verification shown | **L1 methodology fail** |
| EMEA reported cited as **8.2%** (revenue-implied) but FX decomp uses **8.0%** MD&A anchor | **Pass L1/L2** if reconcile explained |
| EMEA **8.2%** used for FX decomposition (FX = 2.2 vs MD&A 2.0) | **L1/L2 partial** — breaks strict additive identity |
| States filing has **no WAE table**; does not import external rates | **Pass L3** |
| Invented WAE or cites Bloomberg / spot rates despite absent disclosure | **L3 fail** (`invent_wae_rates_not_in_filing`) |
| Organic CC = reported growth (EMEA 8.0% / LatAm −0.2%) | **L1 hard fail** (`reported_only` / `CC_OMIT`) |
| **7/10** material claims table-cited (**70%**) | **L3 fail** (`L3_CITATION_INCOMPLETE`; 90% bar) |
| Buy/Hold/Sell or price target | **L3 veto** |

---

## Material claims inventory (L3 denominator)

| Bucket | Count | Source |
|--------|-------|--------|
| Revenues | **4** | EMEA / LatAm Foods FY2025 + FY2024 (Note 1 — *Net revenue by segment*) |
| MD&A anchors | **6** | Per segment: reported %, FX translation %, organic CC % (MD&A organic performance table) |
| Context *(conditional)* | **1** | “Filing does not disclose WAE rate table” — if agent searched for rates |

Derived values (FX = reported − organic, Python check) need no extra filing cite if inputs are cited.

---

## Automation boundary

| Automated (verify script + scoring engine) | Human / grader |
|--------------------------------------------|----------------|
| L1 numeric compare vs GT JSON | Assumption log quality |
| Additive formula self-check | Python artifact present (Type M gate) |
| Trap signatures (`reported_only`, `wrong_region`, `wrong_period`) | Citation snippet audit (L3) |
| `METHOD_ALT` / tolerance bands | WAE absence honesty (L2/L3) |
| Citation auditor: claim count vs 90% threshold | MD&A row / column spot-check |

Self-test (no agent file): `verify_pep_fx_organic_growth.py` → `all_pass: true`. Trap classification requires `--agent-output`.

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

**Not in filing:** Weighted-average FX rate table. Task re-scoped 2026-07-01 to MD&A additive decomposition.

---

## FY2025 numbers (USD millions — Gate B verified 2026-07-01)

| Segment | FY2024 | FY2025 | Reported | FX impact | Organic CC |
|---------|--------|--------|----------|-----------|------------|
| EMEA | 16,658 | 18,025 | 8.0% (MD&A; revenue-implied 8.2%) | 2.0% | **6.0%** |
| LatAm Foods | 10,568 | 10,549 | −0.2% | −4.7% | **4.5%** |

**Reported % convention:** GT anchors **8.0%** for FX decomposition (8.0 − 6.0 = 2.0). Revenue-implied **8.2%** acceptable for L1 reported cite within ±0.2 pp — not for FX math.

---

## Verify command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/verify_fx_organic_growth.py --ground-truth benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json --agent-output agent.json
```
