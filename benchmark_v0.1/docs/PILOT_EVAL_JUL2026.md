# Pilot Eval Report — July 2026 (role slugs)

**Campaign:** `pilot_eval_4task_v1`  
**Run date:** 2026-07-02 (live NFLX re-run post expert sign-off)  
**Models:** `gpt-4o`, `claude-sonnet-4-5`  
**Tasks:** GOOGL + PEP + AMZN + NFLX (24 runs, eval_mode on)  
**Artifacts:** `benchmark_v0.1/runs/pilot_eval_4task_v1/pilot_eval_4task_v1.json`

---

## Methodology

- **Eval mode:** generic citation rules only (no task-specific cheat-sheets).
- **Path roles:** canonical slugs (`segment_financials`, `narrative_guidance`, etc.) — not issuer note numbers.
- **Headline composite (P2-18):** GOOGL excluded from headline — ceiling task for frontier models; headline = PEP + AMZN + NFLX.
- **Layers:** L1 verify (metrics) · L2 gold-path (section recall/order/tools) · L3 submission (citations + policy acks).

---

## Results summary

| Metric | All 4 tasks | Headline (PEP + AMZN + NFLX) |
|--------|-------------|-------------------------------|
| Runs scored | 24/24 | 18/18 |
| L1 pass rate (median) | 1.0 | 1.0 |
| L2 score (median) | 1.0 | 1.0 |
| L3 score (median) | 0.915 | 0.915 |
| Composite (median) | 0.983 | 0.958 |

### Per-model composite (median)

| Model | GOOGL | PEP | AMZN | NFLX | All-task | **Headline weighted** |
|-------|-------|-----|------|------|----------|------------------------|
| gpt-4o | 1.0 | 0.864 | 0.958 | 0.629 | 0.958 | **0.817** |
| claude-sonnet-4-5 | 1.0 | 0.898 | 1.0 | 1.0 | 1.0 | **0.966** |

Headline weighted composite = task-weighted mean of PEP, AMZN, and NFLX task medians (`pilot_eval_4task_v1.json`).

---

## NFLX guidance drift (P2-01 / P2-19)

Fourth published task — annual FY2025 cash content guidance (~$18B) vs nine-month YTD actuals from Q3 2025 10-Q.

| Model | NFLX composite (median) | L1 | L2 | L3 | Notes |
|-------|-------------------------|----|----|-----|-------|
| claude-sonnet-4-5 | **1.0** | pass | pass | pass | 3/3 clean after boolean submit schema fix |
| gpt-4o | **0.629** | partial | pass | ~0.39 | Amort rounding (4002 vs 4003) on 2 runs; L3 duplicate snippets all runs |

**Infrastructure fixes during NFLX pilot:**

- Explicit `Search_Filing` period hints in task prompt (2024Q4 guidance vs 2025Q3 actuals).
- Submit tool schema: `guidance_pace_under` typed as `boolean` (was inferred as integer via Python `bool` ⊂ `int`).
- Trap decoy **7,385** sourced to Q2 2025 10-Q six-month column; amort trap **11,658** from Q3 nine-month amort line.

---

## Fracture signal (Track A)

| Code | Count (24 runs) | Interpretation |
|------|-----------------|---------------|
| CITE_BROAD | 11 | Duplicate snippet reuse across metrics (L3 partial credit) |
| CITE_HALLUC | 3 | Snippet not in bundle excerpt |
| GUIDANCE_PERIOD_ERR | 2 | True trap hits only (mis-tagged non-trap L1 fails fixed in verifier) |

**PEP** remains a sharp wedge (gpt-4o L3 duplicate MD&A citations).  
**AMZN** separates models on L3 citation quality.  
**NFLX** separates models on L1 precision + L3 citations once task is live.  
**GOOGL** ceiling **1.0** both models — excluded from headline ranking.

---

## Expert / publish status

| Task | Expert review | Status |
|------|---------------|--------|
| GOOGL | `GOOGL_GT_REVIEW.md` | published |
| PEP | `PEP_FX_GT_REVIEW.md` | published |
| AMZN | `AMZN_GT_REVIEW.md` | published |
| NFLX | `NFLX_GT_REVIEW.md` | published (2026-07-02) |

---

## Next eval actions

1. ~~**P2-06** — leaderboard v0~~ → [LEADERBOARD_v0.md](./LEADERBOARD_v0.md) (actionable fracture view)
2. Add `gpt-4o-mini` for wider model spread.
3. **LATER-06** — NFLX EDGAR verbatim ingest (excerpt SHA-256 mitigates until then).
4. Tighten gpt-4o L3 on NFLX (distinct snippet enforcement already in eval_mode).
