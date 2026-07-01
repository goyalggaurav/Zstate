# Agent output contract fixtures

Reference JSON files for SH-07 integration.

## L1 agent output (`*.json`)

Each trap mode maps to expected `failure_modes` and `fracture_codes` from the task verify script.

| File | Expected fracture |
|------|-------------------|
| `GOOGL_footnote_reconciliation_gold.json` | (pass) |
| `GOOGL_footnote_reconciliation_trap_googl_sign.json` | `SIGN_ERR` |
| `GOOGL_footnote_reconciliation_trap_googl_blind_sum.json` | `RECON_OMIT` |
| `PEP_fx_organic_growth_gold.json` | (pass) |
| `PEP_fx_organic_growth_trap_pep_reported_only.json` | `CC_OMIT` |
| `PEP_fx_organic_growth_trap_pep_wrong_region.json` | `SCOPE_ERR` |
| `malformed.json` | verify runner error (invalid JSON) |

## L3 submission (`*_submission_*.json`)

Validated by `validate_agent_submission.py`.

| File | Expected fracture |
|------|-------------------|
| `GOOGL_footnote_reconciliation_submission_gold.json` | (pass) |
| `PEP_fx_organic_growth_submission_gold.json` | (pass) |
| `GOOGL_footnote_reconciliation_submission_trap_fake_snippet.json` | `CITE_HALLUC` |
| `GOOGL_footnote_reconciliation_submission_trap_wrong_slug.json` | `SECTION_MISS` |
| `PEP_fx_organic_growth_submission_trap_missing_policy.json` | `POLICY_OMIT` |
| `PEP_fx_organic_growth_submission_trap_halluc_snippet.json` | `CITE_HALLUC` |

Regenerate:

```bash
python3 benchmark_v0.1/scripts/mock_agent_stub.py --write-contract-fixtures
python3 benchmark_v0.1/scripts/mock_agent_stub.py --write-submission-fixtures
```

Validated by `scripts/smoke_test.py`.
