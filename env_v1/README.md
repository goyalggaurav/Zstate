# env_v1 — Dual-Control RL Environment

AlphaNote-Bench **Track B**: tau2-bench-style analyst + PM simulator with 4-component composite reward.

**Lab pitch:** Runnable environment with exposed verifier — not a single-turn leaderboard.

## Quick start

```bash
# Smoke test (full repo)
python3 scripts/smoke_test.py

# Score a sample trace (deterministic components)
python3 env_v1/scripts/score_episode.py --trace env_v1/runs/sample_trace_good.json

# Generate demo trajectories (good / partial / timeout / pushover / rhetoric)
python3 env_v1/scripts/run_episode.py --mode all

# Scripted agent loop (P1-12 prep — replay JSON plan)
python3 env_v1/scripts/agent_loop.py --agent scripted \
  --plan env_v1/examples/agents/solaris_good_plan.json

# Mock weak agent (offline — no API key)
python3 env_v1/scripts/agent_loop.py --agent mock

# Frontier model (OpenAI-compatible — see docs/AGENT_ADAPTERS.md)
# export OPENAI_API_KEY=...
# python3 env_v1/scripts/agent_loop.py --agent openai --model-id gpt-4o \
#   --out env_v1/runs/frontier/frontier_gpt4o_002.json

# Batch frontier campaign (3 seeds → frontier_campaign_v1.json)
# python3 scripts/run_frontier_batch.py --model-id gpt-4o --seeds 3 --start-index 2

# Interactive manual agent (REPL)
python3 env_v1/scripts/agent_loop.py --agent repl
```

## Layout

```
env_v1/
├── manifest.json
├── docs/
│   ├── dual_control_spec_v1.md      # Full environment spec
│   ├── flow_diagram.mermaid         # Reward generation flow
│   └── METHODOLOGY_RL_ENV.md        # Lab-facing methodology (draft)
├── episodes/
│   └── solaris_adj_eps_dispute_v1.json
├── corpus/
│   └── solaris_bundle_v1.json       # Fixed excerpts (public-safe)
├── pm_policies/
│   └── pm_v1.json                   # PM branching FSM (public-safe brief)
├── verifier/
│   ├── weights.json
│   └── defense_rubric.json
├── gold_keys.example/               # Template — copy to gold_keys/ locally
│   └── solaris_adj_eps_v1.json
├── gold_keys/                       # GITIGNORED — expert private artifacts
├── scripts/
│   ├── tool_backend.py
│   ├── run_episode.py      # Demo trajectories
│   ├── agent_loop.py       # Scripted + REPL agent (P1-12 prep)
│   ├── pm_features.py      # PM FSM hint extraction
│   ├── trace_utils.py      # trajectory_v1 enrichment
│   └── score_episode.py
├── examples/agents/        # Scripted agent plans
└── runs/                            # Episode traces + scores
    └── frontier/                    # Frontier campaign index + FRONTIER_RUNS.md
```

## Gold keys (private)

Copy `gold_keys.example/` → `gold_keys/` locally. **Never commit** `gold_keys/`.

## Relation to benchmark_v0.1 (Track A)

| Track A (`benchmark_v0.1/`) | Track B (`env_v1/`) |
|-----------------------------|---------------------|
| Single-turn Type F/M tasks | Multi-turn dual-control |
| 3-layer L1/L2/L3 reward | 4-component composite reward |
| Real SEC filings (GOOGL pilot) | Solaris fictional bundle v1 |
| Public leaderboard | Private env + verifier for labs |

See [docs/ROADMAP.md](../docs/ROADMAP.md) and [docs/BACKLOG.md](../docs/BACKLOG.md).
