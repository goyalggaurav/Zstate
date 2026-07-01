# Zstate — Equity Research Agent Benchmark

Design-phase repository for **AlphaNote-Bench**: credentialed-expert equity research evals + dual-control RL environment.

## Start here

| Audience | Document |
|----------|----------|
| **Everyone** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Planning** | [docs/ROADMAP.md](docs/ROADMAP.md) · [docs/BACKLOG.md](docs/BACKLOG.md) |
| **Product / scope** | [Framework v0.2](docs/ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md) |
| **CFA expert review** | [docs/EXPERT_REVIEW_WORKFLOW.md](docs/EXPERT_REVIEW_WORKFLOW.md) |
| **Full docs index** | [docs/README.md](docs/README.md) |

## Implemented artifacts

| Track | Path | Status |
|-------|------|--------|
| **A — Eval benchmark** | [benchmark_v0.1/](benchmark_v0.1/) | GOOGL footnote pilot (pending CFA sign-off) |
| **B — RL environment** | [env_v1/](env_v1/) | Solaris dual-control demo (3 sample traces) |

## Quick commands

```bash
# Track A — verify GOOGL ground truth
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026

# Track B — generate demo trajectories
python3 env_v1/scripts/run_episode.py --mode all
```
