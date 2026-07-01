# Pilot Eval Report — July 2026 (role slugs)

**Campaign:** `pilot_eval_3task_v1`  
**Run date:** 2026-07-01 (fresh live, post P2-13–15)  
**Models:** `gpt-4o`, `claude-sonnet-4-5`  
**Tasks:** GOOGL + PEP + AMZN (18 runs, eval_mode on)  
**Artifacts:** `benchmark_v0.1/runs/pilot_eval_3task_v1/pilot_eval_3task_v1.json`

---

## Methodology

- **Eval mode:** generic citation rules only (no task-specific cheat-sheets).
- **Path roles:** canonical slugs (`segment_financials`, `compensation_disclosure`, etc.) — not issuer note numbers.
- **Headline composite (P2-18):** GOOGL excluded from headline — task is at ceiling for frontier models; use **discrimination v2** (PEP + AMZN) for model ranking.
- **Layers:** L1 verify (metrics) · L2 gold-path (section recall/order/tools) · L3 submission (citations + policy acks).

---

## Results summary

| Metric | All 3 tasks | Headline (PEP + AMZN) |
|--------|-------------|------------------------|
| Runs scored | 18/18 | 12/12 |
| L1 pass rate (median) | 1.0 | 1.0 |
| L2 score (median) | 1.0 | 1.0 |
| L3 score (median) | 0.858 | 0.603 |
| Composite (median) | 0.979 | 0.928 |

### Per-model composite (median)

| Model | GOOGL | PEP | AMZN | All-task | **Headline weighted** |
|-------|-------|-----|------|----------|------------------------|
| gpt-4o | 1.0 | 0.864 | 0.958 | 0.958 | **0.911** |
| claude-sonnet-4-5 | 1.0 | 0.898 | 1.0 | 1.0 | **0.949** |

Headline weighted composite = task-weighted mean of PEP and AMZN task medians (`pilot_eval_discrimination_v2.json`).

---

## Fracture signal (Track A)

| Code | Count (18 runs) | Interpretation |
|------|-----------------|----------------|
| CITE_BROAD | 9 | Duplicate snippet reuse across metrics (L3 partial credit) |
| CITE_HALLUC | 3 | Snippet not in bundle excerpt |

**PEP** remains the sharpest wedge (gpt-4o L3 **0.32** on duplicate MD&A row citations).  
**AMZN** now separates models after 5-section path: gpt-4o L2 perfect, L3 ~0.72 (duplicate Note 10 snippets); claude median **1.0**.  
**GOOGL** ceiling **1.0** both models — motivates headline exclusion and future L3 hardening (`distinct_snippets_required` added P2-18).

---

## Expert / publish status (post P2-16)

| Task | Expert review | Status |
|------|---------------|--------|
| GOOGL | `GOOGL_GT_REVIEW.md` | published |
| PEP | `PEP_FX_GT_REVIEW.md` | published |
| AMZN | `AMZN_GT_REVIEW.md` | published (2026-07-02) |
| NFLX | — | draft scaffold (P2-01) |

---

## Next eval actions

1. Live NFLX draft task once expert signs GT (or after P2-08 transcript ingest).
2. Add `gpt-4o-mini` to campaign for wider model spread (P2-19).
3. Re-run after GOOGL L3 rescore on existing traces (distinct-snippet rule).
