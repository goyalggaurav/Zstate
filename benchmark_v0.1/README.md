# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks**, starting with **1 complete reference task**.

## Pilot task (reference implementation)

| Task | Type | Period | Status |
|------|------|--------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | **Q1 2026** (10-Q filed 2026-04-30) | Pilot — pending expert sign-off |

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

### Latest annual reference — FY2025 (USD millions)

| Line | FY2025 |
|------|--------|
| Google Services | 342,721 |
| Google Cloud | 58,705 |
| Other Bets | 1,537 |
| **Segment sum** | **402,963** |
| **Hedging gains (losses)** | **(127)** |
| **Consolidated total** | **402,836** |

Source: [Alphabet 10-K FY2025 — Note 16 (SEC)](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R25.htm) (filed 2026-02-05)

### Files

```
benchmark_v0.1/
├── tasks/GOOGL_footnote_reconciliation.json
├── ground_truth/GOOGL_footnote_reconciliation_gt.json
├── gold_paths/GOOGL_footnote_reconciliation.json
├── scripts/verify_googl_footnote_reconciliation.py
└── README.md
```

### Verify ground truth

```bash
# Scored period — Q1 2026
python benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py

# Optional — FY2025 annual cross-check
python benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py --period fy2025
```

### Primary source (Q1 2026)

- [SEC EDGAR — Form 10-Q period ended 2026-03-31](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000048/goog-20260331.htm)

### Expert sign-off required

Numbers verified against public SEC filings. **CFA peer review required** before `status: published`.
