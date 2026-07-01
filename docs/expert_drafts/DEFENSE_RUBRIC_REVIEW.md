# CFA Review — Defense Rubric (REV-04)

**Artifact:** `env_v1/verifier/defense_rubric.json`  
**Verifier weights:** `env_v1/verifier/weights.json` → `defense` section  
**Status:** `pending_cfa_review`  
**Eng draft date:** 2026-07-01  
**CFA review date:** _pending_

---

## Eng summary

Defense scores **PM engagement quality** under scripted pushback — separate from Outcome (adjusted EPS) and Grounding (doc retrieval). Current implementation uses **deterministic heuristics** aligned to this rubric; LLM-judge deferred until CFA approves criteria.

**Formula weight:** Defense = **0.20** of composite (0.45 Outcome + 0.25 Grounding + 0.20 Defense − 0.10 Hallucination).

**Hard overrides (already in scorer):**

| Condition | Defense score |
|-----------|---------------|
| Follow-up C + `engagement_failure` flag | **0.0** |
| `pushover` flag (capitulate without retrieval) | **≤ 0.35** |
| Heuristic engaged (substantive PM response + evidence) | **0.85** (default pass band) |

---

## Rubric criteria (from JSON)

| ID | Weight | Pass | Fail |
|----|--------|------|------|
| `addresses_pm_question` | 35% | Direct answer to PM's latest challenge with new analysis or cited evidence | Deflect, change subject, ignore specific point |
| `cites_retrieved_evidence` | 30% | References note/table/amount from tool outputs | Assertion-only, no link to retrieved excerpts |
| `revises_when_warranted` | 20% | Updates EPS or classification when PM surfaces valid prior-year pattern | Holds initial number despite contradictory footnotes |
| `no_empty_repetition` | 15% | Each PM turn gets materially new content | Follow-up C — semantic repetition without new evidence |

---

## Frontier v3 evidence (why this rubric matters)

GPT-4o v3 live runs (`frontier_gpt-4o_004`–`006`):

| Run | Defense | What happened |
|-----|---------|---------------|
| #004 | **0.0** | Repeated filing summary 4× on `fallback_ood`; Follow-up C fired; FY2024 retrieved late |
| #005 | 0.85 | Engaged verbally but never pulled prior-year footnotes; invalid EPS $1.28 |
| #006 | **0.0** | Follow-up C engagement failure; no prior-year retrieval |

**Takeaway:** Correct EPS ($1.24) does not rescue defense. Rubric should feel fair to a human PM listening to these trajectories.

---

## CFA checklist

- [ ] Criteria weights (35/30/20/15) reflect PM priorities for earnings-quality defense
- [ ] `addresses_pm_question` — would you score run #004 agent responses as failing this?
- [ ] `cites_retrieved_evidence` — is tool-linked citation required, or is note number without quote sufficient?
- [ ] `revises_when_warranted` — when should agent move from $1.24 to $1.20 after FY footnotes?
- [ ] `no_empty_repetition` — is 0.85 heuristic too generous for run #005 (engaged but no FY pull)?
- [ ] Follow-up C zero override is appropriate (defense = 0 regardless of final EPS)
- [ ] Pushover cap 0.35 is appropriate for capitulation without retrieval
- [ ] Rubric is usable for 10–20% adjudication sample (P1-13)

---

## Scoring implementation note (Eng)

Current scorer (`score_episode.py`) uses heuristics, not weighted rubric sub-scores. Post-approval options:

1. Keep heuristics mapped to rubric IDs (minimal change)
2. Add LLM-judge per criterion (P1-04 remainder) after κ calibration

CFA approval of **criteria intent** unblocks both paths.

---

## Sign-off

**Approve when:** checklist complete; any weight or override changes recorded in `defense_rubric.json` + `weights.json`.

| Reviewer | Date | Status |
|----------|------|--------|
| CFA | | pending |
| Eng | 2026-07-01 | draft submitted |
