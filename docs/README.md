# Zstate Documentation

Equity Research Agent Benchmark — design, architecture, and specifications.

## Start here

| Doc | Audience | Purpose |
|-----|----------|---------|
| **[Architecture](./ARCHITECTURE.md)** | Eng + product | Canonical repo structure, tracks A/B/C, scoring map |
| **[Expert review workflow](./EXPERT_REVIEW_WORKFLOW.md)** | CFA + eng | Draft → review → publish handoff |
| **[Roadmap](./ROADMAP.md)** | Leadership | 12-month phases |
| **[Backlog](./BACKLOG.md)** | Team | Prioritized work items |

## Planning

| Doc | Purpose |
|-----|---------|
| **[Roadmap](./ROADMAP.md)** | Unified 12-month plan — eval benchmark + dual-control RL env + training export |
| **[Backlog](./BACKLOG.md)** | Prioritized work items (P0–P4) |

## Share with Zstate

**Start here:** [Equity Research Agent Benchmark — Framework Proposal v0.2 (Revised)](./ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md)

Revised MVD: **15 tasks**, 5 pilot companies, task types (F/M/C), honest 10-week timeline, lightweight pilot stack.

## Dual-control RL environment (Track B)

**Lab signal:** [env_v1/README.md](../env_v1/README.md)

- [Dual-control spec v1](../env_v1/docs/dual_control_spec_v1.md)
- [Flow diagram](../env_v1/docs/flow_diagram.mermaid)
- [RL methodology (draft)](../env_v1/docs/METHODOLOGY_RL_ENV.md)

## Detailed Task Backbone

**For exhaustive analyst workflow:** [Task Catalog Overview](./EQUITY_RESEARCH_BENCHMARK_TASK_CATALOG.md)

**All 185 task definitions:** [Full Task Definitions](./EQUITY_RESEARCH_TASK_DEFINITIONS.md)

Senior-analyst decomposition: SEC/IR data → 3-statement model → DCF / comps / LBO / SOTP / DDM → earnings & guidance → thesis → compliant memo. **184+ indexed micro-tasks** with dependencies, sector variants, and roadmap to full catalog coverage.

## Component Specifications

| Spec | Description |
|------|-------------|
| [Corpus Service](./specs/corpus-service.md) | Filings, transcripts (API + IR fallback), FX, section index |
| [Task Registry](./specs/task-registry.md) | Tasks, ground truth, gold trajectories, anti_patterns |
| [Eval Orchestrator](./specs/eval-orchestrator.md) | Model-agnostic eval, tool sandbox, 3-run campaigns |
| [Scoring Engine](./specs/scoring-engine.md) | 3-layer rewards, FINRA + mandates, leaderboard |
| [Expert Workbench](./specs/expert-workbench.md) | CFA/MBA authoring, review, Layer 2 scoring |

## Export deliverables

Word/PDF: [docs/export/](./export/)

## Status

- **Framework v0.2 (revised MVD):** Complete — 15 tasks, task types, honest timeline
- **Roadmap + backlog v0.3:** Unified planning (eval + RL env)
- **env_v1 scaffold:** Solaris v1.0 published; agent loop + PM heuristics (P1-12 prep)
- **Pilot task package:** GOOGL footnote reconciliation — **published** (CFA approved 2026-07-01)
