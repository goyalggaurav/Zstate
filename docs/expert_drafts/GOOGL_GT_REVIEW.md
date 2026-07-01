# CFA Review — GOOGL Footnote Reconciliation Ground Truth

**Artifact:** `benchmark_v0.1/ground_truth/GOOGL_footnote_reconciliation_gt.json`  
**Task:** `GOOGL_footnote_reconciliation` (Type F)  
**Scored period:** Q1 2026 (10-Q filed 2026-04-30)  
**Status:** `pending_cfa_review`  
**Eng draft date:** 2026-07-01

---

## Eng summary (draft — please verify)

Reconcile Q1 2026 reportable segment revenues to consolidated total. Agent must identify hedging gains (losses) as the reconciling item not allocated to segments (Note 15).

### Q1 2026 numbers (USD millions) — **please confirm against filing**

| Line | Eng value | Source |
|------|-----------|--------|
| Google Services | 89,637 | 10-Q Note 15, three months ended 2026-03-31 |
| Google Cloud | 20,028 | Same |
| Other Bets | 411 | Same |
| **Segment sum** | **110,076** | Computed |
| **Hedging gains (losses)** | **(180)** | Note 15 / Note 2 — **loss, not gain** |
| **Consolidated total** | **109,896** | Face of statements |

**Reconciliation:** 110,076 + (−180) = 109,896

### FY2025 reference (not scored — context only)

| Consolidated total | 402,836 |
| Hedging (loss) | (127) |

---

## CFA checklist

- [ ] All Q1 2026 figures match [Alphabet 10-Q](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm) — correct column (2026, not 2025)
- [ ] Hedging line is **(180)** not +180
- [ ] Note 15 language supports "not allocated to reportable segments"
- [ ] Note 2 cross-check is appropriate secondary source
- [ ] Trap design is fair (omitting hedging is common agent failure)
- [ ] No investment recommendation required (Type F)

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026
```

Expected: `all_pass: true`

---

## CFA verdict

**Verdict:** _approve / revise_

**Reviewer:** _______________  
**Date:** _______________

### Comments

_(CFA fills in)_
