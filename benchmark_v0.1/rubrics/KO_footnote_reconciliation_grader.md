# KO Footnote Reconciliation — Grader Rubric (Draft)

**Task:** `KO_footnote_reconciliation`  
**Expert review:** [KO_GT_REVIEW.md](../../docs/expert_drafts/KO_GT_REVIEW.md)  
**Verify:** `verify_footnote_exact.py` / `verify_benchmark_l1.py --task KO_footnote_reconciliation`  
**Status:** Draft — expert sign-off required

## L1 (automated)

Five operating segments' **third-party** net operating revenues, Corporate third-party net revenues ($144M), consolidated net operating revenues ($47,941M FY2025), and Latin America MD&A pair ((2)% total change / (12)% FX impact) must match GT. Sum of segments + Corporate must equal consolidated.

## L2 (gold path)

Required section order: `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

## L3 (citations)

Distinct verbatim snippets per metric; `section_slug` required. Policy acknowledgement `global_ventures_sunset_2025`.

## Expert narrative (manual sample)

- Agent notes Global Ventures sunset and five-segment structure for FY2025.
- Reconciliation uses third-party row, includes Corporate, equals $47,941M.
- Latin America narrative distinguishes total net revenue change from FX decomposition column.
