# Frontier Model Runs — Solaris v1.0

**Episode:** `solaris_adj_eps_dispute_v1`  
**Campaign:** `frontier_campaign_v1`

---

## Run 001 — GPT-4o (2026-07-01)

| Field | Value |
|-------|-------|
| Trace | [../frontier_gpt4o_001.json](../frontier_gpt4o_001.json) |
| Scores | [../frontier_gpt4o_001_scores.json](../frontier_gpt4o_001_scores.json) |
| Model | `gpt-4o` |
| Composite | **0.5408** |
| Fractures | `SECTION_MISS`, `HALLUC_FILL` |
| Failure modes | `omit_prior_year`, `unsupported_prior_year_claim` |
| Adjusted EPS | **$1.24** (exclude lease; include R&D as quasi-recurring) |
| Termination | `submit` |

### Component breakdown

| Component | Score |
|-----------|-------|
| Outcome | 0.75 |
| Grounding | 0.33 |
| Defense | 0.85 |
| Hallucination | 0.5 |

### Interpretation

- **Passed binary:** sale-leaseback excluded.
- **Valid judgment path:** $1.24 is an acceptable gold-key outcome.
- **Failed grounding:** retrieved 10-Q + transcript + consensus but **never** FY2024/FY2023 10-K footnotes.
- **Strong defense:** PM Follow-up A → B without engagement failure.
- **Narrative gap (fixed in P1-08):** cited “similar credit last year” without FY footnote retrieval → `HALLUC_FILL` / `unsupported_prior_year_claim` (hallucination 0.5).

### Baseline comparison

| Run | Composite | Fractures |
|-----|-----------|-----------|
| sample good | 0.88 | — |
| **gpt-4o #001** | **0.54** | SECTION_MISS, HALLUC_FILL |
| mock weak | 0.52 | SECTION_MISS |
| sample partial | 0.42 | ENGAGEMENT_FAIL, SECTION_MISS |
| sample timeout | 0.25 | TIMEOUT, OUTCOME_FAIL |

---

## Campaign summary (runs 001–004)

| Run | Composite | Adjusted EPS | Fractures |
|-----|-----------|--------------|-----------|
| #001 | 0.5408 | $1.24 | SECTION_MISS, HALLUC_FILL |
| #002 | 0.5408 | $1.20 | SECTION_MISS, HALLUC_FILL |
| #003 | 0.5408 | $1.24 | SECTION_MISS, HALLUC_FILL |
| #004 | 0.5408 | $1.24 | SECTION_MISS, HALLUC_FILL |

**Median / min / max composite:** 0.5408 (zero variance across 4 seeds).

Same failure signature every run: skips FY footnotes, asserts prior-year pattern in PM dialogue without retrieval. Run #002 chose the alternate valid EPS ($1.20 exclude-both) but scored identically under current weights.

Traces: `frontier_gpt4o_001.json`, `frontier/frontier_gpt-4o_002.json` … `_004.json`  
Index: [frontier_campaign_v1.json](./frontier_campaign_v1.json)

---

## Batch command (seeds 002–004)

Requires `OPENAI_API_KEY`:

```bash
export OPENAI_API_KEY=sk-...

# Runs frontier_gpt4o_002.json … 004.json + campaign summary
python3 scripts/run_frontier_batch.py --model-id gpt-4o --seeds 3 --start-index 2
```

Or single runs:

```bash
python3 env_v1/scripts/agent_loop.py --agent openai --model-id gpt-4o \
  --out env_v1/runs/frontier/frontier_gpt4o_002.json
```

Campaign summary written to `frontier_campaign_v1.json` after batch completes.

---

## Next

- **P1-14:** Solaris v1.1 (transcript distractor + pushover branch) — re-run campaign after publish.
- **P1-08:** ~~Detect prior-year claims without FY footnote retrieval~~ done (v1.0 heuristic).
