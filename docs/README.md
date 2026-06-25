# Zstate Documentation

Equity Research Agent Benchmark — design and specifications.

## Share with Zstate

**Start here:** [Equity Research Agent Benchmark — Framework Proposal v0.1](./ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md)

This is the primary document for stakeholder review: executive summary, architecture, pilot scope, timeline, and deliverables.

## Detailed Task Backbone

**For exhaustive analyst workflow:** [Task Catalog Overview](./EQUITY_RESEARCH_BENCHMARK_TASK_CATALOG.md)

**All 185 task definitions:** [Full Task Definitions](./EQUITY_RESEARCH_TASK_DEFINITIONS.md)

Senior-analyst decomposition: SEC/IR data → 3-statement model → DCF / comps / LBO / SOTP / DDM → earnings & guidance → thesis → compliant memo. **184+ indexed micro-tasks** with dependencies, sector variants, and roadmap to full catalog coverage.

## Component Specifications

| Spec | Description |
|------|-------------|
| [Corpus Service](./specs/corpus-service.md) | Filings, transcripts (API + IR fallback), FX, section index |
| [Task Registry](./specs/task-registry.md) | 45 tasks, ground truth, gold trajectories, mandates |
| [Eval Orchestrator](./specs/eval-orchestrator.md) | Model-agnostic eval, tool sandbox, 3-run campaigns |
| [Scoring Engine](./specs/scoring-engine.md) | 3-layer rewards, FINRA + mandates, leaderboard |
| [Expert Workbench](./specs/expert-workbench.md) | CFA/MBA authoring, review, Layer 2 scoring |

## Status

- **Framework, task catalog & specs:** Complete (v0.1 draft)
- **Implementation:** Not started
