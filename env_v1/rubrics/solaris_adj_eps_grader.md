# Grader Brief — Solaris Adjusted EPS Dispute

**Episode ID:** `solaris_adj_eps_dispute_v1` (Track B — dual-control)  
**Canonical brief:** `env_v1/episodes/solaris_adj_eps_dispute_v1.json` → `brief.text`  
**Gold key:** `env_v1/gold_keys.example/solaris_adj_eps_v1.json` (copy to `gold_keys/` locally)  
**Score script:** `env_v1/scripts/score_episode.py`  
**CFA sign-off:** `docs/expert_drafts/SOLARIS_GOLD_KEY_REVIEW.md` (pending)

---

## Agent brief (summary)

Solaris Components (SLRS) reported Q2 EPS **$1.42** vs consensus **$1.28**. PM wants adjusted EPS reflecting underlying earnings quality.

1. Retrieve filing, transcript, consensus via tools  
2. Classify one-time vs recurring beat components  
3. Brief PM via `send_message_to_pm`  
4. Respond to pushback; re-query if needed  
5. Submit via `submit_recommendation` (turn budget: 8)

---

## Composite reward (4 components)

```
Reward = 0.45·Outcome + 0.25·Grounding + 0.20·Defense − 0.10·Hallucination
```

Report **component sub-scores**, not composite alone.

| Component | What it measures |
|-----------|------------------|
| **Outcome** | Binary sale-leaseback exclusion + judgment on R&D credit treatment |
| **Grounding** | Required doc retrievals (10-Q Q2, FY2024/FY2023 R&D footnotes) |
| **Defense** | PM engagement quality (Follow-up C = zero) |
| **Hallucination** | Claims in messages not supported by tool outputs |

---

## Beat decomposition (corpus)

| Item | Per share | Source | Eng treatment |
|------|-----------|--------|---------------|
| Sale-leaseback gain (Tucson fab) | +$0.18 | 10-Q Note 7 | **Exclude** — binary strict |
| R&D tax credit true-up | +$0.04 | 10-Q Note 12 | **Contested** — judgment rubric |

**Prior-year pattern (required for full Outcome judgment credit):**

- FY2024: $0.02 R&D credit true-up (`10-K_FY2024_footnote_rd`)
- FY2023: No material true-up (`10-K_FY2023_footnote_rd`)

---

## Valid adjusted EPS paths

| Path | Calculation | Adjusted EPS |
|------|-------------|--------------|
| Exclude both one-time items | 1.42 − 0.18 − 0.04 | **$1.20** |
| Exclude lease only; R&D quasi-recurring | 1.42 − 0.18 | **$1.24** |

**Binary fail:** Include sale-leaseback in adjusted EPS without exclusion (`sale_leaseback_excluded: false` or adj ≈ $1.42).

---

## Failure modes (primary traps)

| ID | Label | Signature | Fracture code | Typical Outcome |
|----|-------|-----------|---------------|-----------------|
| `include_leaseback` | Include lease gain | adj ≈ 1.42 or `sale_leaseback_excluded: false` | `OUTCOME_FAIL` | ~0.0–0.25 |
| `omit_prior_year` | Skip prior-year footnotes | Missing FY2024/FY2023 retrievals | `SECTION_MISS` | Grounding ↓; judgment capped |
| `engagement_failure` | PM Follow-up C | `pm_flags: engagement_failure` | `ENGAGEMENT_FAIL` | Defense = 0 |
| `timeout` | No submit in budget | `termination: timeout`, not submitted | `TIMEOUT` | Outcome capped 0.5 |
| `invalid_adjusted_eps` | Wrong math after exclusions | adj not in {1.20, 1.24} with lease excluded | `OUTCOME_FAIL` | Partial |

The score script auto-tags `failure_modes` and `fracture_codes` on every trace.

---

## PM dialogue branches

| Branch | PM challenge | Trigger |
|--------|--------------|---------|
| Opening | R&D credit treated same as sell-side? | After first agent message |
| Follow-up A | Prior-year credit — operating in substance? | Excludes R&D without pattern |
| Follow-up B | Accept after reasoning | Pattern addressed |
| Follow-up C | Engagement failure | Repetition without new evidence |

---

## Demo traces

```bash
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_good.json
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_partial.json
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_timeout.json
```

Expected composites (approx): good **0.88**, partial **0.42**, timeout **0.25**.
