# Expert Review — AMZN Footnote Reconciliation Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/AMZN_footnote_reconciliation_gt.json`  
**Task:** `AMZN_footnote_reconciliation` (Type F, archetype `F_exact`)  
**Backlog ref:** P2-03 / P2-12 / P2-16  
**Scored period:** FY2025 (10-K filed 2026-02-06)  
**Status:** `expert_reviewed` — **signed off**  
**Eng draft date:** 2026-07-01  
**Expert review date:** 2026-07-02  
**SBC correction + trap sign-off:** 2026-07-02 (Gate B: $19,467M; `SBC_ALLOCATION_ERR` verified)

---

## Eng summary

Reconcile FY2025 reportable **segment net sales** (North America, International, AWS) to **consolidated net sales** and extract International **reported vs FX-neutral** growth from MD&A. Five-section gold path (role slugs): `segment_policy` → `compensation_disclosure` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

Stock-based compensation expense (~$19,467M) is disclosed in **Note 8 — Stockholders' Equity**, not a standalone SBC note. SBC is **not allocated** to segment operating results — agents must retrieve `compensation_disclosure` before treating segment tables as all-in economics.

**SBC source (Gate B):** Amazon FY2025 Form 10-K, Note 8 — Stockholders' Equity, total stock-based compensation expense table: **$19,467M** for year ended December 31, 2025 ([SEC filing](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm)). Prior pilot bundle draft incorrectly used $22,411M (closer to FY2024's $22,011M); corrected 2026-07-02.

### FY2025 numbers (USD millions)

| Line | Value | Source (path role) |
|------|-------|-------------------|
| North America net sales | 426,305 | `segment_financials` — Note 10 FY2025 column |
| International net sales | 161,894 | Same |
| AWS net sales | 128,725 | Same |
| **Segment sum** | **716,924** | Python verify |
| Consolidated net sales | 716,924 | `consolidated_primary` |
| International reported growth | 13.0% | `narrative_fx` |
| International FX-neutral growth | 10.0% | `narrative_fx` |
| SBC expense (FY2025) | 19,467 | `compensation_disclosure` — context, not in segment sum |

**Reconciliation:** 426,305 + 161,894 + 128,725 = 716,924 (exact; no adjustment line — `F_exact` archetype).

### Traps

| Trap | Wrong behavior |
|------|----------------|
| `wrong_period` | FY2024 consolidated **637,959** or prior-year segment column via decoy slug |
| `intl_fx_swap` | Reported 10% / FX-neutral 13% (swapped) |
| `skip_compensation_disclosure` | Missing Note 8 SBC policy — L2 section recall fail |
| `treat_sbc_as_segment_line_item` | Adds SBC ($19,467M) to segment sum → consolidated **736,391** | L1 → `SBC_ALLOCATION_ERR` |
| `cite_duplicate_snippet` | Reuses same Note 10 row for multiple metrics (L3) |

Decoy slug `segment_financials_prior_year` serves FY2024 column only — must not be used for scored FY2025 metrics.

---

## Expert checklist

- [x] Segment net sales match pilot bundle excerpts (Note 10 FY2025 column)
- [x] Consolidated net sales cross-checks income statement excerpt
- [x] International growth rates match MD&A narrative excerpt (13% / 10% ex-FX)
- [x] Note 8 label correctly reflects Stockholders' Equity (SBC table inside), not a fictional standalone SBC note
- [x] SBC non-allocation policy is fairly tested via required `compensation_disclosure` retrieval
- [x] Five-section path order is auditable and issuer-agnostic via path roles
- [x] No investment recommendation required (Type F)
- [x] SBC expense **$19,467M** verified against Note 8 FY2025 column (10-K filed 2026-02-06)
- [x] SBC allocation trap: consolidated **736,391** → `treat_sbc_as_segment_line_item` / `SBC_ALLOCATION_ERR`
- [x] Live eval (Jul 2026, role slugs): L2 separates models that skip Note 8; L3 duplicate-snippet penalty on gpt-4o AMZN runs

**Scale pass metadata (2026-07-02, no numeric changes):** `verification_schema`; `section_slug` on all extracted citations; `fracture_code` on each `failure_modes` entry (P3-14 parity with KO/GOOGL).

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task AMZN_footnote_reconciliation
```

Expected: `all_pass: true`

**SBC trap regression (exit code 1 expected):**

```bash
python3 benchmark_v0.1/scripts/verify_footnote_exact.py \
  --ground-truth benchmark_v0.1/ground_truth/AMZN_footnote_reconciliation_gt.json \
  --agent-output /tmp/amzn_sbc_trap.json
```

Fixture `/tmp/amzn_sbc_trap.json`:

```json
{
  "north_america_net_sales": 426305,
  "international_net_sales": 161894,
  "aws_net_sales": 128725,
  "consolidated_net_sales": 736391,
  "international_reported_growth_pct": 13.0,
  "international_cc_growth_pct": 10.0
}
```

Expected: `failure_modes: ["treat_sbc_as_segment_line_item"]`, `fracture_codes: ["SBC_ALLOCATION_ERR"]`, `sbc_trap_triggered: true`

---

## Expert verdict

**Verdict:** approve  

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Date:** 2 July 2026  

### Comments

- **Segment net sales / consolidated:** Confirmed. FY2025 column ties exactly (716,924); `F_exact` archetype is correct.
- **International FX disclosure:** Confirmed. 13% reported / 10% ex-FX matches MD&A excerpt.
- **Note 8 / SBC:** Confirmed. SBC lives under Stockholders' Equity; **$19,467M** FY2025 total expense; not in segment net sales sum.
- **SBC trap:** Confirmed. Agent output with consolidated 736,391 correctly fails L1 with `SBC_ALLOCATION_ERR`.
- **Path roles / five-section gold path:** Confirmed. Issuer-agnostic slugs; Note 8 gate is fair.
- **Compliance:** Confirmed. No investment recommendation required.
- **Scale pass metadata (2026-07-02):** Confirmed. `verification_schema`, citation `section_slug` tokens, and `fracture_code` on failure modes — no numeric or snippet changes.

**Sign-off:** AMZN third pilot task cleared for **published** benchmark use alongside GOOGL and PEP. GT artifact **`expert_reviewed`** as of 2026-07-02 (scale-pass metadata re-confirmed).
