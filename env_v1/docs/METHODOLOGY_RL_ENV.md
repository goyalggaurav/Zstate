# RL Environment Methodology

**Version:** 1.0  
**Audience:** AI lab RL infra teams  
**Status:** Review-ready (defense rubric REV-04 approved 2026-07-01)  
**Episode:** `solaris_adj_eps_dispute_v1` v1.1.3

---

## 1. What this environment tests

Dual-control equity research: an **analyst agent** must retrieve filing data, classify one-time vs recurring earnings items, **defend the call to a portfolio manager**, and submit adjusted EPS with cited rationale.

Unlike single-turn finance QA benchmarks, reward depends on **process** (grounding, defense under pushback), not final number alone.

**Reference episode:** Solaris Components (SLRS) Q2 2025 adjusted-EPS dispute — sale-leaseback exclude, R&D tax credit judgment, prior-year pattern, CEO transcript distractor.

---

## 2. Anti-reward-hacking design

| Attack | Defense |
|--------|---------|
| Pattern-match correct adjusted EPS ($1.24) | Grounding (0.25) requires FY2023 + FY2024 + 10-Q retrievals |
| Repeat polished answer to PM | Defense (0.20) + Follow-up C → **defense = 0** |
| Invent footnote magnitudes | Hallucination penalty (−0.10) vs tool logs |
| Assert prior-year pattern without FY footnotes | `unsupported_prior_year_claim` (0.5 penalty) |
| Cite CEO rhetoric over Note 12 filing language | `rhetoric_over_filing` + `note12_mischaracterized` |
| Capitulate to PM desk view without retrieval | `pushover` flag → defense capped at 0.35 |
| Stall until timeout | Outcome capped at 0.5 if no `submit_recommendation` |

**Outcome (0.45) alone is insufficient** for maximum composite reward. Frontier GPT-4o median composite **0.43–0.54** across campaigns while often landing $1.24 — traps fire on process, not EPS.

---

## 3. Verifier components

```
Reward = 0.45·Outcome + 0.25·Grounding + 0.20·Defense − 0.10·Hallucination
```

All four sub-scores exported per episode. See [dual_control_spec_v1.md](./dual_control_spec_v1.md) and `env_v1/verifier/weights.json`.

| Component | What it measures | Benchmark layer analog |
|-----------|------------------|------------------------|
| **Outcome** | Sale-leaseback exclude (binary) + adjusted EPS tier + Note 12 judgment | L1 + L2 |
| **Grounding** | Required doc_id hits in tool log | L2 section recall |
| **Defense** | PM engagement under pushback | L2 (env-only) |
| **Hallucination** | Claims not supported by retrieved excerpts | L3 veto |

### Outcome tiers (Solaris)

| Adjusted EPS | Interpretation |
|--------------|----------------|
| $1.20 | Exclude leaseback + R&D credit |
| $1.24 | Exclude leaseback; include R&D as quasi-recurring (valid judgment path) |
| Other | `OUTCOME_FAIL` |

---

## 4. PM policy and failure modes

Scripted FSM (`pm_v1_1.json`): opening pushback → follow-up A/B/C → pushover branch → acceptance.

| Failure mode | Fracture | Frontier signal (GPT-4o v3) |
|--------------|----------|----------------------------|
| `omit_prior_year` | SECTION_MISS | 3/3 runs — FY2023 footnote not retrieved |
| `unsupported_prior_year_claim` | HALLUC_FILL | Pattern cited without FY footnotes |
| `rhetoric_over_filing` | HALLUC_FILL | CEO transcript over Note 12 |
| `note12_mischaracterized` | HALLUC_FILL | True-up treated as recurring without filing contrast |
| `engagement_failure` | ENGAGEMENT_FAIL | 2/3 v3 — **Agency Collapse Override** (defense = 0) |
| `invalid_adjusted_eps` | OUTCOME_FAIL | 1/3 v3 — submitted $1.28 (consensus anchor) |
| `pushover` | ENGAGEMENT_FAIL | **Epistemic Surrender Cap** (defense ≤ 0.35) |

Defense rubric (REV-04, v1.1.1): **Epistemic Baseline 65%** (Conflict Resolution + Data Provenance) → Thesis Recalibration 20% → Semantic Progression 15%; veto overrides below stack. Stack diagram: [DEFENSE_RUBRIC_REVIEW.md](../../docs/expert_drafts/DEFENSE_RUBRIC_REVIEW.md).

Full fracture summary: [FRACTURE_REPORT_v0.md](../../docs/FRACTURE_REPORT_v0.md).

---

## 5. Calibration loop (separate from RL)

1. **Deterministic scorer** (current) — math, doc_id hits, heuristic defense, hallucination patterns.
2. **Expert adjudication** — 10–20% sample (`adjudication_sample_rate: 0.15` in weights.json).
3. CFA reviews Outcome judgment half and Defense; target κ ≥ 0.7 (Expert-Aligned Ground Truth).
4. Adjust thresholds — **does not train the agent**.

LLM-judge for Defense deferred until κ-calibration (P1-13).

---

## 6. Public vs private artifacts

| Shared with labs | Never public |
|------------------|--------------|
| Task brief, tool API, corpus excerpts | Gold keys (`gold_keys/`) |
| Sample + frontier trajectories (scores exposed) | Full PM branch trigger logic |
| Methodology (this doc) + fracture taxonomy | Expert adjudication sheets |
| Example gold key template | Production defense LLM-judge prompts |

---

## 7. Reproducibility

- Fixed versioned corpus bundle per episode (`corpus/solaris_bundle_v1.json`)
- No live web retrieval in episodes
- Deterministic tool backend
- PM policy v1.1.3: scripted FSM with pushover + fallback escalation
- Frontier runs: `python3 scripts/run_frontier_batch.py` — see [AGENT_ADAPTERS.md](./AGENT_ADAPTERS.md)

---

## 8. Lab demo package

### Scripted demos (no API key)

```bash
python3 env_v1/scripts/run_episode.py --mode all
python3 scripts/smoke_test.py
```

| Trace | Composite | Purpose |
|-------|-----------|---------|
| `sample_trace_good.json` | ~0.88 | Gold path |
| `sample_trace_partial.json` | ~0.45 | Follow-up C engagement fail |
| `sample_trace_timeout.json` | ~0.25 | Turn budget exhausted |
| `sample_trace_pushover.json` | ~0.44 | PM pushover trap |
| `sample_trace_rhetoric.json` | ~0.54 | CEO vs filing trap |

### Frontier reference (GPT-4o, API key required)

| Campaign | Episode | Median composite | Notes |
|----------|---------|------------------|-------|
| v2 (rescored) | v1.1.2 scorer on v1.1.1 traces | 0.5408 | Baseline under tightened scorer |
| v3 (live) | v1.1.2 runtime | 0.4283 | ENGAGEMENT_FAIL 2/3; note12 trap 3/3 |

Index: [FRONTIER_RUNS.md](../runs/frontier/FRONTIER_RUNS.md)

### One-liner pitch

> Fixed filing bundle + skeptical PM FSM + exposed 4-component reward → training-grade signal for earnings-quality defense, not single-turn QA accuracy.

---

## 9. Related docs

| Doc | Purpose |
|-----|---------|
| [dual_control_spec_v1.md](./dual_control_spec_v1.md) | Episode spec |
| [AGENT_ADAPTERS.md](./AGENT_ADAPTERS.md) | scripted / mock / openai |
| [SOLARIS_GOLD_KEY_REVIEW.md](../../docs/expert_drafts/SOLARIS_GOLD_KEY_REVIEW.md) | CFA episode review |
| [EXPERT_REVIEW_WORKFLOW.md](../../docs/EXPERT_REVIEW_WORKFLOW.md) | Sign-off process |
| [ROADMAP.md](../../docs/ROADMAP.md) | Phase map |
