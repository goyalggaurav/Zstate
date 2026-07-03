# Track A Leaderboard v0 — Actionable Fracture View

**Campaign:** `pilot_eval_5task_synthetic_l3_v1`  
**Generated:** 2026-07-03T12:23:15.537485+00:00  
**Git:** `d55c5f1`  
**Source report:** 2026-07-03T12:22:43.104405+00:00  

> **Primary rank:** headline weighted composite (PEP + AMZN + NFLX).  
> **Fracture Intensity (FI):** diagnostic only — severity-weighted fracture load on headline runs (lower is cleaner).

---

## Rankings

| Rank | Model | Headline | FI ↓ | Gap task | Top fractures (headline) |
|------|-------|----------|------|----------|---------------------------|
| 1 | `claude-sonnet-4-5` | **0.938** | 0.150 | — | `CITE_BROAD` |
| 2 | `gpt-4o` | **0.892** | 0.300 | `NFLX_guidance_drift` (−0.073) | `CITE_BROAD`, `CITE_HALLUC` |
| 3 | `gemini-2.5-flash` | **0.694** | 0.650 | `NFLX_guidance_drift` (−0.951) | `CITE_BROAD`, `CITE_HALLUC`, `PATH_INEFF`, `TIMEOUT` |

---

## Per-model fracture profiles

### #1 `claude-sonnet-4-5`

- **Headline composite:** 0.9376
- **Fracture Intensity:** 0.15 *(diagnostic)*
- **Synthetic L3 FI:** 0.0 *(decoy bait hits only)*

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×2

### #2 `gpt-4o`

- **Headline composite:** 0.8924
- **Fracture Intensity:** 0.3 *(diagnostic)*
- **Synthetic L3 FI:** 0.0 *(decoy bait hits only)*
- **Gap task vs leader:** `NFLX_guidance_drift` (0.8786 vs leader 0.9514, Δ 0.0728)

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×4, `CITE_HALLUC`×1

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_HALLUC`
- `AMZN_footnote_reconciliation`: `CITE_BROAD`
- `KO_footnote_reconciliation`: `CITE_BROAD`

### #3 `gemini-2.5-flash`

- **Headline composite:** 0.6935
- **Fracture Intensity:** 0.65 *(diagnostic)*
- **Synthetic L3 FI:** 0.0 *(decoy bait hits only)*
- **Gap task vs leader:** `NFLX_guidance_drift` (0.0 vs leader 0.9514, Δ 0.9514)

**Layer profile (headline runs):**
- **L1:** `TIMEOUT`×1
- **L2:** `PATH_INEFF`×1
- **L3:** `CITE_BROAD`×2, `CITE_HALLUC`×1

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_HALLUC`
- `NFLX_guidance_drift`: `PATH_INEFF`, `TIMEOUT`
- `KO_footnote_reconciliation`: `CITE_BROAD`

---

## Methodology

- **Headline tasks:** `PEP_fx_organic_growth`, `AMZN_footnote_reconciliation`, `NFLX_guidance_drift`, `KO_footnote_reconciliation`
- **Excluded from headline:** `GOOGL_footnote_reconciliation`
- **Runs per task:** 1; task score = median composite
- **FI weights:** critical 1.0 · high 0.6 · medium 0.3 · low 0.1
- **Expert sign-off:** all headline tasks published with CFA review docs

See also: [PILOT_EVAL_JUL2026.md](./PILOT_EVAL_JUL2026.md)
