# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks**, starting with **1 published reference task**.

## Published task

| Task | Type | Period | Status |
|------|------|--------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | **Q1 2026** (10-Q filed 2026-04-30) | **Published** (CFA approved 2026-07-01) |

### What this task tests

Reconcile **Q1 2026** reportable segment revenues to consolidated total revenue. The trap: agents sum Google Services + Google Cloud + Other Bets (**$110,076M**) and miss **hedging gains (losses) of $(180)M** — a **loss**, not a gain. Note 15 states hedging is **not allocated to reportable segments**.

### Q1 2026 reconciliation (USD millions)

| Line | Q1 2026 |
|------|---------|
| Google Services | 89,637 |
| Google Cloud | 20,028 |
| Other Bets | 411 |
| **Segment sum** | **110,076** |
| **Hedging gains (losses)** | **(180)** |
| **Consolidated total** | **109,896** |

### Files

```
benchmark_v0.1/
├── tasks/GOOGL_footnote_reconciliation.json
├── ground_truth/GOOGL_footnote_reconciliation_gt.json
├── gold_paths/GOOGL_footnote_reconciliation.json
├── rubrics/GOOGL_footnote_reconciliation_grader.md
├── scripts/verify_googl_footnote_reconciliation.py
└── manifest.json
```

### Verify ground truth

```bash
python3 benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period q1_2026
```

### CFA sign-off

See [docs/expert_drafts/GOOGL_GT_REVIEW.md](../docs/expert_drafts/GOOGL_GT_REVIEW.md).
