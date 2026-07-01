# Component Specifications — Target Platform

These specs describe the **full platform** (post-pilot). Current MVD implementations:

| Spec | Implemented as |
|------|----------------|
| task-registry | `benchmark_v0.1/tasks/*.json` |
| scoring-engine | `benchmark_v0.1/scripts/verify_*.py`, `env_v1/scripts/score_episode.py` |
| corpus-service | `env_v1/corpus/`, EDGAR manifests (planned) |
| eval-orchestrator | `env_v1/scripts/run_episode.py` (demo modes) |
| expert-workbench | `docs/expert_drafts/`, review workflow |

**MVD scope:** 15 tasks (Track A), 1 episode (Track B). Specs referencing 45 tasks = **v0.1b** scale.

| Spec | File |
|------|------|
| Corpus Service | [corpus-service.md](./corpus-service.md) |
| Task Registry | [task-registry.md](./task-registry.md) |
| Eval Orchestrator | [eval-orchestrator.md](./eval-orchestrator.md) |
| Scoring Engine | [scoring-engine.md](./scoring-engine.md) |
| Expert Workbench | [expert-workbench.md](./expert-workbench.md) |

Cross-track schemas: [schemas/trajectory_v1.json](../../schemas/trajectory_v1.json)
