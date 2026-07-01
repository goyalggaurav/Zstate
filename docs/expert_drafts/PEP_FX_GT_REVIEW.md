# Expert Review — PEP FX Organic Growth Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Task:** `PEP_fx_organic_growth` (Type M)  
**Backlog ref:** P2-02 *(eng tracking only — not a lifecycle status)*  
**Scored period:** FY2025 (10-K filed 2026-02-03)  
**Status:** `pending_expert_review`  
**Eng draft date:** 2026-07-01  
**Expert review date:** _pending_

---

## Eng summary

Compute constant-currency organic net revenue growth for **EMEA** and **LatAm Foods** using **MD&A additive decomposition** — not WAE rebuild. The FY2025 10-K does **not** publish weighted-average EUR/USD (or any currency-pair rate table). Segment names come from the FY2025 10-K segment reporting table (not legacy Europe/AMESA labels).

### Calculation vs MD&A extract (required methodology)

**Both — in sequence, not either/or:**

| Step | Agent must | Scored as |
|------|------------|-----------|
| 1 | Extract reported net revenue (EMEA, LatAm Foods) FY2025 vs FY2024 from Note 1 segment table | L1 extraction |
| 2 | Extract MD&A **reported %**, **foreign exchange translation impact %**, and **organic %** for each segment | L1 extraction |
| 3 | **Python:** verify `organic_cc ≈ reported_growth − fx_impact` for each segment | L1 — primary answer |
| 4 | Reconcile to MD&A disclosed organic % within tolerance; cite both in assumption log | L2 pass |
| 5 | If agent searches for WAE rates: state filing does not disclose them — do not invent or import external rates | L2 auditability |

**Do not** allow MD&A copy-only as the sole answer — that bypasses Type M modeling and fails the Python requirement. **Do not** accept reported GAAP growth as organic CC (e.g. EMEA 8% / LatAm −0.2%) — trap `reported_only`.

Canonical formula (encoded in GT `verification_policy`):

`organic_cc = reported_growth − fx_impact` (additive percentage points; FX impact signed per MD&A).

### Traps

| Trap | Wrong behavior |
|------|----------------|
| `reported_only` | EMEA CC = 8.0% or LatAm CC = −0.2% (reported, not organic) |
| `wrong_region` | PFNA / PBNA / Asia Pacific substituted for EMEA / LatAm Foods |
| `wrong_period` | Wrong fiscal year column |

**Retired (2026-07-01):** `spot_rate_method` — filing has no WAE table to extract; trap was based on eng placeholders.

### FY2025 numbers (USD millions — **Gate B verified 2026-07-01**)

| Segment | FY2024 | FY2025 | Reported growth | FX impact | Organic CC |
|---------|--------|--------|-----------------|-----------|------------|
| EMEA | 16,658 | 18,025 | 8.0% *(MD&A; revenue-implied 8.2%)* | 2.0% | **6.0%** |
| LatAm Foods | 10,568 | 10,549 | −0.2% | −4.7% | **4.5%** |

**Verification today:** SEC accession `0000077476-26-000007` — [PEP FY2025 10-K](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm) (filed 2026-02-03). Full EDGAR text index (LATER-01) not required to sign off GT numbers.

---

## Data finality report (Gate B) — verified 2026-07-01

### EMEA

| Field | Value | Source |
|-------|-------|--------|
| Net revenue FY2025 / FY2024 | $18,025M / $16,658M | Note 1 — Segment Reporting |
| Revenue-implied reported growth | (18025÷16658 − 1) ≈ **8.2%** | Python / Note 1 dollars |
| **GT anchor — reported growth** | **8.0%** | MD&A organic revenue table (whole %) |
| MD&A organic growth | **6.0%** | MD&A — Net Revenue and Organic Revenue Performance |
| FX impact (additive) | 8.0% − 6.0% = **2.0%** | Derived per canonical formula |

### LatAm Foods

| Field | Value | Source |
|-------|-------|--------|
| Net revenue FY2025 / FY2024 | $10,549M / $10,568M | Note 1 — Segment Reporting |
| Reported growth | **−0.2%** | Revenue-implied ≈ MD&A |
| MD&A organic growth | **4.5%** | MD&A organic revenue table |
| FX impact (additive) | −0.2% − 4.5% = **−4.7%** | Derived per canonical formula |

### Why EMEA reported is 8.0% not 8.2%

PepsiCo’s MD&A **Net Revenue and Organic Revenue Performance** table publishes **rounded whole percentage points** (EMEA row: **8%**, not 8.2%). The segment narrative also states revenue increased **8%**. Dollar math from Note 1 yields **8.2%** — the ~0.2 pp gap is normal rounding at the segment level.

**Benchmark rule:**

| Use case | Anchor |
|----------|--------|
| L1 revenue extraction | Note 1 dollars (exact) |
| L1 reported % | MD&A table **or** revenue-implied within **±0.2 pp** |
| FX decomposition + L2 MD&A reconcile | **MD&A table reported (8.0%)** + MD&A organic (6.0%) → FX = 2.0% |

Storing 8.2% as reported would break the additive identity against MD&A organic (8.2 − 6.0 = 2.2 ≠ table FX). Anchoring **8.0%** keeps `reported − fx = organic` consistent with how the filing presents the decomposition.

### WAE re-scope (2026-07-01)

Full-text search of PEP FY2025 and FY2024 10-K HTML confirms **no** table titled “Weighted-average exchange rates” and **no** disclosed EUR/USD pair. Prior GT placeholders (1.024 / 1.081) removed. Task now grades MD&A decomposition only; `fx_instruments` in `verification_schema` is empty.

---

## Gate B blocker — resolved *(2026-07-01)*

| Issue | Resolution |
|-------|------------|
| Europe/AMESA not in FY2025 segment table | Re-scoped to **EMEA + LatAm Foods** |
| WAE EUR/USD not in filing | Re-scoped to **MD&A additive path**; WAE metrics removed from GT |

**Gate B status:** Complete — revenues + MD&A organic/FX verified against filing.

---

## Edge-case tolerance (additive vs multiplicative)

**Problem:** A strict model may compute CC via multiplicative formula vs additive MD&A decomposition. Zero-tolerance checks create false negatives on valid math.

**Policy (encoded in GT `verification_policy`):**

| Band | Tolerance | Pass rule |
|------|-----------|-----------|
| **Strict (L1 pass)** | ±0.2 pp vs MD&A anchor | Canonical additive: `organic_cc = reported_growth − fx_impact` |
| **Alternative formula** | ±0.75 pp vs anchor | Multiplicative: `(1+g)/(1+fx)−1`; flags `METHOD_ALT`, partial L1 if inputs + MD&A cited |
| **Hard fail** | — | `reported_only`, wrong region/period — regardless of tolerance |

**Verify script:** Archetype `verify_fx_organic_growth.py` reads `verification_schema` + GT JSON — segment slugs are data, not code.

---

## Reviewer workflow (JSON-only)

**Separation of concerns:** CFA updates **ground truth JSON only** — never Python.

| Step | Owner | Action |
|------|-------|--------|
| 1 | CFA | Open PEP 10-K URL from `corpus_manifest_v1.json` |
| 2 | CFA | Confirm GT JSON matches filing; set `verification_policy.data_finality.verified_against_filing: true` |
| 3 | Eng or CFA | Run `python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py` (self-test against JSON) |
| 4 | CFA | Complete checklist; set `review_status` → `expert_reviewed` in GT JSON |

No verify-script edits required when numbers change.

---

## Sign-off sequencing (CFA vs Engineering)

Two independent gates — **do not block data sign-off on METHOD_ALT eng work**:

| Gate | Owner | Blocks | When |
|------|-------|--------|------|
| **A — Methodology** | CFA | Nothing downstream | Approve tolerance policy + task design in this doc |
| **B — Data finality** | CFA | `expert_reviewed` | Filing-verified numbers in GT JSON + verify self-test passes |
| **C — Publish** | Eng + CFA | `published` / external demo | Gate B complete; JSON-driven verify with `METHOD_ALT` support |

**Policy:** CFA signs off **data (Gate B)** as soon as JSON is filing-verified and self-test passes.

**Gate C status (eng):** Met as of 2026-07-01 — verify script reads GT JSON and emits `METHOD_ALT`.

---

## Data finality (reviewer action)

**Gate B complete 2026-07-01.** See **Data finality report** above.

**Before `expert_reviewed`:**

1. Complete checklist below
2. Re-run `verify_pep_fx_organic_growth.py` (should report `all_pass: true`)
3. Set `review_status` → `expert_reviewed` in GT JSON

---

## 1. Scope & logic

- **Segments:** EMEA + LatAm Foods (FY2025 Note 1 segment reporting table — not legacy Europe/AMESA).
- **Methodology:** Additive MD&A decomposition: `organic_cc = reported_growth − fx_impact` (percentage points; FX signed per MD&A).
- **Primary sources:** Note 1 (segment net revenue, USD millions) + MD&A *Net Revenue and Organic Revenue Performance* (reported %, FX translation %, organic %).
- **WAE:** Not in scope — filing discloses no weighted-average FX rate table; task anchored on MD&A only (`fx_instruments: []` in GT).
- **Type M gate:** Python verification required; MD&A extract alone is insufficient.

---

## 2. Expert audit ledger (Gate B — data finality)

*Verify against [PEP FY2025 10-K](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm) — SEC accession `0000077476-26-000007` (filed 2026-02-03).*

**How to use:** Section **I** = Gate B (filing data). Section **II** = Gate A/B (design + traps). Section **III** = agent-runtime scoring intent (validate design, not individual runs).

### I. Source & baseline audit *(Gate B)*

- [ ] **Revenue (Note 1):** EMEA and LatAm Foods FY2025/FY2024 net revenue match Note 1 segment table exactly.
- [ ] **MD&A % (organic table):** Reported growth, FX translation impact, and organic CC match MD&A *Net Revenue and Organic Revenue Performance* for both segments.
- [ ] **Additive identity:** `reported − fx = organic` holds for EMEA and LatAm Foods.
- [ ] **Reported % convention:** MD&A whole-percentage anchor (e.g. EMEA **8.0%**) vs revenue-implied (e.g. **8.2%**) — revenue-implied acceptable within ±0.2 pp for L1 reported %; **FX decomposition must use MD&A table reported %**, not revenue-implied.
- [ ] **Geographic scope:** Scored segments are EMEA + LatAm Foods only — not PFNA, PBNA, or Asia Pacific.
- [ ] **WAE absence:** Confirm filing has no WAE rate table; GT contains no placeholder rates.

### II. Trap & methodology audit *(Gate A design; Gate B after data locked)*

- [ ] **Trap signatures:** `reported_only`, `wrong_region`, `wrong_period` documented in GT `failure_modes`.
- [ ] **Formula integrity:** Additive formula matches GT `verification_policy`; FX impact matches MD&A translation column and reconciles as `reported − organic`.
- [ ] **Tolerance policy:** ±0.2 pp strict (L1 pass); ±0.75 pp multiplicative alternative → `METHOD_ALT` (partial credit).
- [ ] **Trap wiring *(eng spot-check)*:** Self-test validates GT JSON only; trap classification (`reported_only`, etc.) applies at agent eval time.
- [ ] **Script self-test:** `verify_pep_fx_organic_growth.py` reports `all_pass: true` on approved GT JSON.

### III. Auditability & traceability *(agent runtime — design check)*

- [ ] **Assumption log:** Grader requires agent list: (a) Note 1 revenue citations, (b) MD&A reported/FX/organic % citations, (c) additive derivation shown.
- [ ] **WAE handling:** If agent searches for FX rates, must state filing does not disclose them — no external/invented rates.
- [ ] **L2 reconcile:** Agent organic CC within ±0.2 pp strict (or ±0.75 pp with `METHOD_ALT` if multiplicative shown + MD&A cited).
- [ ] **Type M scope:** No Buy/Hold/Sell or price target.

---

## Scoring intent (Type M)

| Layer | Weight | What passes |
|-------|--------|-------------|
| L1 | 50% | Correct revenues, MD&A % extraction, computed CC % |
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

**CFA approve when (Gate B only):** Checklist complete, filing-verified GT JSON updated, and verify self-test reports `all_pass: true`.

**Gate C (eng — not your action):** Already met as of 2026-07-01.

**Before `published`:** Both Gate B (your sign-off) and Gate C (eng confirmation) must be complete.

| Reviewer | Date | Status |
|----------|------|--------|
| Gaurav Goyal (CFA L3 candidate) | | pending |
