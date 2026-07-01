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

Compute constant-currency organic net revenue growth for **EMEA** and **LatAm Foods** using **weighted-average FX from Note 1** — not spot rates. Segment names come from the FY2025 10-K segment reporting table (not legacy Europe/AMESA labels).

### Calculation vs MD&A extract (required methodology)

**Both — in sequence, not either/or:**

| Step | Agent must | Scored as |
|------|------------|-----------|
| 1 | Extract reported net revenue (EMEA, LatAm Foods) FY2025 vs FY2024 from Note 1 segment table | L1 extraction |
| 2 | Extract **weighted-average** FX from Note 1 (not spot / year-end) | L1 + trap `spot_rate_method` |
| 3 | **Python:** compute organic CC growth from inputs (show work) | L1 — primary answer |
| 4 | Extract MD&A disclosed organic revenue growth % for EMEA and LatAm Foods | L2 cross-check |
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

### FY2025 numbers (USD millions — **filing draft; CFA confirm MD&A FX sign**)

| Segment | FY2024 | FY2025 | Reported growth | FX impact | Organic CC |
|---------|--------|--------|-----------------|-----------|------------|
| EMEA | 16,658 | 18,025 | 8.0% | 2.0% | **6.0%** |
| LatAm Foods | 10,568 | 10,549 | −0.2% | −4.7% | **4.5%** |

WAE EUR/USD: FY2024 **1.081**, FY2025 **1.024** *(confirm in Note 1)*

WAE EUR/USD: FY2024 **1.081**, FY2025 **1.024**

**Verification today:** SEC accession `0000077476-26-000007` — [PEP FY2025 10-K](https://www.sec.gov/Archives/edgar/data/77476/000007747626000007/pep-20251227.htm) (filed 2026-02-03). Full EDGAR text index (LATER-01) not required to sign off GT numbers.

---

## Gate B blocker — resolved via re-scope *(2026-07-01)*

**Was:** Task referenced Europe/AMESA — not in FY2025 10-K segment table.  
**Now:** Re-scoped to **EMEA + LatAm Foods** per Note 1. L1 verify uses `verification_schema` in GT JSON + archetype script `verify_fx_organic_growth.py` (no hardcoded segment names in Python).

**CFA still required:** Confirm MD&A organic % and FX sign convention; confirm WAE EUR/USD in Note 1.

---

## Edge-case tolerance (additive vs multiplicative)

**Problem:** A strict model may compute Europe CC as **10.6%** (multiplicative) vs **10.0%** (additive MD&A decomposition). Zero-tolerance or point-equality checks create false negatives on valid math.

**Policy (encoded in GT `verification_policy`):**

| Band | Tolerance | Pass rule |
|------|-----------|-----------|
| **Strict (L1 pass)** | ±0.2 pp vs MD&A anchor | Canonical additive: `organic_cc = reported_growth − fx_impact` |
| **Alternative formula** | ±0.75 pp vs anchor | Multiplicative: `(1+g)/(1+fx)−1`; flags `METHOD_ALT`, partial L1 if inputs + MD&A cited |
| **WAE rebuild** | ±0.5 pp vs anchor | CC revenue at prior-year WAE; strict pass if WAE + revenues correct |
| **Hard fail** | — | `reported_only`, spot rates, wrong region/period — regardless of tolerance |

**Europe example:** anchor **10.0%** → strict pass [9.8, 10.2]; multiplicative 10.6% → within alternative band, not auto-fail if agent shows work + cites MD&A 10.0% reconciliation.

**Verify script:** Archetype `verify_fx_organic_growth.py` reads `verification_schema` + GT JSON — segment slugs are data, not code.

---

## Reviewer workflow (JSON-only)

**Separation of concerns:** CFA updates **ground truth JSON only** — never Python.

| Step | Owner | Action |
|------|-------|--------|
| 1 | CFA | Open PEP 10-K URL from `corpus_manifest_v1.json` |
| 2 | CFA | Edit `extracted_values` + `computed_values` in GT JSON; set `verification_policy.data_finality.verified_against_filing: true` |
| 3 | Eng or CFA | Run `python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py` (self-test against JSON) |
| 4 | CFA | Complete checklist; set `review_status` → `expert_reviewed` in GT JSON |

No verify-script edits required when numbers change.

---

## Sign-off sequencing (CFA vs Engineering)

Two independent gates — **do not block data sign-off on METHOD_ALT eng work**:

| Gate | Owner | Blocks | When |
|------|-------|--------|------|
| **A — Methodology** | CFA | Nothing downstream | Approve tolerance policy + task design in this doc (can happen now) |
| **B — Data finality** | CFA | `expert_reviewed` | Filing-verified numbers in GT JSON + verify self-test passes |
| **C — Publish** | Eng + CFA | `published` / external demo | Gate B complete; JSON-driven verify with `METHOD_ALT` support |

**Policy:** CFA signs off **data (Gate B)** as soon as JSON is filing-verified and self-test passes. **Do not wait** for Gate C to approve numbers.

**Gate C (standing rule):** Engineering confirms verify infrastructure is publish-ready before any external demo or `published` status.

**Gate C status (eng):** Met as of 2026-07-01 — verify script reads GT JSON and emits `METHOD_ALT`.

Until Gate B: keep `review_status` as `pending_expert_review` in this doc and GT JSON.

---

## Data finality (reviewer action)

**These figures are NOT filing-verified yet.** [Certain]

The table above is **eng-authored placeholder** until checked against the live SEC filing (see **FY2025 numbers** section). You **cannot** complete Gate B until:

1. Open PEP 10-K URL from `benchmark_v0.1/corpus/corpus_manifest_v1.json`
2. Verify Note 1 revenues, WAE table, MD&A Europe/AMESA organic %
3. **Update GT JSON only** with verified values (see Reviewer workflow above)
4. Re-run `verify_pep_fx_organic_growth.py` — must report `all_pass: true`
5. Complete checklist and set `review_status` → `expert_reviewed`

Until step 5: keep `review_status` as `pending_expert_review`; do not set `published`.

---

## Expert checklist (P2-02)

**How to use:** Section **I** and **II** (data rows) are **Gate B** — filing-verified before sign-off. Section **II** (design rows) and **III** are **Gate A / task design** — confirm scoring intent; can approve before filing numbers are final. Items marked *(agent runtime)* are encoded in prompt/grader/verify — you validate design, not individual agent runs.

### I. Source integrity & data *(Gate B — you verify against 10-K)*

- [ ] **10-K anchoring:** All FY2025/FY2024 revenue figures in GT JSON match Note 1 exactly (correct fiscal-year columns). *(See **FY2025 numbers** above; update `extracted_values` only.)*
- [ ] **Geographic scope:** EMEA and LatAm Foods match Note 1 segment reporting table — not PFNA, PBNA, or Asia Pacific.
- [ ] **WAE rate integrity:** Weighted-average EUR/USD in GT JSON match Note 1 FX table — not spot or year-end rates.
- [ ] **MD&A organic CC (your manual calc):** You compute CC from filing inputs; result matches MD&A disclosed EMEA/LatAm organic % *and* GT JSON `computed_values`.

### II. Methodology & logic *(Gate A — task design; Gate B — traps after data locked)*

- [ ] **Agent scoring intent *(task design)*:** Prompt requires independent Python computation **and** MD&A cross-check — MD&A extract alone is an auto-fail (L1 methodology gate).
- [ ] **Trap design *(task design)*:** `spot_rate_method`, `reported_only`, `wrong_region`, and `wrong_period` signatures are fair and documented in GT JSON `failure_modes`.
- [ ] **Trap wiring *(eng — spot-check)*:** Verify script classifies spot/year-end WAE and reported-only CC as hard fails; you do not review Python source — run a self-test only.
- [ ] **Tolerance policy *(task design)*:** `verification_policy` bands in GT JSON match the Edge-case tolerance section (±0.2 pp strict, ±0.75 pp alternative / `METHOD_ALT`).

### III. Auditability & traceability *(task design — agent runtime)*

- [ ] **Assumption log *(agent runtime, L2)*:** Grader brief requires agents to list (a) WAE rates used, (b) reported revenue base, (c) FX impact derivation.
- [ ] **MD&A reconciliation *(agent runtime, L2)*:** Agent’s computed organic CC must reconcile to MD&A disclosed % within ±0.2 pp strict or ±0.75 pp alternative band with citation.
- [ ] **Type M scope *(task design)*:** No investment recommendation required — modeling / forensics only.
- [ ] **Script validation *(Gate B)*:** `verify_pep_fx_organic_growth.py` reports `all_pass: true` on approved GT JSON *(run command below; no code review)*.

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

**CFA approve when (Gate B only):** Checklist complete, filing-verified GT JSON updated, and verify self-test reports `all_pass: true` (run command above — no Python code review required).

**Gate C (eng — not your action):** Already met as of 2026-07-01. Engineering owns verify infrastructure; you do not re-verify the script before signing off data.

**Before `published`:** Both Gate B (your sign-off) and Gate C (eng confirmation) must be complete. Eng marks publish after your Gate B is done.

| Reviewer | Date | Status |
|----------|------|--------|
| Gaurav Goyal (CFA L3 candidate) | | pending |
