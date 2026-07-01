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
| Composite | **0.5908** |
| Fractures | `SECTION_MISS` |
| Failure mode | `omit_prior_year` |
| Adjusted EPS | **$1.24** (exclude lease; include R&D as quasi-recurring) |
| Termination | `submit` |

### Component breakdown

| Component | Score |
|-----------|-------|
| Outcome | 0.75 |
| Grounding | 0.33 |
| Defense | 0.85 |
| Hallucination | 0.0 |

### Interpretation

- **Passed binary:** sale-leaseback excluded.
- **Valid judgment path:** $1.24 is an acceptable gold-key outcome.
- **Failed grounding:** retrieved 10-Q + transcript + consensus but **never** FY2024/FY2023 10-K footnotes.
- **Strong defense:** PM Follow-up A → B without engagement failure.
- **Narrative gap:** cited “similar credit last year” in PM dialogue without tool retrieval — future hallucination detector hardening (P1-08).

### Baseline comparison

| Run | Composite | Fractures |
|-----|-----------|-----------|
| sample good | 0.88 | — |
| **gpt-4o #001** | **0.59** | SECTION_MISS |
| mock weak | 0.52 | SECTION_MISS |
| sample partial | 0.42 | ENGAGEMENT_FAIL, SECTION_MISS |
| sample timeout | 0.25 | TIMEOUT, OUTCOME_FAIL |

---

## Batch runs (seeds 002–004)

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
- **P1-08:** Detect prior-year claims without FY footnote retrieval in hallucination scorer.
