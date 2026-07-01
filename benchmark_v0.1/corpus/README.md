# Track A corpus bundles

Redacted filing excerpts for benchmark pilot tasks. Schema and required content: [`docs/CORPUS_BUNDLE_CONTRACT.md`](../docs/CORPUS_BUNDLE_CONTRACT.md).

| Bundle | Task | Sections |
|--------|------|----------|
| `googl_q1_2026_bundle.json` | `GOOGL_footnote_reconciliation` | Note 15 (segments), Note 2 (revenues) |
| `pep_fy2025_bundle.json` | `PEP_fx_organic_growth` | Note 1 (`note_1`), MD&A organic (`mdna_organic`) |

Bundles v1.1 include `section_registry[]` and `policy_notes[]`. Slugs are canonical only — see contract §1a.

Validate: `python3 benchmark_v0.1/scripts/validate_corpus_bundle.py --all`
