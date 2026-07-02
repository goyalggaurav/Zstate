# Track A Leaderboard v0 — Actionable Fracture View

**Campaign:** `pilot_eval_4task_v1`  
**Generated:** 2026-07-02T01:20:13.833223+00:00  
**Git:** `61fcb9a`  
**Source report:** 2026-07-02T00:36:35.579447+00:00  

> **Primary rank:** headline weighted composite (PEP + AMZN + NFLX).  
> **Fracture Intensity (FI):** diagnostic only — severity-weighted fracture load on headline runs (lower is cleaner).

---

## Rankings

| Rank | Model | Headline | FI ↓ | Gap task | Top fractures (headline) |
|------|-------|----------|------|----------|---------------------------|
| 1 | `claude-sonnet-4-5` | **0.966** | 0.000 | — | `CITE_BROAD` |
| 2 | `gpt-4o` | **0.817** | 1.000 | `NFLX_guidance_drift` (−0.371) | `CITE_BROAD`, `CITE_HALLUC`, `GUIDANCE_PERIOD_ERR` |

---

## Per-model fracture profiles

### #1 `claude-sonnet-4-5`

- **Headline composite:** 0.966
- **Fracture Intensity:** 0.0 *(diagnostic)*

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×3

### #2 `gpt-4o`

- **Headline composite:** 0.8167
- **Fracture Intensity:** 1.0 *(diagnostic)*
- **Gap task vs leader:** `NFLX_guidance_drift` (0.6286 vs leader 1.0, Δ 0.3714)

**Layer profile (headline runs):**
- **L1:** `GUIDANCE_PERIOD_ERR`×2
- **L3:** `CITE_BROAD`×8, `CITE_HALLUC`×3

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_HALLUC`
- `AMZN_footnote_reconciliation`: `CITE_BROAD`
- `NFLX_guidance_drift`: `CITE_BROAD`, `GUIDANCE_PERIOD_ERR`

---

## Methodology

- **Headline tasks:** `PEP_fx_organic_growth`, `AMZN_footnote_reconciliation`, `NFLX_guidance_drift`
- **Excluded from headline:** `GOOGL_footnote_reconciliation`
- **Runs per task:** 3; task score = median composite
- **FI weights:** critical 1.0 · high 0.6 · medium 0.3 · low 0.1
- **Expert sign-off:** all headline tasks published with CFA review docs

See also: [PILOT_EVAL_JUL2026.md](./PILOT_EVAL_JUL2026.md)
