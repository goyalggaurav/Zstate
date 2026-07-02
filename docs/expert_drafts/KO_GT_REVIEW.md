# KO Footnote Reconciliation — Expert GT Review (Draft)

**Task:** `KO_footnote_reconciliation`  
**Archetype:** `F_exact`  
**Status:** Draft — **not published** until sign-off below  
**Template:** P3-18 hardened task (GT-native L1 + `fixture_from_gt`)

---

## Expert wedge checklist (complete before bundle finalization)

Expert must confirm within **2 hours** or escalate / pick a different footnote wedge:

| # | Gate | Pass? | Notes |
|---|------|-------|-------|
| 1 | **Scored wedge** — six-segment net revenue sum equals consolidated ($50,256M FY2025) | ☐ | Note 19 operating segments |
| 2 | **KO-specific trap** — Global Ventures omission is realistic (not a GOOGL hedging clone) | ☐ | Costa / innocent brands |
| 3 | **Second trap** — Bottling Investments omission or LatAm FX swap is citable | ☐ | |
| 4 | **Decoy** — FY2024 column available as `segment_financials_prior_year` | ☐ | Consolidated $46,905M |
| 5 | **Excerpt fidelity** — bundle excerpts match filing tables (± rounding) | ☐ | Pending LATER-06 verbatim ingest |
| 6 | **No recommendation** — task prompt excludes Buy/Hold/Sell | ☑ | Built into prompt |

---

## Scoring design

| Layer | Focus |
|-------|--------|
| L1 | Six segment net revenues + consolidated; LatAm 12% reported / 15% CC |
| L2 | segment_policy → segment_financials → consolidated_primary → narrative_fx |
| L3 | Distinct snippets; policy ack `global_ventures_is_reportable_segment` |

### Primary failure modes

| Mode | Agent behavior | Fracture |
|------|----------------|----------|
| `omit_global_ventures` | Sums geo segments only; skips Global Ventures | `RECON_OMIT` |
| `omit_bottling_investments` | Omits Bottling Investments line | `RECON_OMIT` |
| `latin_fx_swap` | Swaps 12% reported vs 15% CC | `CC_OMIT` |
| `wrong_period` | Uses FY2024 consolidated $46,905M | `HALLUC_FILL` |

---

## Verification commands

```bash
python3 benchmark_v0.1/scripts/verify_footnote_exact.py \
  --ground-truth benchmark_v0.1/ground_truth/KO_footnote_reconciliation_gt.json

python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task KO_footnote_reconciliation

python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --task KO_footnote_reconciliation
```

### Contract fixtures (GT-derived — no hand-typed literals)

```bash
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'benchmark_v0.1/scripts')
from agent_output_contract import l1_values_from_gt, submission_from_gt
print(l1_values_from_gt('KO_footnote_reconciliation'))
"
```

---

## Sign-off

| Field | Value |
|-------|-------|
| Reviewer | _pending_ |
| Review date | _pending_ |
| Decision | ☐ Approve publish &nbsp; ☐ Revise wedge &nbsp; ☐ Reject task |

**Blockers:** Expert must verify Note 19 numbers against KO 10-K FY2025 filing before changing manifest status to `published`.
