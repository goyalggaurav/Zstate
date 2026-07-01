# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks** across 5 companies; **2 published** tasks (Type F + Type M).

## Corpus (P0-06)

Pilot registry for **GOOGL, AMZN, NFLX, PEP, KO** — EDGAR metadata + SEC URLs. Full text ingest deferred to SH-06.

```bash
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

Manifest: [corpus/corpus_manifest_v1.json](./corpus/corpus_manifest_v1.json)

Task bundles (redacted excerpts for agent runs): [corpus/googl_q1_2026_bundle.json](./corpus/googl_q1_2026_bundle.json), [corpus/pep_fy2025_bundle.json](./corpus/pep_fy2025_bundle.json)

```bash
python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --all
```

Contract: [docs/CORPUS_BUNDLE_CONTRACT.md](./docs/CORPUS_BUNDLE_CONTRACT.md)

---

## Published tasks

| Task | Type | Period | Status |
|------|------|--------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | **Q1 2026** (10-Q filed 2026-04-30) | **Published** (expert-reviewed 2026-07-01) |
| [PEP_fx_organic_growth](./tasks/PEP_fx_organic_growth.json) | M — Modeling | **FY2025** (10-K filed 2026-02-03) | **Published** (expert-reviewed 2026-07-01) |
| [AMZN_footnote_reconciliation](./tasks/AMZN_footnote_reconciliation.json) | F — Forensics | **FY2025** (10-K filed 2026-02-06) | **Published** (pilot draft) |

### GOOGL — footnote reconciliation

Reconcile **Q1 2026** reportable segment revenues to consolidated total revenue. The trap: agents sum Google Services + Google Cloud + Other Bets (**$110,076M**) and miss **hedging gains (losses) of $(180)M** — a **loss**, not a gain. Note 15 states hedging is **not allocated to reportable segments**.

### PEP — FX organic growth

Constant-currency organic revenue growth for **EMEA** and **LatAm Foods** via MD&A additive decomposition (`reported − FX = organic`) — not WAE rebuild (FY2025 10-K has no FX rate table). Traps: reporting GAAP growth as organic CC, wrong segment, wrong period.

---

## Eval campaign (P2-04)

Config: [campaigns/pilot_eval_campaign_v1.json](./campaigns/pilot_eval_campaign_v1.json) — 2 models × 2 published tasks × 3 runs.

```bash
# Gold-fixture smoke (verify + median aggregation)
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py --bootstrap-fixtures

# Execute scripted agents (CI / offline — no API key)
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py --execute --agent scripted

# Execute live agents (requires API keys; routes OpenAI vs Anthropic by model id)
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_campaign_v1.json \
  --execute --agent auto

# OpenAI-only or Anthropic-only subsets
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --execute --agent openai --models gpt-4o
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --execute --agent anthropic --models claude-sonnet-4-5

# Score existing agent outputs on disk
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py
```

Output: [runs/pilot_eval_campaign_v1/pilot_eval_campaign_v1.json](./runs/pilot_eval_campaign_v1/pilot_eval_campaign_v1.json) — includes `composite_score_median` per campaign.

**Discrimination campaign (P2-09):** [campaigns/pilot_eval_discrimination_v1.json](./campaigns/pilot_eval_discrimination_v1.json) sets `"eval_mode": true` (generic citation rules, no task-specific examples) and uses L2 gold-path scoring (section recall + access order + tool coverage) plus L3 partial credit on citations.

**Three-task campaign (P2-10):** [campaigns/pilot_eval_3task_v1.json](./campaigns/pilot_eval_3task_v1.json) adds `AMZN_footnote_reconciliation` with a **4-section ordered gold path** (policy → Note 10 → income statement → MD&A International). PEP L3 now requires **distinct snippets per metric** (`l3_citation_rules.distinct_snippets_required`).

**Live results (Jul 2026):** 18/18 runs (`gpt-4o` + `claude-sonnet-4-5` × 3 tasks × 3). Headline composite median **1.0** — GOOGL/AMZN still at ceiling. **PEP separates models:** gpt-4o composite **0.864** (L3 0.32, duplicate MD&A row citations + halluc snippets); claude median **1.0** (one run 0.898 on duplicate snippet). Fractures: `CITE_HALLUC`×3, `CITE_BROAD`×4. Full report: [runs/pilot_eval_3task_v1/pilot_eval_3task_v1.json](./runs/pilot_eval_3task_v1/pilot_eval_3task_v1.json).

**Discrimination v2 (P2-11):** [campaigns/pilot_eval_discrimination_v2.json](./campaigns/pilot_eval_discrimination_v2.json) drops GOOGL from the headline and reports **task-weighted per-model composite** (`weighted_composite_by_model`). Rescore existing 3-task runs without new API calls:

```bash
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_discrimination_v2.json
```

**AMZN path hardening (P2-12):** Five-section gold path adds required `stock_compensation_note` (Note 8) between policy and Note 10, plus optional decoy slug `note_10_prior_year` (FY2024 column only). Prior live runs that skipped Note 8 score lower on L2 section recall when rescored — discrimination v2 weighted composite shifts to **gpt-4o 0.885 vs claude 0.953** (was 0.932 vs 1.0).

```bash
export BENCHMARK_RUN_DELAY_SECONDS=3
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_3task_v1.json \
  --execute --agent auto
```

Single-run composite (L1 verify + L2 gold-path + L3 submission):

```bash
python3 benchmark_v0.1/scripts/score_benchmark_run.py \
  --task GOOGL_footnote_reconciliation \
  --agent-output path/to/run.json \
  --trace path/to/run_trace.json \
  --submission path/to/run_submission.json
```

`--execute` runs the Track A agent loop for each model×task×run slot and writes structured output + trace under `runs_dir`. Use `--models`, `--tasks`, or `--skip-existing` to narrow or resume runs. For live gpt-4o campaigns on low TPM tiers, set `BENCHMARK_RUN_DELAY_SECONDS=3` between slots.

### Agent output contract (SH-07 stub)

Schema: [schemas/agent_output_v1.json](./schemas/agent_output_v1.json)

Path pattern: `runs/{campaign_id}/{model_slug}/{task_id}_run{NN}.json` (L1 metrics)

L3 submissions: `{task_id}_run{NN}_submission.json` — validated by `validate_agent_submission.py`.

```bash
python3 benchmark_v0.1/scripts/validate_agent_submission.py --all
python3 benchmark_v0.1/scripts/validate_agent_submission.py \
  --task GOOGL_footnote_reconciliation \
  --submission benchmark_v0.1/contract_fixtures/GOOGL_footnote_reconciliation_submission_gold.json
```

```bash
# Reference trap fixtures (checked in smoke_test.py)
python3 benchmark_v0.1/scripts/mock_agent_stub.py --write-contract-fixtures

# Write one slot (same path SH-07 must use)
python3 benchmark_v0.1/scripts/mock_agent_stub.py \
  --mode trap_googl_sign \
  --slot gpt-4o/GOOGL_footnote_reconciliation_run01
```

Trap modes: `gold`, `trap_googl_sign`, `trap_googl_blind_sum`, `trap_pep_reported_only`, `trap_pep_wrong_region`, `malformed`, `missing`.

Fixtures: [contract_fixtures/](./contract_fixtures/)

### Benchmark agent loop (Track A runtime)

```bash
# Scripted gold path — corpus → tools → structured output + trace (A2 gate)
python3 benchmark_v0.1/scripts/benchmark_agent_loop.py \
  --agent scripted \
  --task GOOGL_footnote_reconciliation \
  --plan benchmark_v0.1/examples/agents/googl_good_plan.json \
  --out-dir /tmp/bench_googl --run-index 1

# Mock weak agent (blind sum → RECON_OMIT)
python3 benchmark_v0.1/scripts/benchmark_agent_loop.py \
  --agent mock --task GOOGL_footnote_reconciliation \
  --out-dir /tmp/bench_mock --run-index 1
```

Modes: `scripted`, `mock`, `openai`. No PM — tools + structured submit only.

OpenAI mode uses `OPENAI_API_KEY` (optional `OPENAI_MODEL`, default `gpt-4o-mini`). Submit tool requires `metrics` + `citations` + policy acks (PEP).

### API keys (local only)

Do **not** paste keys into shell history or commit them. Recommended:

1. Create repo-root `.env` (already gitignored): `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, optional `BENCHMARK_RUN_DELAY_SECONDS=3`.
2. Load once per session: `set -a && source .env && set +a`
3. Verify Anthropic format: `python3 -c "import os; k=os.environ.get('ANTHROPIC_API_KEY',''); print('ok' if k.startswith('sk-ant-') and 'ANTHROPIC_API_KEY=' not in k else 'bad')"`
4. **Rotate** any key that appeared in terminal logs, chat, or screenshots — revoke the old key in the provider console after creating a replacement.

**1×1×1 live pilot** (before full 2×2×3):

```bash
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_1x1x1.json \
  --execute --agent openai

# PEP re-pilot (after citation tweak — overwrite prior run)
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_1x1x1.json \
  --execute --agent openai --tasks PEP_fx_organic_growth

# Full OpenAI mini grid (2 tasks × 3 runs = 6 slots)
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py \
  --campaign benchmark_v0.1/campaigns/pilot_eval_openai_mini_v1.json \
  --execute --agent openai
```

---

## Planned next (P2)

| Task | Blocker |
|------|---------|
| P2-04g live eval | API keys + Anthropic adapter (OpenAI `--execute` ready) |
| NFLX_guidance_drift (Type F) | P2-08 transcript ingest |
| AMZN_footnote_reconciliation | CFA associate draft |
| KO_fx_organic_growth | Clone PEP published template |

---

## Verify commands

```bash
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

## Expert sign-off (published)

- [GOOGL_GT_REVIEW.md](../docs/expert_drafts/GOOGL_GT_REVIEW.md)
- [PEP_FX_GT_REVIEW.md](../docs/expert_drafts/PEP_FX_GT_REVIEW.md)
