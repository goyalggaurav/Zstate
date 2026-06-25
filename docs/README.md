# Zstate Documentation

Equity Research Agent Benchmark — design and specifications.

## Share with Zstate

**Start here:** [Equity Research Agent Benchmark — Framework Proposal v0.1](./ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md)

This is the primary document for stakeholder review: executive summary, architecture, pilot scope, timeline, and deliverables.

## Component Specifications

| Spec | Description |
|------|-------------|
| [Corpus Service](./specs/corpus-service.md) | Filings, transcripts (API + IR fallback), FX, section index |
| [Task Registry](./specs/task-registry.md) | 45 tasks, ground truth, gold trajectories, mandates |
| [Eval Orchestrator](./specs/eval-orchestrator.md) | Model-agnostic eval, tool sandbox, 3-run campaigns |
| [Scoring Engine](./specs/scoring-engine.md) | 3-layer rewards, FINRA + mandates, leaderboard |
| [Expert Workbench](./specs/expert-workbench.md) | CFA/MBA authoring, review, Layer 2 scoring |

## Status

- **Framework & specs:** Complete (v0.1 draft)
- **Implementation:** Not started
