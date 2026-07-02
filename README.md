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
<!-- MANIFEST:SYNC:START pilot_summary -->
| **A — Eval benchmark** | [benchmark_v0.1/](benchmark_v0.1/) | **5 published tasks** (GOOGL, PEP, AMZN, NFLX, KO) — expert-reviewed Jul 2026 |
<!-- MANIFEST:SYNC:END pilot_summary -->
| **A — Leaderboard** | [LEADERBOARD_v0.md](benchmark_v0.1/docs/LEADERBOARD_v0.md) | `pilot_eval_5task_v1` — headline excludes GOOGL ceiling |
| **B — RL environment** | [env_v1/](env_v1/) | Solaris v1.1 + frontier campaign |

Published tasks are listed in [benchmark_v0.1/manifest.json](benchmark_v0.1/manifest.json) (source of truth).

## Quick commands

```bash
# Smoke test (35 checks — Track A L1/L2/L3 + Track B scorer)
python3 scripts/smoke_test.py

# Track A — unified L1 verify (any published task)
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task GOOGL_footnote_reconciliation
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task NFLX_guidance_drift

# Track A — score campaign + regenerate leaderboard (uses pinned report by default)
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_5task_v1.json
python3 benchmark_v0.1/scripts/generate_leaderboard.py

# Track B — demo trajectories (schema-enriched traces)
python3 env_v1/scripts/run_episode.py --mode all

# Track B — scripted agent
python3 env_v1/scripts/agent_loop.py --agent scripted \
  --plan env_v1/examples/agents/solaris_good_plan.json

# Track B — frontier model batch (requires OPENAI_API_KEY)
python3 scripts/run_frontier_batch.py --model-id gpt-4o --seeds 3 --start-index 2
```
