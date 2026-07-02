# KO Footnote Reconciliation — Grader Rubric (Draft)

**Task:** `KO_footnote_reconciliation`  
**Expert review:** [KO_GT_REVIEW.md](../../docs/expert_drafts/KO_GT_REVIEW.md)  
**Verify:** `verify_footnote_exact.py` / `verify_benchmark_l1.py --task KO_footnote_reconciliation`  
**Status:** Draft — expert sign-off required

## L1 (automated)

All six segment net revenues, consolidated net operating revenues ($50,256M FY2025), and Latin America growth pair (12% reported / 15% CC) must match GT within tolerance. Six-segment sum must reconcile to consolidated.

## L2 (gold path)

Required section order: `segment_policy` → `segment_financials` → `consolidated_primary` → `narrative_fx`.

## L3 (citations)

Distinct verbatim snippets per metric; `section_slug` required (no note numbers in GT). Policy acknowledgement `global_ventures_is_reportable_segment`.

## Expert narrative (manual sample)

- Agent explains Global Ventures is a reportable segment (Costa, innocent), not corporate overhead.
- Reconciliation table shows six-segment sum equals consolidated $50,256M.
- Latin America narrative distinguishes reported vs currency-neutral growth.
