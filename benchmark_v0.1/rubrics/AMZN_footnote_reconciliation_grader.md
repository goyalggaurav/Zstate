# AMZN footnote reconciliation — grader brief (pilot draft)

Type F forensics task. FY2025 10-K segment net sales reconcile exactly to consolidated (no GOOGL-style hedging line). **L2 signal** comes from four-section gold path order and International FX cross-check.

## Layer weights

| Layer | Weight | Signal |
|-------|--------|--------|
| L1 | 50% | Segment values + consolidated + International growth % |
| L2 | 35% | Section recall + **access order** (policy → Note 10 → IS → MD&A) |
| L3 | 15% | Distinct verbatim citations + `sbc_not_in_segment_oi` ack |

## L2 path variance vs GOOGL

- **4 required sections** (GOOGL: 2)
- **Order-weighted L2** (40% order vs 25% on GOOGL/PEP)
- Agents that jump straight to Note 10 miss policy context and score lower on path

## Common failure modes

| Mode | Fracture | Trigger |
|------|----------|---------|
| wrong_period | HALLUC_FILL | FY2024 consolidated 637,959 |
| intl_fx_swap | CC_OMIT | 10% reported / 13% CC swapped |
| policy_skip | SECTION_MISS | Missing `segment_reporting_policy` |
| cite_duplicate_snippet | CITE_BROAD | Same MD&A row copied for multiple metrics |
