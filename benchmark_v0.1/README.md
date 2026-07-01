# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks** across 5 companies; **2 published** tasks (Type F + Type M).

## Corpus (P0-06)

Pilot registry for **GOOGL, AMZN, NFLX, PEP, KO** — EDGAR metadata + SEC URLs. Full text ingest deferred to SH-06.

```bash
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

Manifest: [corpus/corpus_manifest_v1.json](./corpus/corpus_manifest_v1.json)

---

## Published tasks

| Task | Type | Period | Status |
|------|------|--------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | **Q1 2026** (10-Q filed 2026-04-30) | **Published** (expert-reviewed 2026-07-01) |
| [PEP_fx_organic_growth](./tasks/PEP_fx_organic_growth.json) | M — Modeling | **FY2025** (10-K filed 2026-02-03) | **Published** (expert-reviewed 2026-07-01) |

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

# Score existing agent outputs on disk
python3 benchmark_v0.1/scripts/run_benchmark_campaign.py
```

Output: [runs/pilot_eval_campaign_v1/pilot_eval_campaign_v1.json](./runs/pilot_eval_campaign_v1/pilot_eval_campaign_v1.json)

Live agent runs require **LATER-03** (SH-07 eval orchestrator). This pipeline scores structured `--agent-output` JSON via task verify scripts.

---

## Planned next (P2)

| Task | Blocker |
|------|---------|
| P2-04 live eval | LATER-03 orchestrator (fixtures + scoring ready) |
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
