# Track A corpus bundles

Redacted filing excerpts for benchmark pilot tasks. Schema and required content: [`docs/CORPUS_BUNDLE_CONTRACT.md`](../docs/CORPUS_BUNDLE_CONTRACT.md).

| Bundle | Task | Archetype | Path roles (canonical slugs) |
|--------|------|-----------|------------------------------|
| `googl_q1_2026_bundle.json` | `GOOGL_footnote_reconciliation` | `F_adjustment` | `segment_financials`, `revenue_disaggregation` |
| `pep_fy2025_bundle.json` | `PEP_fx_organic_growth` | `M_organic` | `segment_financials`, `narrative_organic` |
| `amzn_fy2025_bundle.json` | `AMZN_footnote_reconciliation` | `F_exact` | `segment_policy`, `compensation_disclosure`, `segment_financials`, `consolidated_primary`, `narrative_fx` (+ decoy `segment_financials_prior_year`) |
| `nflx_q2q3_2025_bundle.json` | `NFLX_guidance_drift` *(draft)* | `F_guidance_drift` | `narrative_guidance`, `quantitative_actuals` (+ decoy `quantitative_wrong_ytd_window`) |

Bundles v1.2 include `archetype`, `section_registry[].path_role`, `filing_label`, and optional `legacy_section_slugs[]` for rescore compatibility. Slugs are canonical only — see contract §1a.

Validate: `python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --all`
