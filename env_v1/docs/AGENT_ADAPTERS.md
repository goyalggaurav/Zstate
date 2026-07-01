# Agent Adapters — env_v1 (P1-12)

**Status:** v1 — mock + OpenAI-compatible  
**Episode runner:** `env_v1/scripts/agent_loop.py`

---

## Recommendation (eng + lab)

| Choice | Verdict |
|--------|---------|
| **Pluggable adapter interface** | One `run_agent_episode()` loop; agents implement `next_action()` only |
| **First provider: OpenAI-compatible HTTP** | Works with OpenAI, Azure OpenAI, Together, Groq, local vLLM — one code path |
| **Anthropic native SDK** | Defer to v2 unless lab standardizes on Claude-only |
| **Cursor SDK / cloud agents** | Wrong tool for benchmark eval — use direct model API for reproducible traces |
| **Mock agent in CI** | Required — smoke tests must not need API keys |

**Do not** embed the PM or scorer inside the agent. The environment owns tool backend, PM FSM, and `score_episode.py`.

---

## Agent modes

| Mode | Use case | API key |
|------|----------|---------|
| `scripted` | Gold path replay, regression | No |
| `mock` | Offline weak agent (omit prior-year) | No |
| `repl` | Manual debugging | No |
| `openai` | Frontier model eval (P1-12) | `OPENAI_API_KEY` |

---

## OpenAI-compatible run

```bash
pip3 install -r env_v1/requirements-agent.txt   # certifi — macOS SSL fix

export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o          # optional
# export OPENAI_BASE_URL=https://...  # for Azure / compatible hosts

python3 env_v1/scripts/agent_loop.py \
  --agent openai \
  --model-id gpt-4o \
  --out env_v1/runs/frontier_run_001.json
```

Trace is schema-enriched (`trajectory_id`, `fractures`, `reward`) via `write_trace()`.

### Timeouts and retries

Long tool-calling turns can exceed 120s on slow networks. Defaults (override via env):

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_TIMEOUT_SECONDS` | `300` | Per-request read timeout |
| `OPENAI_MAX_RETRIES` | `3` | Retries on timeout / 429 / 5xx |

`run_frontier_batch.py` also retries failed episodes (`--run-retries 2`).

### macOS SSL error (`CERTIFICATE_VERIFY_FAILED`)

Common with python.org Python on Mac. Fix in order:

1. `pip3 install certifi` (or `pip3 install -r env_v1/requirements-agent.txt`)
2. Retry the agent command
3. If still failing: run **Install Certificates.command** from your Python app folder, e.g.  
   `open "/Applications/Python 3.14/Install Certificates.command"`

---

## Tool surface

Six functions map 1:1 to episode `allowed_tools`:

- Corpus: `get_filing`, `get_transcript`, `get_consensus`, `calculator` → `ToolBackend`
- Episode: `send_message_to_pm`, `submit_recommendation` → PM FSM + termination

PM replies are injected as `user` messages: `Portfolio Manager: ...`

---

## Next adapters (backlog)

| ID | Adapter | When |
|----|---------|------|
| P1-12b | `--agent anthropic` native tool use | Lab requests Claude-only |
| P1-12c | Batch runner `scripts/run_eval.py` | Multi-episode campaigns |
| P2 | Track A GOOGL single-turn adapter | Same tool pattern, no PM |

---

## Anti-patterns

- **Agent reads gold key** — never pass gold key into prompt
- **Scorer inside agent loop** — score after trace write only
- **Unlogged tool I/O** — every call must appear in `steps` + `tool_log`
