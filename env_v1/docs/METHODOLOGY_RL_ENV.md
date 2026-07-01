# RL Environment Methodology (Draft)

**Version:** 0.1  
**Audience:** AI lab RL infra teams  
**Status:** Draft — complete after P1 demo trajectories

---

## 1. What this environment tests

Dual-control equity research: an **analyst agent** must retrieve filing data, classify one-time vs recurring earnings items, **defend the call to a portfolio manager**, and submit adjusted EPS with cited rationale.

Unlike single-turn finance QA benchmarks, reward depends on **process** (grounding, defense under pushback), not final number alone.

---

## 2. Anti-reward-hacking design

| Attack | Defense |
|--------|---------|
| Pattern-match correct adjusted EPS | Grounding (0.25) requires tool-retrieved evidence |
| Repeat polished answer to PM | Defense (0.20) + Follow-up C engagement failure flag |
| Invent footnote magnitudes | Hallucination penalty (−0.10) vs tool logs |
| Assert prior-year pattern without FY footnotes | Hallucination `unsupported_prior_year_claim` (0.5 penalty) + no judgment credit |
| Stall until timeout | Outcome capped at 0.5 if no `submit_recommendation` |

**Outcome (0.45) alone is insufficient** for maximum composite reward.

---

## 3. Verifier components

```
Reward = 0.45·Outcome + 0.25·Grounding + 0.20·Defense − 0.10·Hallucination
```

All four sub-scores exported per episode. See [dual_control_spec_v1.md](./dual_control_spec_v1.md).

| Component | Benchmark layer analog |
|-----------|------------------------|
| Outcome | L1 (binary) + L2 (judgment) |
| Grounding | L2 section recall + L3 citations |
| Defense | L2 (new — PM engagement) |
| Hallucination | L3 veto / penalty |

---

## 4. Calibration loop (separate from RL)

- 10–20% of episodes sampled for CFA adjudication
- Review LLM-judge scores on Outcome (judgment half) and Defense
- Target inter-rater κ ≥ 0.7
- Adjust judge prompts/thresholds — **does not train the agent**

---

## 5. Public vs private artifacts

| Shared with labs | Never public |
|------------------|--------------|
| Task brief, tool API, corpus excerpts | Gold keys, full PM branch logic |
| Sample trajectories (redacted) | Defense LLM-judge prompts |
| Methodology (this doc) | Expert adjudication sheets |

---

## 6. Reproducibility

- Fixed versioned corpus bundle per episode (`corpus/solaris_bundle_v1.json`)
- No live web retrieval
- Deterministic tool backend + calculator
- PM policy v1: scripted FSM (LLM paraphrase deferred to v1.1)

---

## 7. Demo package (P1 deliverable)

- [x] `runs/sample_trace_good.json` + score breakdown
- [x] `runs/sample_trace_partial.json` + score breakdown
- [x] `runs/sample_trace_timeout.json` + score breakdown
- [x] One-command: `python3 env_v1/scripts/run_episode.py --mode all`
- [x] Agent loop: scripted / mock / openai — see [AGENT_ADAPTERS.md](./AGENT_ADAPTERS.md)
- [x] First frontier run: GPT-4o composite **0.54**, fractures `SECTION_MISS` + `HALLUC_FILL` — [FRONTIER_RUNS.md](../runs/frontier/FRONTIER_RUNS.md)

See [ROADMAP.md](../../docs/ROADMAP.md) Phase P1.
