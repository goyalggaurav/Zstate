# Agent output contract fixtures

Reference JSON files for SH-07 integration. Each trap mode maps to expected `failure_modes` and `fracture_codes` from the task verify script.

| File | Expected fracture |
|------|-------------------|
| `GOOGL_footnote_reconciliation_gold.json` | (pass) |
| `GOOGL_footnote_reconciliation_trap_googl_sign.json` | `SIGN_ERR` |
| `GOOGL_footnote_reconciliation_trap_googl_blind_sum.json` | `RECON_OMIT` |
| `PEP_fx_organic_growth_gold.json` | (pass) |
| `PEP_fx_organic_growth_trap_pep_reported_only.json` | `CC_OMIT` |
| `PEP_fx_organic_growth_trap_pep_wrong_region.json` | `SCOPE_ERR` |
| `malformed.json` | verify runner error (invalid JSON) |

Regenerate: `python3 benchmark_v0.1/scripts/mock_agent_stub.py --write-contract-fixtures`

Validated by `scripts/smoke_test.py` → `Benchmark agent output contract`.
