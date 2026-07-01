# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks** across 5 companies, starting with **1 published** + **1 draft** task.

## Corpus (P0-06)

Pilot registry for **GOOGL, AMZN, NFLX, PEP, KO** — EDGAR metadata + SEC URLs. Full text ingest deferred to SH-06.

```bash
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

Manifest: [corpus/corpus_manifest_v1.json](./corpus/corpus_manifest_v1.json)

---

## Published task

| Task | Type | Period | Status |
|------|------|--------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | **Q1 2026** (10-Q filed 2026-04-30) | **Published** (CFA approved 2026-07-01) |

### What this task tests

Reconcile **Q1 2026** reportable segment revenues to consolidated total revenue. The trap: agents sum Google Services + Google Cloud + Other Bets (**$110,076M**) and miss **hedging gains (losses) of $(180)M** — a **loss**, not a gain. Note 15 states hedging is **not allocated to reportable segments**.

---

## Draft task (Type M — third archetype)

| Task | Type | Period | Status |
|------|------|--------|--------|
| [PEP_fx_organic_growth](./tasks/PEP_fx_organic_growth.json) | M — Modeling | **FY2025** (10-K filed 2026-02-18) | **Draft** (CFA review pending) |

### What this task tests

Constant-currency organic revenue growth for **Europe** and **AMESA** using **weighted-average FX** from the 10-K — not spot rates. Traps: reporting GAAP growth as organic CC, or using year-end EUR/USD instead of WAE.

```bash
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
```

CFA review: [docs/expert_drafts/PEP_FX_GT_REVIEW.md](../docs/expert_drafts/PEP_FX_GT_REVIEW.md)

---

## Planned next (P2)

| Task | Blocker |
|------|---------|
| NFLX_guidance_drift (Type F) | P2-08 transcript ingest |
| AMZN_footnote_reconciliation | CFA associate draft |
| KO_fx_organic_growth | After PEP template proven |

---

## Verify commands

```bash
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026
python3 benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py
python3 benchmark_v0.1/scripts/validate_corpus_manifest.py
```

## CFA sign-off (published)

See [docs/expert_drafts/GOOGL_GT_REVIEW.md](../docs/expert_drafts/GOOGL_GT_REVIEW.md).
