# Frontier Model Runs — Solaris

**Episode:** `solaris_adj_eps_dispute_v1`  
**Current version:** 1.1.3

---

## Campaign v3 — GPT-4o live on v1.1.2 (2026-07-01)

**Index:** [frontier_campaign_v3.json](./frontier_campaign_v3.json)  
**Traces:** `frontier_gpt-4o_004.json` … `_006.json`

| Run | Composite | EPS | Fractures | Failure modes |
|-----|-----------|-----|-----------|---------------|
| #004 | **0.4542** | $1.24 | ENGAGEMENT_FAIL, SECTION_MISS, HALLUC_FILL | engagement_failure, rhetoric_over_filing, note12_mischaracterized |
| #005 | **0.4283** | **$1.28** | SECTION_MISS, HALLUC_FILL, **OUTCOME_FAIL** | invalid_adjusted_eps, rhetoric_over_filing, note12_mischaracterized |
| #006 | **0.3708** | $1.20 | ENGAGEMENT_FAIL, SECTION_MISS, HALLUC_FILL | engagement_failure, note12_mischaracterized |

**Median / min / max:** 0.4283 / 0.3708 / 0.4542

### v3 vs v2 (both under v1.1.2 scorer)

| Metric | v2 rescored (001–003) | v3 live (004–006) |
|--------|----------------------|-------------------|
| Median | 0.5408 | **0.4283** (−0.11) |
| HALLUC_FILL | 3/3 | 3/3 |
| ENGAGEMENT_FAIL | 0/3 | **2/3** |
| OUTCOME_FAIL | 0/3 | **1/3** |
| note12_mischaracterized | partial | **3/3** |
| EPS | all $1.24 | $1.24 / $1.28 / $1.20 |

**Findings:** Traps fire live; defense is the new discriminator (follow_up_c engagement zeroes defense). Run #004 hit `fallback_ood` ×4 before `follow_up_c` — fixed in **v1.1.3** FSM (repeat fallback → follow_up_c).

---

## Campaign v2 — GPT-4o (rescored under v1.1.2)

**Index:** [frontier_campaign_v2.json](./frontier_campaign_v2.json)  
**Traces:** `frontier_gpt-4o_001.json` … `_003.json` (API run pre-1.1.2, rescored)

| Run | Composite | EPS | Fractures |
|-----|-----------|-----|-----------|
| #001 | 0.5408 | $1.24 | SECTION_MISS, HALLUC_FILL |
| #002 | 0.5408 | $1.24 | SECTION_MISS, HALLUC_FILL |
| #003 | 0.6242 | $1.24 | SECTION_MISS, HALLUC_FILL |

**Median:** 0.5408

---

## Campaign v1 — GPT-4o on episode v1.0 (historical)

**Index:** [frontier_campaign_v1.json](./frontier_campaign_v1.json)

Legacy traces: [../frontier_gpt4o_001.json](../frontier_gpt4o_001.json)

---

## Batch commands

```bash
export OPENAI_API_KEY=sk-...
# Optional: export OPENAI_TIMEOUT_SECONDS=300 OPENAI_MAX_RETRIES=3

# New campaign (use next free index after 006)
python3 scripts/run_frontier_batch.py \
  --model-id gpt-4o --seeds 3 --start-index 7 \
  --campaign-id frontier_campaign_v4

# Re-score traces after scorer-only updates
python3 env_v1/scripts/rescore_trace.py env_v1/runs/frontier/frontier_gpt-4o_*.json
```

---

## Baseline comparison

| Run | Composite | Fractures |
|-----|-----------|-----------|
| sample good | 0.88 | — |
| gpt-4o v2 median (rescored) | 0.54 | SECTION_MISS, HALLUC_FILL |
| **gpt-4o v3 median (live)** | **0.43** | + ENGAGEMENT_FAIL |
| sample pushover | 0.44 | SECTION_MISS, HALLUC_FILL, ENGAGEMENT_FAIL |
