# benchmark_v0.1 — Pilot Package

Minimum Viable Benchmark pilot: **15 tasks**, starting with **1 complete reference task**.

## Pilot task (reference implementation)

| Task | Type | Status |
|------|------|--------|
| [GOOGL_footnote_reconciliation](./tasks/GOOGL_footnote_reconciliation.json) | F — Forensics | Pilot — pending expert sign-off |

### What this task tests

Reconcile Alphabet FY2024 **reportable segment revenues** to **consolidated total revenue**. The trap: agents sum Google Services + Google Cloud + Other Bets ($349,807M) and miss **hedging gains (losses) of $211M**, which the 10-K states is **not allocated to segments** (Note 16).

### Files

```
benchmark_v0.1/
├── tasks/GOOGL_footnote_reconciliation.json      # Agent-facing task spec
├── ground_truth/GOOGL_footnote_reconciliation_gt.json
├── gold_paths/GOOGL_footnote_reconciliation.json # Minimal section set
├── scripts/verify_googl_footnote_reconciliation.py
└── README.md
```

### Verify ground truth script

```bash
python benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py
# Expected: all_pass: true
```

### Expert sign-off required

Ground truth numbers sourced from Alphabet 10-K FY2024 (filed 2025-02-05). **CFA peer review required** before marking `status: published`.

### Primary source

- [SEC EDGAR — Note 16 Segment Information (R25.htm)](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/R25.htm)
