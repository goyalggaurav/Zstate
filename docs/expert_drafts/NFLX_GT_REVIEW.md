# Expert Review — NFLX Guidance Drift Ground Truth

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Artifact:** `benchmark_v0.1/ground_truth/NFLX_guidance_drift_gt.json`  
**Task:** `NFLX_guidance_drift` (Type F, archetype `F_guidance_drift`)  
**Backlog ref:** P2-01 / P2-08 (EDGAR ingest deferred)  
**Scored period:** FY2025 guidance vs YTD through 2025Q3  
**Status:** `expert_reviewed` — **signed off**  
**Eng Pattern 1 rebuild date:** 2026-07-02  
**Expert review date:** 2026-07-02  
**Implied-pace L1 formula sign-off:** 2026-07-02 (9/12 pro-rata baseline approved)

---

## Eng summary

Compare **FY2025 annual cash content spend guidance** from the Q4 2024 shareholder letter to **nine-month YTD actual** content cash payments in the Q3 2025 10-Q. Archetype `F_guidance_drift` uses path roles: `narrative_guidance` → `quantitative_actuals`.

**Guidance grain:** annual (~$18B). **Actual grain:** nine months ended September 30, 2025. **Implied pace:** `18,000 × 9/12 = 13,500` USD M — standard pro-rata baseline for variance analysis (expert-approved for L1 scoring).

**Drift narrative:** YTD cash **below** implied annual pace (−10.8% variance); `guidance_pace_under: true`.

**Gate B sources (SEC):**

- [Q4 2024 shareholder letter](https://cdn.arstechnica.net/wp-content/uploads/2025/01/FINAL-Q4-24-Shareholder-Letter.pdf) — filed 2025-01-21  
- [Q3 2025 Form 10-Q](https://www.sec.gov/Archives/edgar/data/1065280/000106528025000406/nflx-20250930.htm) — filed 2025-10-17  

Corpus bundle uses pilot excerpts aligned to these filings; full EDGAR verbatim ingest deferred (LATER-06 / P2-08).

### Pattern 1 numbers (USD millions)

| Line | Value | Source (path role) |
|------|-------|-------------------|
| Annual cash content spend guidance | 18,000 | `narrative_guidance` — Q4 2024 letter |
| YTD period (months) | 9 | `quantitative_actuals` — 10-Q column header |
| YTD content cash payments | 12,039 | `quantitative_actuals` — additions (12,039,405) |
| Q3 content amortization | 4,003 | `quantitative_actuals` — supplemental table (4,002,744) |
| **Implied YTD pace** | **13,500** | `18,000 × 9/12` (L1 computed) |
| Pace variance % | −10.8 | `(12,039 − 13,500) / 13,500 × 100` |
| Below implied pace | true | YTD cash < implied pace |

**Note:** Cash flow statement reports additions as `(12,039,405)` outflow; GT stores **12,039** USD M absolute spend (consistent with other benchmark tasks).

### Traps

| Trap | Wrong behavior | Fracture |
|------|----------------|----------|
| `wrong_ytd_window` | Six-month YTD **7,385** instead of nine-month **12,039** | `GUIDANCE_PERIOD_ERR` |
| `amortization_as_cash` | Nine-month amortization **11,658** reported as YTD cash | `CASH_VS_AMORT_ERR` |
| `cite_duplicate_snippet` | Reuses same excerpt for multiple metrics (L3) | `CITE_BROAD` |

Decoy slug `quantitative_wrong_ytd_window` serves six-month column only — must not be used for scored nine-month metrics.

**Policy:** Content amortization ≠ content cash payments (`amortization_not_cash_spend` ack required).

---

## Expert checklist

- [x] Annual guidance ~$18B matches Q4 2024 shareholder letter excerpt
- [x] Nine-month YTD additions 12,039M matches Q3 2025 10-Q cash flow statement
- [x] Q3 amortization 4,003M matches supplemental amortization table
- [x] Implied pace formula `annual × ytd_months / 12` approved for L1 (standard pro-rata baseline)
- [x] Pace variance −10.8% and `guidance_pace_under: true` arithmetically correct
- [x] Six-month decoy (7,385) and amort-as-cash trap (11,658) use real filing lines
- [x] Path roles auditable; guidance grain declared in GT `guidance_spec`
- [x] No investment recommendation required (Type F)
- [ ] Full EDGAR verbatim ingest + checksums — **deferred** (LATER-06; not blocking sign-off)

---

## Eng verification command

```bash
python3 benchmark_v0.1/scripts/verify_benchmark_l1.py --task NFLX_guidance_drift
```

Expected: `all_pass: true`

**YTD window trap (exit code 1 expected):**

```bash
python3 benchmark_v0.1/scripts/verify_guidance_drift.py \
  --ground-truth benchmark_v0.1/ground_truth/NFLX_guidance_drift_gt.json \
  --agent-output /tmp/nflx_ytd_trap.json
```

Fixture `/tmp/nflx_ytd_trap.json` — copy extracted values from GT but set `"ytd_content_cash_payments_usd_m": 7385`.

Expected: `failure_modes: ["wrong_ytd_window"]`, `fracture_codes: ["GUIDANCE_PERIOD_ERR"]`

**Amort-as-cash trap:**

Set `"ytd_content_cash_payments_usd_m": 11658` in the same fixture shape.

Expected: `failure_modes: ["amortization_as_cash"]`, `fracture_codes: ["CASH_VS_AMORT_ERR"]`

---

## Expert verdict

**Verdict:** approve  

**Reviewer:** Gaurav Goyal (CFA Level III candidate)  
**Date:** 2 July 2026  

### Comments

- **Annual guidance:** Confirmed. ~$18B cash content spend from Q4 2024 letter; no fictional quarterly range.
- **YTD actuals:** Confirmed. 12,039M nine-month additions from Q3 2025 10-Q.
- **Implied pace / variance:** Confirmed. 9/12 pro-rata baseline (13,500M) is appropriate for L1 variance scoring; −10.8% under pace.
- **Amortization line:** Confirmed. 4,003M Q3 supplemental table; distinct from cash payments.
- **Traps:** Confirmed. Six-month YTD and YTD-amort-as-cash signatures match real decoy lines.
- **Corpus:** Excerpt stubs acceptable for pilot; EDGAR full ingest tracked separately (LATER-06).
- **Compliance:** Confirmed. No investment recommendation required.

**Sign-off:** NFLX fourth pilot task cleared for **published** benchmark use alongside GOOGL, PEP, and AMZN.
