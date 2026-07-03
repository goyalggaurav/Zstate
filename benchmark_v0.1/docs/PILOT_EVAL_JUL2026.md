# Pilot Eval Report — July 2026 (5-task pilot, v0.2 schema)

**Campaign:** `pilot_eval_5task_v1` (pinned baseline)  
**Run date:** 2026-07-02 (post-9B rescore pinned; v0.2 schema pass 2026-07-03)  
**Models:** `gpt-4o`, `claude-sonnet-4-5`, `gemini-2.5-flash`  
**Tasks:** GOOGL + PEP + AMZN + NFLX + KO (45 runs, eval_mode on)  
**Artifacts:** `benchmark_v0.1/runs/pilot_eval_5task_v1/pilot_eval_5task_v1.json`  
**Diagnostic fork:** `pilot_eval_5task_synthetic_l3_v1` (15 runs, synthetic L3 decoys on — see below)

---

## Methodology

- **Eval mode:** generic citation rules only (no task-specific cheat-sheets).
- **Path roles:** canonical slugs (`segment_financials`, `narrative_guidance`, etc.) — not issuer note numbers.
- **Headline composite:** GOOGL excluded — ceiling task for frontier models; headline = PEP + AMZN + NFLX + KO (task-weighted mean of task medians).
- **Layers:** L1 verify (metrics) · L2 gold-path (section recall/order/tools) · L3 submission (citations + policy acks).
- **v0.2 L3 anchors (P3-35/36):** GT-derived row/column anchors with token-set matching; gold-path overrides only where discrimination requires them (KO bridge). Anchor regression + schema coherence gates in CI (P3-36/37/39).
- **KO bridge naming:** `reconciliation_bridge_total` (renamed from `segment_net_revenues_sum` in v0.2) = five segments + Corporate + Eliminations = consolidated $47,941M.

---

## Results summary (pinned baseline)

### Per-model composite (median, 3 runs per cell)

| Model | GOOGL | PEP | AMZN | NFLX | KO | **Headline weighted** |
|-------|-------|-----|------|------|-----|------------------------|
| claude-sonnet-4-5 | 1.0 | 1.0 | 1.0 | 0.879 | 0.896 | **0.944** |
| gemini-2.5-flash | 1.0 | 1.0 | 1.0 | 0.830 | 0.873 | **0.926** |
| gpt-4o | 1.0 | 0.864 | 0.958 | 0.830 | 0.873 | **0.881** |

Headline weighted composite = task-weighted mean of PEP, AMZN, NFLX, and KO task medians (`pilot_eval_5task_v1.json`).

---

## Fracture signal (Track A, 45 runs)

| Code | Count | Interpretation |
|------|-------|---------------|
| CITE_BROAD | 17 | Duplicate snippet reuse across metrics (L3 partial credit) |
| CITE_HALLUC | 13 | Snippet not verbatim in bundle excerpt |
| TIMEOUT | 1 | No submit within execution limits |

**NFLX** and **KO** are the sharpest wedges — every model loses composite there on L3 citation quality.  
**PEP** separates gpt-4o (duplicate MD&A citations).  
**GOOGL** ceiling 1.0 for all three models — excluded from headline ranking.

---

## Synthetic L3 diagnostic (LATER-05, 2026-07-03)

Fork campaign `pilot_eval_5task_synthetic_l3_v1` — same 5 tasks × 3 models × 1 run with `synthetic_l3_eval: true` (decoy bait excerpts injected per P3-15).

- **Decoy bait hits: 0 across 14 evaluated runs.** No frontier model cited a synthetic decoy excerpt. `synthetic_fracture_intensity` = 0.0 for all models.
- 1 run not evaluated: gemini-2.5-flash NFLX TIMEOUT (composite 0.0, no submission to check).
- **Interpretation:** at current decoy strength, synthetic L3 is a robustness checkmark, not a ranking dimension. Ranking continues to come from real-citation quality (CITE_BROAD / CITE_HALLUC). Revisit decoy strength if this changes at 3× runs or with harder baits.
- Diagnostic report: `runs/pilot_eval_5task_synthetic_l3_v1/` (aggregate + leaderboard view). **Pinned baseline unchanged** — `pilot_eval_5task_v1` remains the official pilot report.

**Infrastructure fix during fork run:** OpenAI adapter deferred the retrieval nudge until all parallel `tool_call_id`s have responses (2 gpt-4o slots initially 400'd when the nudge interleaved sibling tool results).

---

## Expert / publish status

| Task | Expert review | Status |
|------|---------------|--------|
| GOOGL | `GOOGL_GT_REVIEW.md` | published |
| PEP | `PEP_FX_GT_REVIEW.md` | published |
| AMZN | `AMZN_GT_REVIEW.md` | published (expert_reviewed metadata 2026-07-02) |
| NFLX | `NFLX_GT_REVIEW.md` | published (computed-citation L3 policy signed off) |
| KO | `KO_GT_REVIEW.md` | published (bridge semantics expert-confirmed 2026-07-02) |

---

## Next eval actions

1. **P3-03 task #6** via `scaffold_task.py` — publish gate now includes schema coherence (P3-37).
2. Tighten L3 on NFLX/KO — CITE_BROAD is the main separator on headline tasks.
3. Synthetic L3 at 3× runs (or harder decoys) before treating it as a ranking dimension.
4. **LATER-06** — full EDGAR ingest (excerpt SHA-256 pins mitigate until then).
