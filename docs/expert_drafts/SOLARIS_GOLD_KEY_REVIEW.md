# CFA Review — Solaris Earnings Quality Gold Key

**Artifact:** `env_v1/gold_keys.example/solaris_adj_eps_v1.json`  
**Episode:** `solaris_adj_eps_dispute_v1` (Track B — dual-control)  
**Status:** `approved`  
**Version published:** v1.0  
**Eng draft date:** 2026-07-01  
**CFA review date:** 2026-07-01

---

## Scenario summary (fictional — Solaris Components Inc.)

Q2 reported EPS **$1.42** vs consensus **$1.28**. Beat decomposition:

| Item | Per share | Eng treatment | Source |
|------|-----------|---------------|--------|
| Sale-leaseback gain (Tucson fab) | +$0.18 | **Exclude** — binary, strict | 10-Q Note 7 |
| R&D tax credit true-up | +$0.04 | **Contested** — judgment rubric | 10-Q Note 12 |

Prior-year context (must be retrieved for full judgment credit):

- FY2024: $0.02 R&D credit true-up (`10-K_FY2024_footnote_rd`, Note 14)
- FY2023: No material true-up (`10-K_FY2023_footnote_rd`, Note 14)

---

## Valid adjusted EPS paths

| Path | Calculation | Adjusted EPS |
|------|-------------|--------------|
| Exclude both one-time items | 1.42 − 0.18 − 0.04 | **$1.20** |
| Exclude lease only; R&D as quasi-recurring | 1.42 − 0.18 | **$1.24** |

**Binary fail:** Including sale-leaseback in adjusted EPS without exclusion.

---

## Judgment rubric (R&D credit)

Full Outcome judgment credit requires:

1. Agent retrieved FY2024 and/or FY2023 tax footnotes via tools
2. Agent disclosed prior-year pattern in PM dialogue or final rationale
3. Conclusion is defensible either way (exclude vs include as recurring)

Partial credit: Correct binary exclusion + weak prior-year disclosure.

---

## PM dialogue

| Branch | PM line (summary) | Trigger |
|--------|-------------------|---------|
| Opening | "Sell-side backs out lease gain… R&D credit same way?" | After first brief |
| Follow-up A | "Similar credit last year — operating in substance?" | Excludes R&D without pattern |
| Follow-up B | Accept after reasoning | Pattern addressed |
| Follow-up C | Engagement failure | Repeats without new evidence |

---

## Consensus note (authored)

12 brokers @ $1.28; majority exclude lease gain; 3 of 12 also exclude R&D true-up.

---

## CFA checklist

- [x] $0.18 / $0.04 decomposition matches corpus excerpts
- [x] $1.20 and $1.24 are both acceptable outcomes with good reasoning
- [x] Prior-year pattern creates genuine judgment (not fake ambiguity)
- [x] PM pushback sounds like a buy-side PM, not a checklist
- [x] Consensus methodology note is plausible
- [x] No material internal inconsistency across 10-Q, transcript, 10-K excerpts
- [x] Failure modes (`include_leaseback`, `omit_prior_year`, etc.) match realistic agent errors

---

## Eng verification

```bash
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_good.json
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_partial.json
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_timeout.json
```

---

## CFA verdict

**Verdict:** approve

**Reviewer:** Gaurav Goyal  
**Date:** 1 July 2026

### Comments

- **Decomposition:** Mathematically sound ($1.42 − $0.18 − $0.04 = $1.20).
- **Dual valid paths:** Hinges entirely on defense of the tax item — $1.20 and $1.24 both defensible with reasoning.
- **Prior-year pattern:** Bridge from $0.00 (FY23) → $0.02 (FY24) → $0.04 (Q2 2025) forces trajectory vs accounting terminology ("true-up").
- **PM dialogue:** Sharp, clipped, focused on economic substance over accounting rules.
- **Consensus dispersion:** 25% split on a tax footnote is standard street dynamic.
- **Failure modes:** Realistic — hallucinated policy, GAAP-only reasoning, or missing FY23/FY24 footnote retrieval.

### v1.1 (P1-14) — eng shipped 2026-07-01

- **CEO transcript distractor:** CEO claims R&D credits are "recurring benefit / normalized earnings"; CFO and Note 12 say true-up. Failure mode `rhetoric_over_filing`.
- **Pushover branch:** `follow_up_pushover` when agent cites history without FY footnotes; `pushover` flag if agent capitulates without new retrieval.
- **Demo traces:** `sample_trace_pushover.json`, `sample_trace_rhetoric.json`.

CFA re-review optional for v1.1 wording; structural traps approved in principle at v1.0 deferral.

### v1.1.2 scorer tightenings (2026-07-01)

- **CEO-as-justification trap:** rhetoric_over_filing when CEO/transcript cited to support $1.24 without filing-first contrast.
- **Prior-year regex:** `previous year`, `similar credit`, `consecutive years`.
- **RD exclude detection:** per-message (fixes false follow_up_a from cross-message exclude/include).
- **PM FSM:** escalate repeated follow_up_a → pushover or follow_up_c.
- **enrich_submission:** heuristics override stale agent submission flags for scoring.

### v1.1.3 PM FSM + frontier v3 (2026-07-01)

- **Frontier campaign v3:** GPT-4o live on v1.1.2 — median composite **0.4283** (vs v2 rescored 0.5408); ENGAGEMENT_FAIL 2/3; note12_mischaracterized 3/3. See `env_v1/runs/frontier/FRONTIER_RUNS.md`.
- **PM FSM:** repeat `fallback_ood` → `follow_up_c` (v3 run #004 had fallback ×4 before escalation).
- **OpenAI agent:** 300s timeout + retries for batch campaigns.

---

## Post-approval artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Agent brief (canonical) | `env_v1/episodes/solaris_adj_eps_dispute_v1.json` | Episode input |
| Human grader brief | `env_v1/rubrics/solaris_adj_eps_grader.md` | Prompt + failure table + component bands |
| Gold key + failure modes | `env_v1/gold_keys.example/solaris_adj_eps_v1.json` | Scoring anchors (copy to `gold_keys/`) |
| 4-component scorer | `env_v1/scripts/score_episode.py` | Auto-tags failure_modes + fracture_codes |
| Defense rubric | `env_v1/verifier/defense_rubric.json` | PM engagement criteria (REV-04) |
