# Zstate Equity Research — Unified Backlog

**Version:** 0.5  
**Last updated:** July 2026 (SH-14 + P3-14 + P3-27; P3-22–26 architecture hardening)

Single backlog for **eval benchmark (Track A)**, **dual-control RL env (Track B)**, and **shared platform**. Priorities: **P0** (now) → **P4** (later).

Status key: `todo` | `in_progress` | `done` | `blocked` | `deferred`

---

## P0 — Foundation (now)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P0-01 | GOOGL footnote pilot — expert sign-off | A | done | Finance expert | Expert-reviewed 2026-07-01; see `GOOGL_GT_REVIEW.md` |
| P0-02 | env_v1 scaffold (tool backend, episode, PM FSM, scorer) | B | done | Eng | See `env_v1/` |
| P0-03 | Copy dual-control spec + flow diagram into repo | B | done | Eng | `env_v1/docs/` |
| P0-04 | gitignore `gold_keys/` + example template | B | done | Eng | `gold_keys.example/` |
| P0-05 | Solaris gold key (expert-authored) | B | done | Finance expert | Expert-reviewed 2026-07-01; `SOLARIS_GOLD_KEY_REVIEW.md` |
| P0-06 | Corpus manifest for 5 pilot tickers (EDGAR) | A | done | Eng | `benchmark_v0.1/corpus/corpus_manifest_v1.json` |
| P0-07 | Roadmap + backlog (this file) | Both | done | Eng | Unified planning |
| P0-08 | Name finance expert + associate | Both | done | Product | Gaurav Goyal (CFA L3 candidate) — lead + associate; see `EXPERT_CREDENTIALS.md` |

---

## P1 — Lab signal (weeks 4–8)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P1-01 | Solaris corpus bundle JSON (10-Q, transcript, consensus, prior 10-K) | B | done | Eng | `corpus/solaris_bundle_v1.json` — CFA review REV-03 |
| P1-02 | PM policy FSM v1 (opening, follow-up A/B/C) | B | done | Eng | `pm_policies/pm_v1.json` |
| P1-03 | `agent_loop.py` — scripted / mock / openai agents | B | done | Eng | See `env_v1/docs/AGENT_ADAPTERS.md` |
| P1-04 | `score_episode.py` — 4-component verifier | B | in_progress | Eng | Deterministic done; LLM-judge pending |
| P1-05 | Outcome checker — sale-leaseback binary exclude | B | done | Eng | In `score_episode.py` |
| P1-06 | Grounding checker — claims vs tool log | B | done | Eng | Doc ID hits in `score_episode.py` |
| P1-07 | Defense rubric + Follow-up C engagement flag | B | done | Finance expert + Eng | REV-04 expert-reviewed 2026-07-01 |
| P1-08 | Hallucination detector — facts not in tool outputs | B | done | Eng | Unsupported prior-year narrative without FY footnotes → `HALLUC_FILL` |
| P1-09 | Timeout rule — cap Outcome / zero Defense if no submit | B | done | Eng | In `score_episode.py` |
| P1-10 | 3 demo trajectories (good / partial / timeout) | B | done | Eng | `run_episode.py --mode all` |
| P1-11 | `METHODOLOGY_RL_ENV.md` — anti-hacking, calibration | B | done | Eng | v1.0 review-ready; lab demo package |
| P1-12 | One frontier model end-to-end run | B | done | Eng | GPT-4o run #001 — composite 0.59, `SECTION_MISS`; see `env_v1/runs/frontier/` |
| P1-12b | Frontier campaign — 3 seeds + summary | B | done | Eng | 4/4 gpt-4o runs; composite 0.5408 constant; see `frontier_campaign_v1.json` |
| P1-13 | Expert adjudication protocol (10–20% sample) | Both | todo | CFA | κ ≥ 0.7 on Outcome (judgment) + Defense |
| P1-14 | Solaris episode v1.1 — transcript distractor + pushover branch | B | done | Eng | CEO rhetoric vs Note 12; `follow_up_pushover`; failure modes `pushover`, `rhetoric_over_filing` |

---

## P2 — Credibility scale (weeks 6–12)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P2-01 | NFLX guidance drift task (Type F) | A | done | Associate | Pattern 1 rebuild; expert sign-off `NFLX_GT_REVIEW.md` 2026-07-02 |
| P2-02 | PEP or KO FX organic growth task (Type M) | A | done | Associate | `PEP_fx_organic_growth` expert-reviewed 2026-07-01; see `PEP_FX_GT_REVIEW.md` |
| P2-03 | AMZN footnote task (Type F) | A | done | Eng | `AMZN_footnote_reconciliation` — 4-section L2 path; pilot draft |
| P2-04 | Eval campaign — 2 models × core tasks × 3 runs | A | done | Eng | `gpt-4o` + `claude-sonnet-4-5` × GOOGL + PEP × 3; 12/12 composite 1.0; see `runs/pilot_eval_campaign_v1/` |
| P2-05 | Fracture report v0 | Both | done | Eng | `docs/FRACTURE_REPORT_v0.md` — frontier v1–v3 |
| P2-06 | Leaderboard v0 publish | A | done | Product | [LEADERBOARD_v0.md](../benchmark_v0.1/docs/LEADERBOARD_v0.md) — composite rank + FI + fracture delta |
| P2-07 | Trajectory JSONL schema — align A + B | Both | done | Eng | `schemas/trajectory_v1.json` |
| P2-08 | Transcript API trial (5 pilot names) | A | todo | Eng | Guidance tasks; see LATER-06 for NFLX EDGAR bundle ingest |

**Cap:** Do not expand beyond 3–5 MVD tasks until P1-10 demo trajectories exist. *(Cap lifted — P1-10 done; 4 tasks published. Complete P3-11/P3-12 before task #5.)*

### P2-04 sub-track (eval campaign)

| ID | Item | Status | Notes |
|----|------|--------|-------|
| P2-04a | Campaign scorer + contract stub | done | `run_benchmark_campaign.py`, `mock_agent_stub.py`, `contract_fixtures/` |
| P2-04b | Track A agent loop (scripted + mock) | done | `benchmark_agent_loop.py`; A2 gate passes L1 |
| P2-04c | Corpus bundles v1.1 + sectional retrieval | done | `section_registry`, `policy_notes`, canonical slug enforcement |
| P2-04d | Agent submission + L3 citation validator | done | `validate_agent_submission.py`; `_submission.json` contract fixtures |
| P2-04e | `score_benchmark_run.py` — L2/L3 v0 | done | Section recall from trace; composite median in campaign |
| P2-04f | OpenAI adapter + `--execute` on campaign | done | `agents/openai_benchmark_agent.py`; `--execute --agent scripted|openai` |
| P2-04g | **Live eval** — OpenAI mini 2×3 grid | done | `gpt-4o-mini` × GOOGL + PEP × 3 runs; 6/6 composite 1.0; `runs/pilot_eval_openai_mini_v1/` |
| P2-04h | Anthropic adapter + `--agent auto` routing | done | `claude-sonnet-4-5`; live 12/12 in `pilot_eval_campaign_v1` |
| P2-09 | **Discrimination eval** — eval_mode + L2 gold-path + L3 partial | done | Live 12/12; PEP composite 0.966; `CITE_HALLUC`×5; GOOGL still 1.0 — scorer validated, ranking deferred |
| P2-10 | **Harder L3 + 3rd task** — PEP distinct snippets; AMZN 4-section path | done | Live 18/18; PEP task median 0.881; `pilot_eval_3task_v1` |
| P2-11 | **Discrimination v2** — drop GOOGL headline; weighted per-model composite | done | `pilot_eval_discrimination_v2`; gpt-4o 0.932 vs claude 1.0 |
| P2-12 | **AMZN path hardening** — Note 8 required + FY2024 decoy slug | done | 5-section path; `compensation_disclosure`; `segment_financials_prior_year` decoy |
| P2-13 | **Universal archetypes** — `archetype_roles_v1.json` + `archetype_roles.py` | done | `F_exact`, `F_adjustment`, `M_organic`; decoy trap registry |
| P2-14 | **Path-role slugs** — migrate bundles/gold paths/tasks to role slugs (v1.2) | done | `segment_financials`, `narrative_organic`, `compensation_disclosure`, etc.; unified `verify_benchmark_l1.py` |
| P2-15 | **Legacy slug aliasing** — rescore old live traces without re-run | done | `legacy_section_slugs[]` on registry; L2/L3 + backend canonicalize |
| P2-16 | **AMZN expert sign-off** — `AMZN_GT_REVIEW.md` | done | Third published task expert-backed |
| P2-17 | **Jul 2026 eval write-up** — pilot report + fracture report Track A | done | `benchmark_v0.1/docs/PILOT_EVAL_JUL2026.md` |
| P2-18 | **GOOGL L3 hardening + headline policy** — distinct snippets; GOOGL out of headline | done | `l3_citation_rules` on GOOGL; `headline_tasks` on 3-task campaign |
| P2-19 | **NFLX expert sign-off** — Pattern 1 GT + `NFLX_GT_REVIEW.md` | done | Fourth published task; annual vs YTD pace archetype |
| P2-20 | **4-task eval campaign** — `pilot_eval_4task_v1` live + NFLX re-run | done | 24/24 scored; headline gpt-4o 0.817 vs claude 0.966; boolean submit fix |
| P3-08 | **Fracture registry SSOT** — `fracture_library_v1.json` + `fracture_registry.py` | done | L2/L3 central maps; L1 from gold_path + GT; verifiers migrated |
| P3-09 | **Synthetic L3 bait pilot** — decoy-only hallucination traps | done | NFLX decoy `synthetic_l3_bait` + validator isolation from required excerpts |
| P3-10 | **EDGAR excerpt provenance pins** — SHA-256 recompute in bundle validator | done | `excerpt_sha256` + manifest accession sync; full ingest remains LATER-06/SH-06 |

---

## P3 — Env v1.1 + benchmark scale (weeks 10–20)

### Architecture hardening (Jul 2026 review — before task #5)

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P3-11 | **`task_registry.py` SSOT** — manifest-driven task wiring | A | done | Eng | `task_registry.py`; `corpus_bundle` + `scripted_plan` in manifest; 3× bundle maps removed |
| P3-12 | **GT-native L1** — GOOGL + AMZN verifiers | A | done | Eng | GT-loaded verify; `verify_benchmark_l1.py` router + `l1_verify_argv()`; hardcoded constants removed |
| P3-13 | **Doc sync from manifest** | Both | done | Eng | Manual sync done; **P3-28** adds `sync_track_a_docs.py` automation |
| P3-14 | **Track B fracture registry** | B | done | Eng | `fracture_library_v1.json` env map; `score_episode.py` uses `fracture_registry` |
| P3-15 | **Synthetic L3 eval mode** | A | done | Eng | `synthetic_l3_eval` campaign flag; `synthetic_l3.py`; separate Synthetic L3 FI in leaderboard |
| P3-16 | **Task special-case cleanup** | A | done | Eng | `l1_verify_argv()`; mock agent generalized to all 5 published tasks via `mock_benchmark_agents.py` |
| P3-29b | **L3 AMZN/NFLX row/column anchors** | A | done | Eng | `metric_citation_anchors` on AMZN/NFLX gold paths; NFLX numeric_optional for derived metrics; billion/thousands numeric forms |
| P3-30 | **Archetype L1 consolidation** | A | done | Eng | AMZN `verification_schema` → `verify_footnote_exact`; dropped `verify_amzn_footnote_reconciliation.py` |
| P3-31 | **`scaffold_task.py`** | A | done | Eng | Archetype skeleton for task/GT/gold_path under `_scaffold/` |
| P3-32 | **Computed-metric L3 policy** | A | done | Eng | `computed_citations` in gold path; `submission_from_gt()` auto-builds computed citations |
| P3-33 | **Scripted plans NFLX/KO** | A | done | Eng | `nflx_good_plan.json`, `ko_good_plan.json`; publish gate requires scripted_plan |
| P3-34 | **Metric unit typing (L3)** | A | done | Eng | `infer_metric_unit` / `build_metric_units`; unit-aware `numeric_in_snippet` |
| P3-35 | **KO `reconciliation_bridge_total` rename (v0.2)** | A | deferred | Eng | Rename `segment_net_revenues_sum` → `reconciliation_bridge_total` (GT, task schema, fixtures, pinned runs, L3 rules). Expert-confirmed semantics 2026-07-02; defer to avoid destabilizing green pilot. Blast radius: schema + `pilot_eval_5task_v1` rescore |
| P3-28 | **`sync_track_a_docs.py`** | Both | done | Eng | Manifest-driven blocks in root README, benchmark README, ARCHITECTURE; `--check` in CI |
| P3-29 | **L3 citation hardening (9B)** | A | done | Eng | Archetype baselines + KO column/row anchors; `l3_citation_rules.py`; KO trap fixture |
| P3-17 | **Contract GT fixtures (new tasks)** | A | done | Eng | `l1_values_from_gt()` + `submission_from_gt()`; `GT_DERIVED_TASKS`; KO uses GT-only fixtures |
| P3-17b | **Contract GT fixtures (legacy + KO L1)** | A | done | Eng | L1 gold from `l1_values_from_gt()` for all 5 tasks; submission fixtures hand-maintained where computed metrics need distinct L3 citations |
| P3-18 | **KO_footnote_reconciliation — hardened template** | A | done | Associate | Published 2026-07-02; EDGAR elimination bridge; [KO_GT_REVIEW.md](./expert_drafts/KO_GT_REVIEW.md) |
| P3-20 | **Per-task submit metric schema fidelity** | A | done | Eng | F_exact GT-driven metric keys in `archetype_roles.py`; `validate_task_metrics` + tool_error retry; KO re-run post-fix (`pilot_eval_5task_v1`) |
| P3-21 | **Horizontal segment tables (KO Note 20)** | A | noted | Associate | **Horizontal layout adds real difficulty** — segments-as-columns vs vertical Note 10-style tables; filing-faithful, keep for discrimination. Not a scoring failure mode after P3-20; optional normalized row view deferred to LATER-06. |
| P3-22 | **`headline_eligible` manifest flag** | A | done | Eng | GOOGL `false`; PEP/AMZN/NFLX/KO explicit `true`; campaigns/leaderboard use `resolve_campaign_headline_tasks()` |
| P3-23 | **Publish gate (`validate_publish_task.py`)** | A | done | Eng | GT L1 verify, submit schema, contract fixture parity, L3 submission fixture |
| P3-24 | **Pin scored campaign report** | A | done | Eng | `manifest.pinned_campaign_report`; gitignore exception for `pilot_eval_5task_v1.json` only |
| P3-25 | **CI — smoke + validators (no live API)** | A | done | Eng | `.github/workflows/ci.yml` |
| P3-26 | **Doc sync (5-task pilot SSOT)** | A | done | Eng | Root README, benchmark README, smoke leaderboard assert |
| P3-27 | **Track A trajectory_v1 validation** | A | done | Eng | `shared/trace_utils.py`; validate on benchmark trace write |

**Gate:** P3 architecture hardening **complete for pilot**; **scale pass open** (P3-30–34 done). P3-03 (15 tasks) unblocked — scripted plan + publish gate per task. Full EDGAR ingest remains **LATER-06**.

### Env + catalog scale

| ID | Item | Track | Status | Owner | Notes |
|----|------|-------|--------|-------|-------|
| P3-01 | Guidance dispute dual-control episode (Scenario #2) | B | deferred | CFA + Eng | NFLX-style |
| P3-02 | Real-ticker earnings-quality episode (PEP/KO) | B | deferred | CFA | Authored excerpts |
| P3-03 | Scale MVD to 15 tasks (5 cos × 3 archetypes) | A | deferred | Associate | ≤6 hrs/task by task 5; **P3-11/P3-12 done** |
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
| SH-06 | Corpus service implementation | deferred | **Explore later** — implementation rolls into **LATER-06** (full EDGAR ingest pipeline) |
| SH-07 | Eval orchestrator (model adapters) | done | OpenAI + Anthropic + Gemini adapters; `pilot_eval_5task_v1` live |
| SH-08 | Calibration dataset (5 tasks, dual-rater) | todo | Both benchmark L2 and env Defense |
| SH-09 | Architecture + expert workflow docs | done | Jul 2026 |
| SH-10 | Trajectory schema v1 | done | `schemas/trajectory_v1.json` |
| SH-11 | Trace enrichment + fracture registry | done | `trace_utils.py`, `fracture_taxonomy_v1.json` |
| SH-12 | Smoke test harness | done | `scripts/smoke_test.py` — 35 checks |
| SH-13 | Manifest + bundle validators | done | `validate_manifest.py`, `validate_corpus_bundle.py` B3 |
| SH-14 | Shared runtime extract (Track A/B dedupe) | done | `shared/` — `safe_calc`, `llm_retry`, `trace_utils`; backends import shared |

---

## Explore later (explicitly not P0–P2)

| ID | Item | Track | Notes |
|----|------|-------|-------|
| LATER-01 | **Track A — EDGAR corpus full ingest** | A | Unlock met (4 published tasks + lab demo). **Implementation: LATER-06**; service wrapper: SH-06. Defer until P3-03 scale. |
| LATER-02 | Track A — transcript API (non-NFLX guidance tasks) | A | P2-08; vendor + IR fallback runbook. NFLX uses shareholder letter (no transcript). |
| LATER-06 | **Full EDGAR ingest pipeline** | A | **Single home for corpus automation** — `ingest_edgar_excerpt.py` (accession → slice → bundle + checksum), NFLX Q4 2024 letter + Q3 2025 10-Q verbatim in `nflx_q2q3_2025_bundle.json`, manifest `ingest_status` + `checksum_sha256`; extend to other pilot tickers. P3-10 excerpt SHA pins are interim. GT signed off — ingest does not block published status. Depends on P2-08 / SH-06. |
| LATER-03 | Track A — eval orchestrator (SH-07) | A | done | Adapters + `pilot_eval_campaign_v1` live run complete |
| LATER-04 | Frontier campaign v4 (v1.1.3 FSM validation) | B | Optional API run; start-index 7 |
| LATER-05 | Track A — model ranking / harder L3 thresholds | A | in_progress | **9B shipped** (P3-29/29b); scale pass (P3-30–34) done; pinned post-9B rescore in `pilot_eval_5task_v1.json`. Enable `synthetic_l3_eval` on next live campaign; 9A weight bump deferred |

---

## Explicitly deferred (do not pull into P0–P1)

- 45-company universe before 5-company proof
- FINRA linter on Type F forensics tasks
- Expert Workbench UI
- 14-week full platform Gantt
- Competing on “research note agent” breadth vs Anthropic templates
- Live web retrieval in env episodes (fixed bundle only)
- Full platform microservices (`docs/specs/*`) before 10 tasks — manifest + scripts remain MVD
- Merging Track A and B episode formats
- LLM-judge for benchmark L2 before SH-08 calibration set

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
| DONE-13 | P1-12 prep sprint (agent loop, trace normalize, smoke tests) | Jul 2026 |
| DONE-14 | First frontier run GPT-4o on Solaris v1.0 | Jul 2026 |
| DONE-15 | P1-08 unsupported prior-year hallucination detector | Jul 2026 |
| DONE-16 | GPT-4o frontier campaign (4 seeds, zero variance) | Jul 2026 |
| DONE-17 | Solaris v1.1 — transcript distractor + pushover PM branch (P1-14) | Jul 2026 |
| DONE-18 | Solaris v1.1.2 scorer tightenings + frontier v2 rescore | Jul 2026 |
| DONE-19 | Pilot corpus manifest (5 tickers) + PEP FX task draft (P0-06, P2-02) | Jul 2026 |
| DONE-20 | Frontier v3 live campaign + v1.1.3 FSM + OpenAI retry hardening | Jul 2026 |
| DONE-21 | Lab package: METHODOLOGY v1.0, FRACTURE_REPORT v0, REV-04 draft | Jul 2026 |
| DONE-22 | Expert credentials policy + Gaurav Goyal named (P0-08) | Jul 2026 |
| DONE-23 | P2-04a campaign scorer + agent output contract stub | Jul 2026 |
| DONE-24 | Week 0 hygiene — fracture taxonomy, validate_manifest, doc sync | Jul 2026 |
| DONE-25 | P2-04b/c Track A runtime + corpus v1.1 + sectional retrieval | Jul 2026 |
| DONE-26 | P2-04f OpenAI adapter + campaign `--execute` | Jul 2026 |
| DONE-27 | P2-04d L3 submission validator + citation fixtures | Jul 2026 |
| DONE-28 | P2-04e composite run scoring (L1+L2+L3) | Jul 2026 |
| DONE-29 | P2-04g OpenAI mini live eval (6/6, composite 1.0) + PEP L3 citation fix | Jul 2026 |
| DONE-30 | P2-04 live campaign — gpt-4o + claude-sonnet-4-5, 12/12 composite 1.0 | Jul 2026 |
| DONE-31 | P2-09 discrimination eval — eval_mode, L2 gold-path, L3 partial; live 12/12 | Jul 2026 |
| DONE-32 | P2-10 PEP distinct L3 + AMZN third task (4-section L2 path) | Jul 2026 |
| DONE-33 | P2-11 discrimination v2 + live 3-task eval (PEP separates models) | Jul 2026 |
| DONE-34 | P2-12 AMZN 5-section path + FY2024 decoy slug | Jul 2026 |
| DONE-35 | P3-20 per-task submit schema fidelity + KO eval re-run | Jul 2026 |
| DONE-36 | Gemini adapter + 5-task pilot campaign + pilot status brief export | Jul 2026 |

---

## How to use this backlog

1. **Weekly:** Pull only from P0/P1 unless env demo is shipped.  
2. **Lab meeting prep:** P1-10, P1-11, P1-04 must be `done`.  
3. **Investor / Zstate review:** P2-06 + roadmap Phase map.  
4. **Before task #5:** P3-11 → P3-12 → P3-13 (registry, GT L1, doc sync).  
5. **Update status** in this file when items complete; add new IDs sequentially.
