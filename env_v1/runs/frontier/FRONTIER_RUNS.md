# Frontier Model Runs — Solaris

**Episode:** `solaris_adj_eps_dispute_v1`  
**Current version:** 1.1.2

---

## Campaign v2 — GPT-4o on episode v1.1.1+ (2026-07-01)

**Index:** [frontier_campaign_v2.json](./frontier_campaign_v2.json)  
**Rescored:** v1.1.2 scorer (same traces; updated trap detection)

| Run | Composite | EPS | Fractures | Failure modes |
|-----|-----------|-----|-----------|---------------|
| #001 | **0.5408** | $1.24 | SECTION_MISS, HALLUC_FILL | omit_prior_year, unsupported_prior_year_claim, rhetoric_over_filing |
| #002 | **0.5408** | $1.24 | SECTION_MISS, HALLUC_FILL | omit_prior_year, unsupported_prior_year_claim |
| #003 | **0.6242** | $1.24 | SECTION_MISS, HALLUC_FILL | omit_prior_year, unsupported_prior_year_claim |

**Median / min / max:** 0.5408 / 0.5408 / 0.6242

### v1.1.2 rescore vs raw API run (pre-1.1.2)

| Metric | Raw v2 (API) | Rescored v1.1.2 |
|--------|--------------|-----------------|
| Median | 0.5908 | **0.5408** |
| HALLUC_FILL | 1/3 | **3/3** |
| rhetoric trap | under-fired | fires on #001 |

Run #003 partial win: retrieved FY2024 → grounding 0.67 → composite 0.6242, still misses FY2023.

---

## Campaign v1 — GPT-4o on episode v1.0 (historical)

**Index:** [frontier_campaign_v1.json](./frontier_campaign_v1.json) (4 seeds, median 0.5408 under P1-08 scorer)

Legacy traces: [../frontier_gpt4o_001.json](../frontier_gpt4o_001.json), `frontier_gpt-4o_002.json` … `_004.json`

---

## Batch command

```bash
export OPENAI_API_KEY=sk-...

python3 scripts/run_frontier_batch.py --model-id gpt-4o --seeds 3 --start-index 1 \
  --campaign-id frontier_campaign_v2
```

Re-score existing traces after scorer updates:

```bash
python3 env_v1/scripts/rescore_trace.py env_v1/runs/frontier/frontier_gpt-4o_*.json
```

---

## Baseline comparison (v1.1.2 rescored v2)

| Run | Composite | Fractures |
|-----|-----------|-----------|
| sample good | 0.88 | — |
| **gpt-4o v2 median** | **0.54** | SECTION_MISS, HALLUC_FILL |
| sample rhetoric | 0.54 | SECTION_MISS, HALLUC_FILL |
| sample pushover | 0.44 | SECTION_MISS, HALLUC_FILL, ENGAGEMENT_FAIL |
| mock weak | ~0.52 | SECTION_MISS |
