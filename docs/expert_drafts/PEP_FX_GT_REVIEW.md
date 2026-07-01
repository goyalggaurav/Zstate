# Expert Review — PEP FX Organic Growth Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json`  
**Task:** `PEP_fx_organic_growth` (Type M)  
**Backlog ref:** P2-02 *(eng tracking only — not a lifecycle status)*  
**Scored period:** FY2025 (10-K filed 2026-02-03)  
**Status:** `expert_reviewed`  
**Eng draft date:** 2026-07-01  
**Expert review date:** 2026-07-01

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

**Gate B complete (2026-07-01).** Expert audit ledger §2 signed off; `review_status: expert_reviewed` in GT JSON.

**Eng follow-up for `published`:** Done 2026-07-01 — `manifest.json` PEP `status: published`; `published_tasks: 2`.

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

- [x] **Revenue (Note 1):** EMEA and LatAm Foods FY2025/FY2024 net revenue match Note 1 segment table exactly.
- [x] **MD&A % (organic table):** Reported growth, FX translation impact, and organic CC match MD&A *Net Revenue and Organic Revenue Performance* for both segments.
- [x] **Additive identity:** `reported − fx = organic` holds for EMEA and LatAm Foods.
- [x] **Reported % convention:** MD&A whole-percentage anchor (e.g. EMEA **8.0%**) vs revenue-implied (e.g. **8.2%**) — revenue-implied acceptable within ±0.2 pp for L1 reported %; **FX decomposition must use MD&A table reported %**, not revenue-implied.
- [x] **Geographic scope:** Scored segments are EMEA + LatAm Foods only — not PFNA, PBNA, or Asia Pacific.
- [x] **WAE absence:** Confirm filing has no WAE rate table; GT contains no placeholder rates.

### II. Trap & methodology audit *(Gate A design; Gate B after data locked)*

- [x] **Trap signatures:** `reported_only`, `wrong_region`, `wrong_period` documented in GT `failure_modes`.
- [x] **Formula integrity:** Additive formula matches GT `verification_policy`; FX impact matches MD&A translation column and reconciles as `reported − organic`.
- [x] **Tolerance policy:** ±0.2 pp strict (L1 pass); ±0.75 pp multiplicative alternative → `METHOD_ALT` (partial credit).
- [x] **Trap wiring *(eng spot-check)*:** Self-test validates GT JSON only; trap classification (`reported_only`, etc.) applies at agent eval time.
- [x] **Script self-test:** `verify_pep_fx_organic_growth.py` reports `all_pass: true` on approved GT JSON.

### III. Auditability & traceability *(agent runtime — design check)*

- [x] **Assumption log:** Grader requires agent list: (a) Note 1 revenue citations, (b) MD&A reported/FX/organic % citations, (c) additive derivation shown.
- [x] **WAE handling:** If agent searches for FX rates, must state filing does not disclose them — no external/invented rates.
- [x] **L2 reconcile:** Agent organic CC within ±0.2 pp strict (or ±0.75 pp with `METHOD_ALT` if multiplicative shown + MD&A cited).
- [x] **L3 citation design:** Material-claim inventory (10–11 claims) and citation schema match **Scoring intent → Layer 3**; ≥90% table-level cite bar documented.
- [x] **Type M scope:** No Buy/Hold/Sell or price target.

---

## Scoring intent (Type M)

**Weights:** L1 **50%** · L2 **30%** · L3 **20%** (from `tasks/PEP_fx_organic_growth.json` → `scoring.task_type_weights`).

Report **layer sub-scores**, not a single pass/fail. A `reported_only` trap hit zeroes organic CC on L1 but can still earn partial L2 if Note 1 + MD&A were accessed and cited.

### Layer 1 — Technical & tabular accuracy *(automated + hard gates)*

**Verify script** (`verify_pep_fx_organic_growth.py` with `--agent-output`) scores structured fields against GT JSON:

| Check class | Metrics | Tolerance | Critical |
|-------------|---------|-----------|----------|
| Segment revenue | `emea_net_revenue_fy2024/2025`, `latam_foods_net_revenue_fy2024/2025` | Exact (USD M) | No |
| MD&A % extraction | `*_reported_growth_pct`, `*_fx_impact_pct`, `*_organic_cc_growth_pct` | ±0.1–0.2 pp | Organic **yes** |
| Additive identity | `*_cc_formula_pct` (= reported − fx) | ±0.2 pp vs organic anchor | No |

**Pass semantics:**

| Script field | Meaning |
|--------------|---------|
| `all_pass: true` | Every metric within **strict** tolerance |
| `l1_pass: true` | Strict pass **or** organic CC within `acceptable_range_pp` → flags `METHOD_ALT` |
| `critical_fail: true` | Any critical metric (organic CC) failed strict **and** alternative band |

**Hard fails (L1 cap / fracture):** `reported_only` (`CC_OMIT`), `wrong_region` (`SCOPE_ERR`), `wrong_period` (`HALLUC_FILL`) — see GT `failure_modes` and `hard_fail`.

**Type M methodology gate *(not in verify script — grader / expert rule)*:** Agent must show Python verification of additive identity. Correct MD&A % copy with **no Python** → **L1 fail** even if numbers match.

**Reported % edge case:** EMEA revenue-implied **8.2%** vs MD&A table **8.0%** — L1 reported % may pass within ±0.2 pp; **FX decomposition and organic CC must anchor on MD&A table reported %** (see §1 Scope).

### Layer 2 — Domain reasoning *(mostly automated on calibration)*

| Signal | Pass | Fail / penalty |
|--------|------|----------------|
| **Section recall** | Note 1 segment table + MD&A organic performance accessed (gold path `minimal_section_set`) | Wrong note or segment table skipped |
| **Assumption log** | (a) Note 1 revenue cites, (b) MD&A reported/FX/organic cites, (c) additive derivation shown | Missing derivation or uncited % |
| **WAE handling** | States filing has no WAE table if agent searched for rates | External, spot, or invented EUR/USD rates |
| **MD&A reconcile** | Computed organic within ±0.2 pp strict of MD&A anchor | Organic off anchor with no cited reconciliation |

`layer2_method: assumption_log_automated` in task JSON — expert spot-check on calibration set only at MVD scale.

### Layer 3 — Traceability & trust *(20% weight)*

**Scope for this task:** `compliance_baseline: citation_only` — FINRA linter **not** required (`finra_required: false`). L3 is **source grounding + uncertainty honesty**, not investment compliance.

**Pilot aggregation:** On 3-run calibration, L3 uses **worst run wins** for citation completeness (framework default).

#### Material claims inventory

Every row below is a **material claim** — each needs a table-level citation in the growth table or assumption log:

| # | Claim | Required cite anchor |
|---|-------|----------------------|
| 1–4 | EMEA / LatAm Foods net revenue (FY2025 + FY2024) | Note 1 — *Net revenue by segment*; correct fiscal-year **column** |
| 5–10 | Per segment: reported growth %, FX translation %, organic CC % | MD&A — *Net Revenue and Organic Revenue Performance*; **segment row** |
| 11 *(conditional)* | “Filing does not disclose WAE rate table” | Negative search OK — must name sections checked; no external FX source |

**Derived values** (e.g. FX = reported − organic, Python check) do **not** need a separate filing line if all inputs are cited and derivation is shown.

**L3 denominator:** Count material claims present in the agent output (typically **10**; **11** if WAE search is discussed). Do not penalize for omitting uncited optional commentary.

#### Citation schema (pass bar)

Gold shape matches GT `extracted_values[].citation`:

```json
{
  "doc_id": "PEP_10K_2025",
  "note": "Note 1 — Segment Reporting",
  "table_title": "Net revenue by segment",
  "column": "Year ended December 27, 2025",
  "snippet": "EMEA $ 18,025"
}
```

| Field | Pass | Fail |
|-------|------|------|
| `doc_id` | `PEP_10K_2025` (scored filing) | `PEP_10K_2024` as primary; external URL; “PepsiCo 10-K” only |
| `note` / section | Note 1 or MD&A subsection name | “Item 8” with no table; wrong note for metric type |
| `table_title` | Named table (e.g. *Net revenue by segment*) | “segment data” / “financial statements” |
| `column` | Fiscal period column (Dec 27 2025 vs Dec 28 2024) | Missing column; wrong year in cite |
| `snippet` | Short verbatim or numeric anchor | Paraphrase with no locatable string |

**Completeness rule:** ≥**90%** of material claims fully cited → L3 pass. Below 90% → `L3_CITATION_INCOMPLETE` (pilot veto on L3 sub-score, not necessarily whole task unless campaign config says so).

#### Trust signals beyond citations

| Signal | Pass | Fail / penalty |
|--------|------|----------------|
| **Source scope** | Scored doc only: PEP FY2025 10-K (`PEP_10K_2025`) | Primary cite from `PEP_10K_2024`, 10-Q, or web FX feed |
| **Section–metric match** | Revenues from Note 1; % from MD&A organic table | Organic % cited to Note 1; revenue cited to MD&A narrative only |
| **Uncertainty** | “Unverified” / “not disclosed” when absent; no interpolation | Invented WAE (`invent_wae_rates_not_in_filing`); filled gaps |
| **Sign / label honesty** | FX impact labeled as MD&A *translation*; organic ≠ reported | Calls reported growth “organic CC” without FX adjustment |
| **Task-type compliance** | No Buy/Hold/Sell or price target | `produce_buy_hold_sell_recommendation` → **L3 veto** |

#### L3 anti-patterns (gold path)

| Anti-pattern | L3 effect |
|--------------|-----------|
| `invent_wae_rates_not_in_filing` | Trust fail — fabricated or external FX |
| `produce_buy_hold_sell_recommendation` | Veto |
| `use_fy2024_10k_as_primary` | Wrong doc_id in cites → completeness fail |
| `use_quarterly_10q_instead_of_fy2025_10k` | Wrong period in cites |

#### L2 vs L3 boundary

| Concern | Layer |
|---------|-------|
| Assumption log lists (a)(b)(c) derivation steps | L2 |
| Each listed input has auditable `{doc, note, table, column}` | L3 |
| MD&A accessed (section recall) | L2 |
| MD&A cite includes segment row + correct % column | L3 |
| Python shown | L2 (Type M methodology) |
| Python I/O traceable to cited inputs | L3 |

#### Illustrative citation quality

| Quality | Example |
|---------|---------|
| **Pass** | “EMEA FY2025 revenue $18,025M — PEP 10-K Note 1, Net revenue by segment, column Year ended Dec 27 2025, snippet: ‘EMEA $ 18,025’.” |
| **Pass** | “EMEA organic CC 6.0% — MD&A Net Revenue and Organic Revenue Performance, EMEA row, organic % column FY2025 vs FY2024.” |
| **Fail** | “EMEA revenue from PepsiCo 10-K segment footnote.” *(no note, table, or column)* |
| **Fail** | “Organic growth 6% per MD&A.” *(no table name or segment row)* |
| **Fail** | “EUR/USD 1.024 (Bloomberg).” *(external FX — not in filing)* |

#### Automation boundary (L3)

| Automated (scoring engine / citation auditor) | Expert calibration |
|-------------------------------------------------|-------------------|
| Claim count vs fully-cited count | Snippet plausibility spot-check |
| `doc_id` / period mismatch heuristics | MD&A row correctly identified |
| FINRA skip on this task | WAE absence statement adequacy |
| Anti-pattern tags from trajectory | Borderline “Item 7” cites |

L1 verify script does **not** score citations — L3 requires separate citation audit on agent narrative output.

### Partial credit examples

| Agent behavior | Typical outcome |
|----------------|-----------------|
| Note 1 revenues correct; organic CC = reported (trap) | L1 **~0%** on CC metrics; partial L2 if sections cited |
| All % correct; multiplicative formula; MD&A cited | L1 **`METHOD_ALT`** partial via ±0.75 pp band; not `all_pass` |
| Correct table extract; no Python work shown | L1 **methodology fail**; L2/L3 may still score |
| Both segments correct; one wrong fiscal column | L1 partial; possible `wrong_period` fracture |
| All numbers correct; 7/10 material claims table-cited | L1 pass; L3 **fail** (`L3_CITATION_INCOMPLETE` at 70%) |

### Automation boundary

| Automated (L1 script) | Expert / grader (L2–L3) |
|-----------------------|-------------------------|
| Numeric compare vs GT JSON | Assumption log quality |
| `reported_only` / `wrong_region` classification | Python artifact present |
| `METHOD_ALT` flag on organic CC | Citation snippet audit (L3) |
| Additive formula self-check | WAE absence acknowledgment (L2/L3) |
| — | Citation auditor: claim count vs 90% threshold (L3) |

**Calibration command:**

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py --ground-truth benchmark_v0.1/ground_truth/PEP_fx_organic_growth_gt.json --agent-output agent.json
```

Expected on approved GT (self-test, no agent file): `all_pass: true`, `failure_modes: []`.

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

---

## Sign-off

**Gate B (CFA):** Complete 2026-07-01 — audit ledger §2 checked against PEP FY2025 10-K; verify self-test `all_pass: true`.

**Gate C (eng):** Complete 2026-07-01 — PEP published in `benchmark_v0.1/manifest.json`; preflight verify + corpus validation passed.

| Reviewer | Date | Status |
|----------|------|--------|
| Gaurav Goyal (CFA L3 candidate) | 2026-07-01 | **expert_reviewed** |

### Expert verdict

**Verdict:** approve (Gate B)

- **Note 1 revenues:** EMEA / LatAm Foods FY2025/FY2024 match segment table.
- **MD&A anchors:** Reported %, FX translation, organic CC match *Net Revenue and Organic Revenue Performance*; additive identity holds.
- **WAE re-scope:** No rate table in filing; GT and task correctly anchored on MD&A decomposition only.
- **Trap / tolerance design:** `reported_only`, `wrong_region`, `wrong_period` fair; ±0.2 pp strict / ±0.75 pp `METHOD_ALT` documented.
- **Verify self-test:** `all_pass: true` (12 checks).
