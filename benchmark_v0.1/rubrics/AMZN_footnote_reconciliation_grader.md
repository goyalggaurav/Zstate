# AMZN footnote reconciliation — grader brief (pilot draft)

Type F forensics task. FY2025 10-K segment net sales reconcile exactly to consolidated (no GOOGL-style hedging line). **L2 signal** comes from five-section gold path order, Note 8 SBC gate, and FY2024 decoy slug.

## Layer weights

| Layer | Weight | Signal |
|-------|--------|--------|
| L1 | 50% | Segment values + consolidated + International growth % |
| L2 | 35% | Section recall + **access order** (policy → Note 8 → Note 10 → IS → MD&A) |
| L3 | 15% | Distinct verbatim citations + `sbc_not_in_segment_oi` ack |

## L2 path variance vs GOOGL

- **5 required sections** (GOOGL: 2)
- **Order-weighted L2** (40% order vs 25% on GOOGL/PEP)
- **`strict_first_section`**: first filing access must be `segment_reporting_policy`
- **Decoy slug** `note_10_prior_year` returns FY2024 column only (637,959 consolidated) — L1 fail if used for metrics

## Common failure modes

| Mode | Fracture | Trigger |
|------|----------|---------|
| wrong_period | HALLUC_FILL | FY2024 consolidated 637,959 |
| intl_fx_swap | CC_OMIT | 10% reported / 13% CC swapped |
| treat_sbc_as_segment_line_item | SBC_ALLOCATION_ERR | Consolidated 736,391 (= 716,924 + 19,467 SBC) |
| policy_skip | SECTION_MISS | Missing `segment_policy` |
| sbc_note_skip | SECTION_MISS | Missing `stock_compensation_note` |
| cite_duplicate_snippet | CITE_BROAD | Same row copied for multiple metrics |
