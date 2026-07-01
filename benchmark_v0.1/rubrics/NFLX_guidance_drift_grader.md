# Grader rubric — NFLX_guidance_drift

**Archetype:** `F_guidance_drift` · **Tier:** L3 · **Guidance grain:** annual vs YTD actuals

## Layer 1

| Metric | Pass | Fail |
|--------|------|------|
| Annual guidance | 18,000 USD M from Q4 2024 letter | Wrong figure or quarterly fiction |
| YTD period | 9 months (through Q3 2025) | Six-month or single-quarter window |
| YTD content cash | 12,039 USD M (9-month additions) | Six-month (7,385) or YTD amort (11,658) |
| Q3 amortization | 4,003 USD M (Q3 supplemental table) | N/A or swapped with cash |
| Pace variance | ~−10.8% vs implied 13,500 USD M pace | Wrong formula or wrong grain |
| Below pace | true (YTD under implied pace) | false when YTD < pace |

## Layer 2

- Required slugs: `narrative_guidance`, `quantitative_actuals`
- Order: guidance before actuals (`strict_first_section`)
- Python_Interpreter used for pace variance check

## Layer 3

- Distinct snippet per metric
- Policy ack: `amortization_not_cash_spend`
- Citations must map to correct `section_slug`

## Fractures

| Mode | Code |
|------|------|
| wrong_ytd_window | GUIDANCE_PERIOD_ERR |
| amortization_as_cash | CASH_VS_AMORT_ERR |
| cite_duplicate_snippet | CITE_BROAD |
