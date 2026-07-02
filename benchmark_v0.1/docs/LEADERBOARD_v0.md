# Track A Leaderboard v0 — Actionable Fracture View

**Campaign:** `pilot_eval_5task_v1`  
**Generated:** 2026-07-02T14:40:12.988935+00:00  
**Git:** `c306bec`  
**Source report:** 2026-07-02T14:22:32.262009+00:00  

> **Primary rank:** headline weighted composite (PEP + AMZN + NFLX).  
> **Fracture Intensity (FI):** diagnostic only — severity-weighted fracture load on headline runs (lower is cleaner).

---

## Rankings

| Rank | Model | Headline | FI ↓ | Gap task | Top fractures (headline) |
|------|-------|----------|------|----------|---------------------------|
| 1 | `claude-sonnet-4-5` | **0.994** | 0.000 | — | `CITE_BROAD`, `CITE_HALLUC` |
| 2 | `gemini-2.5-flash` | **0.982** | 0.000 | `NFLX_guidance_drift` (−0.049) | `CITE_BROAD`, `CITE_HALLUC` |
| 3 | `gpt-4o` | **0.896** | 0.300 | `PEP_fx_organic_growth` (−0.136) | `CITE_BROAD`, `CITE_HALLUC` |

---

## Per-model fracture profiles

### #1 `claude-sonnet-4-5`

- **Headline composite:** 0.9939
- **Fracture Intensity:** 0.0 *(diagnostic)*

**Layer profile (headline runs):**
- **L3:** `CITE_HALLUC`×2, `CITE_BROAD`×1

### #2 `gemini-2.5-flash`

- **Headline composite:** 0.9818
- **Fracture Intensity:** 0.0 *(diagnostic)*
- **Gap task vs leader:** `NFLX_guidance_drift` (0.9271 vs leader 0.9757, Δ 0.0486)

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×4, `CITE_HALLUC`×1

**Fracture delta vs leader (by task):**
- `PEP_fx_organic_growth`: `CITE_HALLUC`
- `KO_footnote_reconciliation`: `CITE_BROAD`

### #3 `gpt-4o`

- **Headline composite:** 0.8961
- **Fracture Intensity:** 0.3 *(diagnostic)*
- **Gap task vs leader:** `PEP_fx_organic_growth` (0.864 vs leader 1.0, Δ 0.136)

**Layer profile (headline runs):**
- **L3:** `CITE_BROAD`×11, `CITE_HALLUC`×3

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
