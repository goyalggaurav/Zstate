# Zstate — Equity Research Agent Benchmark

Design-phase repository for **AlphaNote-Bench**: credentialed-expert equity research evals + dual-control RL environment.

## Start here

| Audience | Document |
|----------|----------|
| **Everyone** | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Planning** | [docs/ROADMAP.md](docs/ROADMAP.md) · [docs/BACKLOG.md](docs/BACKLOG.md) |
| **Product / scope** | [Framework v0.2](docs/ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md) |
| **CFA expert review** | [docs/EXPERT_REVIEW_WORKFLOW.md](docs/EXPERT_REVIEW_WORKFLOW.md) · [credentials](docs/EXPERT_CREDENTIALS.md) |
| **Full docs index** | [docs/README.md](docs/README.md) |

## Implemented artifacts

| Track | Path | Status |
|-------|------|--------|
| **A — Eval benchmark** | [benchmark_v0.1/](benchmark_v0.1/) | GOOGL + PEP published (expert-reviewed 2026-07-01) |
| **B — RL environment** | [env_v1/](env_v1/) | Solaris v1.0 published + agent loop |

## Quick commands

```bash
# Smoke test (Track A L1 + Track B scorer + scripted agent)
python3 scripts/smoke_test.py

# Track A — verify GOOGL ground truth
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026

# Track B — demo trajectories (schema-enriched traces)
python3 env_v1/scripts/run_episode.py --mode all

# Track B — scripted agent (P1-12 prep)
python3 env_v1/scripts/agent_loop.py --agent scripted \
  --plan env_v1/examples/agents/solaris_good_plan.json

# Track B — mock weak agent (offline, no API key)
python3 env_v1/scripts/agent_loop.py --agent mock

# Track B — frontier model batch (requires OPENAI_API_KEY)
python3 scripts/run_frontier_batch.py --model-id gpt-4o --seeds 3 --start-index 2
```
