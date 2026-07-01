# Fracture Report v0 — Solaris Frontier Campaigns

**Version:** 0.1  
**Date:** 2026-07-01  
**Scope:** Track B env — GPT-4o on `solaris_adj_eps_dispute_v1`  
**Sources:** `env_v1/runs/frontier/frontier_campaign_v1.json` … `v3.json`  
**Taxonomy:** `schemas/fracture_taxonomy_v1.json`

---

## Summary

Six GPT-4o frontier runs (001–006) across three campaigns. Under v1.1.2+ scorer, **every run** fails grounding (`SECTION_MISS`) and hallucination checks (`HALLUC_FILL`). v3 live runs add **ENGAGEMENT_FAIL** (2/3) and **OUTCOME_FAIL** (1/3).

| Campaign | Runs | Median composite | Top fractures |
|----------|------|------------------|---------------|
| v1 (historical) | 001–004 | 0.5408 | SECTION_MISS |
| v2 rescored | 001–003 | 0.5408 | SECTION_MISS, HALLUC_FILL |
| v3 live | 004–006 | **0.4283** | + ENGAGEMENT_FAIL, OUTCOME_FAIL |

---

## Fracture frequency (6 frontier runs, latest scorer)

| Code | Label | Count | Rate |
|------|-------|-------|------|
| **SECTION_MISS** | Required doc not retrieved | 6/6 | 100% |
| **HALLUC_FILL** | Unsupported claim / wrong framing | 6/6 | 100% |
| **ENGAGEMENT_FAIL** | PM engagement failure | 2/6 | 33% |
| **OUTCOME_FAIL** | Invalid adjusted EPS | 1/6 | 17% |
| TIMEOUT | No submit before turn budget | 0/6 | 0% |
| PM_OOD | Fallback OOD branch only | 0/6* | — |

\*Agents hit `fallback_ood` branch in traces but fracture code not emitted — consider tagging in v0.2.

---

## Failure mode frequency (env-specific)

| Failure mode | v2 rescored (3) | v3 live (3) | Notes |
|--------------|-----------------|-------------|-------|
| `omit_prior_year` | 3/3 | 3/3 | FY2023 footnote never retrieved |
| `unsupported_prior_year_claim` | 2/3 | 1/3 | Cited pattern without FY evidence |
| `rhetoric_over_filing` | 1/3 | 2/3 | CEO transcript over Note 12 |
| `note12_mischaracterized` | — | **3/3** | v1.1.2+ trap; sharpest v3 signal |
| `engagement_failure` | 0/3 | **2/3** | Follow-up C zero defense |
| `invalid_adjusted_eps` | 0/3 | **1/3** | $1.28 consensus anchor |

---

## Component breakdown (v3 live)

| Run | Outcome | Grounding | Defense | Halluc. penalty | Composite |
|-----|---------|-----------|---------|-----------------|-----------|
| 004 | 0.75 | **0.67** | **0.0** | 0.5 | 0.4542 |
| 005 | **0.5** | 0.33 | 0.85 | 0.5 | 0.4283 |
| 006 | 0.75 | 0.33 | **0.0** | 0.5 | 0.3708 |

**Pattern:** Grounding and Defense are the discriminators — not Outcome binary (sale-leaseback exclude passes 3/3).

---

## Demo trace baselines

| Trace | Composite | Fractures |
|-------|-----------|-----------|
| sample good | 0.88 | — |
| sample rhetoric | 0.54 | SECTION_MISS, HALLUC_FILL |
| sample pushover | 0.44 | SECTION_MISS, HALLUC_FILL, ENGAGEMENT_FAIL |
| sample partial | ~0.45 | ENGAGEMENT_FAIL |
| **gpt-4o v3 median** | **0.43** | SECTION_MISS, HALLUC_FILL, ENGAGEMENT_FAIL |

Frontier model performs near **rhetoric/pushover demo traps**, not near gold path.

---

## Implications for labs

1. **EPS alone is gameable** — $1.24 appears in 4/6 runs; composite spread 0.37–0.62.
2. **Prior-year retrieval** is the grounding bottleneck — FY2023 required, rarely fetched.
3. **Defense under PM pushback** separates partial (0.85) from fail (0.0) — core RL signal.
4. **Note 12 vs CEO rhetoric** — consistent failure mode for transcript-distractor design.

---

## Next (v0.2)

- [ ] Tag `PM_OOD` when agent loops on `fallback_ood` (pre-v1.1.3)
- [ ] Add fracture counts to campaign JSON auto-summary
- [ ] Cross-track GOOGL benchmark fractures (RECON_OMIT, SIGN_ERR) when P2-04 runs
- [ ] v4 campaign under v1.1.3 FSM — validate fallback escalation fix

See [FRONTIER_RUNS.md](../env_v1/runs/frontier/FRONTIER_RUNS.md).
