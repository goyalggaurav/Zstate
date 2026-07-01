# Grader Brief — GOOGL Footnote Reconciliation

**Task ID:** `GOOGL_footnote_reconciliation` (Type F)  
**Canonical prompt:** `benchmark_v0.1/tasks/GOOGL_footnote_reconciliation.json` → `prompt.text`  
**Ground truth:** `benchmark_v0.1/ground_truth/GOOGL_footnote_reconciliation_gt.json`  
**Verify script:** `benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py`  
**CFA sign-off:** `docs/expert_drafts/GOOGL_GT_REVIEW.md` (approved 2026-07-01)

---

## Agent prompt (verbatim)

Using Alphabet Inc.'s Form 10-Q for the quarter ended March 31, 2026 (filed April 30, 2026), reconcile reportable segment revenues to consolidated total revenue for Q1 2026.

1. Extract Q1 2026 revenue for Google Services, Google Cloud, and Other Bets from the segment disclosure (Note 15) and cross-check against the revenue disaggregation table (Note 2).
2. Sum the three reportable segments and compare to consolidated total revenue for the quarter.
3. Identify and quantify any reconciling item(s). Explain, citing the filing, why the reconciling item is not included in the three reportable segments.
4. Produce a reconciliation table (USD millions) and a short narrative (no investment recommendation).

**Constraints:** specified 10-Q only; every number cited; preserve hedging sign; Python required for arithmetic; mark unverified values — do not interpolate.

---

## Scoring layers (Type F weights)

| Layer | Weight | What it measures |
|-------|--------|------------------|
| **L1** | 55% | Numeric extraction + reconciliation balance |
| **L2** | 25% | Section recall (Note 15 + Note 2) + narrative anchors |
| **L3** | 20% | Citation quality (table-level, auditable) |

Report **layer sub-scores**, not a single pass/fail. A blind-sum failure can still earn partial L2 if Note 15 was accessed.

---

## Failure modes (primary traps)

| ID | Label | Wrong output signature | Fracture code | Typical L1 |
|----|-------|------------------------|---------------|------------|
| `blind_sum` | Blind sum | `consolidated_total = 110,076` or hedging omitted; segments correct | `RECON_OMIT` | ~45–55% |
| `sign_error` | Sign error | `hedging = +180`; implied total 110,256 | `SIGN_ERR` | ~65–75% |
| `wrong_period` | Wrong column / filing | FY2025 annual, Q1 2025 column, or stale 10-K | `HALLUC_FILL` | ~0–25% |

Additional modes (see ground truth): `hedging_as_segment`, `wrong_filing`.

The verify script auto-tags the primary mode when run with `--agent-output`.

---

## Source anchors (human reviewer)

| Metric | Note | Table | Column |
|--------|------|-------|--------|
| Segment revenues | Note 15 | Revenues, traffic acquisition costs (TAC) and monetization metrics by segment | Three months ended March 31, **2026** |
| Hedging + total | Note 15 | Same table (hedging row + total revenues row) | Same column |
| Cross-check | Note 2 | Disaggregation of revenue by type | Three months ended March 31, **2026** |

**Policy text (Note 15):** hedging gains (losses) related to revenue are not allocated to reportable segments.

---

## Gold answer (Q1 2026, USD millions)

| Line | Value |
|------|-------|
| Google Services | 89,637 |
| Google Cloud | 20,028 |
| Other Bets | 411 |
| Segment sum | 110,076 |
| Hedging gains (losses) | (180) |
| Consolidated total | 109,896 |

**Check:** 110,076 + (−180) = 109,896

---

## Verification

```bash
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --agent-output agent_values.json
```

Expected on ground truth: `all_pass: true`, `failure_modes: []`.
