# Track A Leaderboard v0 — Actionable Fracture View

**Campaign:** `pilot_eval_5task_v1`  
**Generated:** 2026-07-02T15:24:41.170026+00:00  
**Git:** `1208d81`  
**Source report:** 2026-07-02T15:18:14.991727+00:00  

> **Primary rank:** headline weighted composite (PEP + AMZN + NFLX).  
> **Fracture Intensity (FI):** diagnostic only — severity-weighted fracture load on headline runs (lower is cleaner).

---

## Rankings

| Rank | Model | Headline | FI ↓ | Gap task | Top fractures (headline) |
|------|-------|----------|------|----------|---------------------------|
| 1 | `claude-sonnet-4-5` | **0.944** | 0.000 | — | `CITE_BROAD`, `CITE_HALLUC` |
| 2 | `gemini-2.5-flash` | **0.926** | 0.150 | `NFLX_guidance_drift` (−0.049) | `CITE_BROAD`, `CITE_HALLUC`, `TIMEOUT` |
| 3 | `gpt-4o` | **0.881** | 0.800 | `PEP_fx_organic_growth` (−0.136) | `CITE_BROAD`, `CITE_HALLUC` |

---

## Per-model fracture profiles

### #1 `claude-sonnet-4-5`

- **Headline composite:** 0.9436
- **Fracture Intensity:** 0.0 *(diagnostic)*

**Layer profile (headline runs):**
- **L3:** `CITE_HALLUC`×4, `CITE_BROAD`×1

### #2 `gemini-2.5-flash`

- **Headline composite:** 0.9256
- **Fracture Intensity:** 0.15 *(diagnostic)*
- **Gap task vs leader:** `NFLX_guidance_drift` (0.83 vs leader 0.8786, Δ 0.0486)

**Layer profile (headline runs):**
- **L1:** `TIMEOUT`×1
- **L3:** `CITE_BROAD`×5, `CITE_HALLUC`×3

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_HALLUC`
- `NFLX_guidance_drift`: `TIMEOUT`
- `KO_footnote_reconciliation`: `CITE_BROAD`

### #3 `gpt-4o`

- **Headline composite:** 0.881
- **Fracture Intensity:** 0.8 *(diagnostic)*
- **Gap task vs leader:** `PEP_fx_organic_growth` (0.864 vs leader 1.0, Δ 0.136)

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×11, `CITE_HALLUC`×6

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_BROAD`, `CITE_HALLUC`
- `AMZN_footnote_reconciliation`: `CITE_BROAD`
- `KO_footnote_reconciliation`: `CITE_BROAD`

---

## Methodology

- **Headline tasks:** `PEP_fx_organic_growth`, `AMZN_footnote_reconciliation`, `NFLX_guidance_drift`, `KO_footnote_reconciliation`
- **Excluded from headline:** `GOOGL_footnote_reconciliation`
- **Runs per task:** 3; task score = median composite
- **FI weights:** critical 1.0 · high 0.6 · medium 0.3 · low 0.1
- **Expert sign-off:** all headline tasks published with CFA review docs

See also: [PILOT_EVAL_JUL2026.md](./PILOT_EVAL_JUL2026.md)
