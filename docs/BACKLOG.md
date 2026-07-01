# Zstate Equity Research — Unified Backlog

**Version:** 0.3  
**Last updated:** July 2026  

Single backlog for **eval benchmark (Track A)**, **dual-control RL env (Track B)**, and **shared platform**. Priorities: **P0** (now) → **P4** (later).

Status key: `todo` | `in_progress` | `done` | `blocked` | `deferred`

---

## P0 — Foundation (now)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P0-01 | GOOGL footnote pilot — expert sign-off | A | done | CFA | Approved 2026-07-01; see `GOOGL_GT_REVIEW.md` + `rubrics/GOOGL_footnote_reconciliation_grader.md` |
| P0-02 | env_v1 scaffold (tool backend, episode, PM FSM, scorer) | B | done | Eng | See `env_v1/` |
| P0-03 | Copy dual-control spec + flow diagram into repo | B | done | Eng | `env_v1/docs/` |
| P0-04 | gitignore `gold_keys/` + example template | B | done | Eng | `gold_keys.example/` |
| P0-05 | Solaris gold key (expert-authored) | B | done | CFA | v1.0 approved 2026-07-01; `SOLARIS_GOLD_KEY_REVIEW.md` |
| P0-06 | Corpus manifest for 5 pilot tickers (EDGAR) | A | todo | Eng | Feeds Track A tasks |
| P0-07 | Roadmap + backlog (this file) | Both | done | Eng | Unified planning |
| P0-08 | Name CFA lead + associate | Both | todo | Product | Binding constraint |

---

## P1 — Lab signal (weeks 4–8)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P1-01 | Solaris corpus bundle JSON (10-Q, transcript, consensus, prior 10-K) | B | done | Eng | `corpus/solaris_bundle_v1.json` — CFA review REV-03 |
| P1-02 | PM policy FSM v1 (opening, follow-up A/B/C) | B | done | Eng | `pm_policies/pm_v1.json` |
| P1-03 | `run_episode.py` — agent adapter + 8-turn budget | B | in_progress | Eng | Demo modes done; real agent + turn enforce pending |
| P1-04 | `score_episode.py` — 4-component verifier | B | in_progress | Eng | Deterministic done; LLM-judge pending |
| P1-05 | Outcome checker — sale-leaseback binary exclude | B | done | Eng | In `score_episode.py` |
| P1-06 | Grounding checker — claims vs tool log | B | done | Eng | Doc ID hits in `score_episode.py` |
| P1-07 | Defense rubric + Follow-up C engagement flag | B | pending_cfa_review | CFA + Eng | `defense_rubric.json` + REV-04 |
| P1-08 | Hallucination detector — facts not in tool outputs | B | in_progress | Eng | Basic pattern match; needs hardening |
| P1-09 | Timeout rule — cap Outcome / zero Defense if no submit | B | done | Eng | In `score_episode.py` |
| P1-10 | 3 demo trajectories (good / partial / timeout) | B | done | Eng | `run_episode.py --mode all` |
| P1-11 | `METHODOLOGY_RL_ENV.md` — anti-hacking, calibration | B | in_progress | Eng | Draft exists; finalize for lab |
| P1-12 | One frontier model end-to-end run | B | todo | Eng | First fracture data from env |
| P1-13 | Expert adjudication protocol (10–20% sample) | Both | todo | CFA | κ ≥ 0.7 on Outcome (judgment) + Defense |
| P1-14 | Solaris episode v1.1 — transcript distractor + pushover branch | B | todo | CFA + Eng | CEO rhetoric vs Note 12; `follow_up_pushover`; failure modes `pushover`, `rhetoric_over_filing`. Forward P/E out of scope — separate task |

---

## P2 — Credibility scale (weeks 6–12)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P2-01 | NFLX guidance drift task (Type F) | A | todo | Associate | Maps to env Scenario #2 later |
| P2-02 | PEP or KO FX organic growth task (Type M) | A | todo | Associate | Third MVD archetype |
| P2-03 | AMZN footnote task (Type F) | A | deferred | Associate | After 3 core tasks |
| P2-04 | Eval campaign — 2 models × core tasks × 3 runs | A | todo | Eng | Median aggregation |
| P2-05 | Fracture report v0 | Both | todo | Eng | ≥8 codes; include `PM_OOD` |
| P2-06 | Leaderboard v0 publish | A | todo | Product | Not the lab headline |
| P2-07 | Trajectory JSONL schema — align A + B | Both | done | Eng | `schemas/trajectory_v1.json` |
| P2-08 | Transcript API trial (5 pilot names) | A | todo | Eng | Guidance tasks |

**Cap:** Do not expand beyond 3–5 MVD tasks until P1-10 demo trajectories exist.

---

## P3 — Env v1.1 + benchmark scale (weeks 10–20)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P3-01 | Guidance dispute dual-control episode (Scenario #2) | B | deferred | CFA + Eng | NFLX-style |
| P3-02 | Real-ticker earnings-quality episode (PEP/KO) | B | deferred | CFA | Authored excerpts |
| P3-03 | Scale MVD to 15 tasks (5 cos × 3 archetypes) | A | deferred | Associate | ≤6 hrs/task by task 5 |
| P3-04 | LLM-judge calibration loop — adjust thresholds | B | deferred | CFA | After 20+ env runs |
| P3-05 | PM policy v2 — optional LLM paraphrase on FSM | B | deferred | Eng | After branch miss metrics |
| P3-06 | Add `earnings_quality_dispute` to task catalog | Both | deferred | Product | New archetype |
| P3-07 | Expert Workbench (lightweight) | Both | deferred | Eng | JSON + sheets until needed |

---

## P4 — Full catalog & platform (months 6–12)

| ID | Item | Track | Status | Notes |
|----|------|-------|--------|-------|
| P4-01 | MVD v0.1b — 45 tasks, 15 companies | A | deferred | After templates proven |
| P4-02 | 3-statement model task bundles (v0.2) | A | deferred | Type M expansion |
| P4-03 | DCF + comps + market data tier (v0.3) | A | deferred | Bloomberg/Refinitiv gate |
| P4-04 | Type C initiation memo (v0.5) | A | deferred | FINRA + market data |
| P4-05 | Thesis pushback env (Scenario #3) | B | deferred | Highest reward-hacking risk |
| P4-06 | Long-horizon Toolathlon-style env | B | deferred | After real trajectories captured |
| P4-07 | Full 5-service platform per specs | Both | deferred | Post-pilot |
| P4-08 | 185 tasks at full definition depth | A | deferred | Internal north star only |
| P4-09 | Trajectory dataset v1 (curated SFT/RL export) | C | deferred | Zstate Phase 2 product |
| P4-10 | Reward model training on 3/4-layer signals | C | deferred | Zstate Phase 3 |

---

## Shared infrastructure (cross-track)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| SH-01 | Fracture taxonomy maintenance | done | Framework doc; extend for env |
| SH-02 | Gold path + anti_patterns schema | done | GOOGL pilot reference |
| SH-03 | L1 Python verification pattern | done | Reuse in Outcome checker |
| SH-04 | Component specs (corpus, registry, eval, scoring) | done | Target architecture; implement lightweight first |
| SH-05 | Word/PDF export generator | done | Stakeholder docs |
| SH-06 | Corpus service implementation | todo | EDGAR + section index |
| SH-07 | Eval orchestrator (model adapters) | todo | Shared by A and B |
| SH-08 | Calibration dataset (5 tasks, dual-rater) | todo | Both benchmark L2 and env Defense |
| SH-09 | Architecture + expert workflow docs | done | Jul 2026 |
| SH-10 | Trajectory schema v1 | done | `schemas/trajectory_v1.json` |

---

## Explicitly deferred (do not pull into P0–P1)

- 45-company universe before 5-company proof
- FINRA linter on Type F forensics tasks
- Expert Workbench UI
- 14-week full platform Gantt
- Competing on “research note agent” breadth vs Anthropic templates
- Live web retrieval in env episodes (fixed bundle only)

---

## Done (archive)

| ID | Item | Completed |
|----|------|-----------|
| DONE-01 | Framework v0.2 (15-task MVD, task types F/M/C) | Jun 2025 |
| DONE-02 | 185-task catalog + definitions index | Jun 2025 |
| DONE-03 | GOOGL footnote pilot package (draft GT) | Jun 2025 |
| DONE-04 | Export docs (Word/PDF) | Jun 2025 |
| DONE-05 | Gold trajectory RL signal + anti_patterns elevation | Jun 2025 |
| DONE-06 | Type C v0.5 deferral rationale (market data) | Jun 2025 |
| DONE-07 | Unified roadmap + backlog | Jul 2026 |
| DONE-09 | Architecture v1 + expert review workflow | Jul 2026 |
| DONE-10 | 3 demo trajectories (good/partial/timeout) | Jul 2026 |
| DONE-11 | CFA review drafts (GOOGL + Solaris) | Jul 2026 |
| DONE-12 | Trajectory schema v1 + benchmark manifest | Jul 2026 |

---

## How to use this backlog

1. **Weekly:** Pull only from P0/P1 unless env demo is shipped.  
2. **Lab meeting prep:** P1-10, P1-11, P1-04 must be `done`.  
3. **Investor / Zstate review:** P2-06 + roadmap Phase map.  
4. **Update status** in this file when items complete; add new IDs sequentially.
