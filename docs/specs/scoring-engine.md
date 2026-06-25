# Scoring Engine — Component Spec

**Version:** 0.1 (draft)  
**Status:** Design — no implementation  
**Owner:** Platform Engineering + Domain Experts  
**Consumers:** Eval Orchestrator, Expert Workbench, Benchmark leaderboard

---

## 1. Purpose

The Scoring Engine evaluates agent runs against the **three-layer reward model** aligned with Zstate's Task → Trajectory → Reward philosophy:

| Layer | Name | Method | Weight (initial) |
|-------|------|--------|------------------|
| **Layer 1** | Technical & Tabular Accuracy | Programmatic | 40% |
| **Layer 2** | Domain Reasoning & Judgment | Expert rubric + trajectory analysis | 35% |
| **Layer 3** | Traceability & Enterprise Safety | Automated + compliance | 25% |

Plus **FINRA baseline** (hard veto) and **mandate profiles** (score cap or fail).

**Aggregation across 3 runs:** median score; Layer 3 compliance = worst run wins.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Scoring Engine                             │
├─────────────────────────────────────────────────────────────────┤
│  Ingest                                                           │
│    ├── Run trajectory + final output                             │
│    ├── Task ground truth + gold trajectory                       │
│    └── Rubric config (versioned)                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1 — Hard Reward                                           │
│    ├── Numeric claim extractor                                   │
│    ├── Ground truth comparator (± tolerance)                     │
│    ├── Python verification re-runner                             │
│    └── Sign & directionality rules                               │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2 — Expert Reward                                         │
│    ├── Trajectory vs gold path analyzer                          │
│    ├── Section access coverage scorer                            │
│    ├── CoT rubric scorer (assisted)                              │
│    └── Expert override interface                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3 — Trust Reward                                          │
│    ├── Citation completeness auditor                             │
│    ├── Uncertainty calibration checker                           │
│    ├── FINRA baseline linter                                     │
│    └── Mandate profile linter                                    │
├─────────────────────────────────────────────────────────────────┤
│  Aggregator                                                       │
│    ├── Per-run reward vector                                     │
│    ├── 3-run median aggregation                                  │
│    └── Leaderboard export                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Reward Vector Schema

```json
{
  "run_id": "run_abc123",
  "task_id": "GOOGL_footnote_reconciliation",
  "model_id": "tier_a_model_x",
  "run_index": 2,
  "scored_at": "2025-08-15T10:15:00Z",
  "rubric_version": "rubric_v1",

  "layer1": {
    "score": 0.85,
    "metrics": [
      {
        "metric_id": "google_cloud_revenue_fy2024",
        "expected": 43224,
        "actual": 43224,
        "pass": true,
        "weight": "high"
      },
      {
        "metric_id": "reconciliation_delta",
        "expected": 0,
        "actual": 0,
        "pass": true,
        "weight": "medium"
      }
    ],
    "sign_checks": { "pass": true, "violations": [] },
    "python_verification": { "pass": true, "delta_pct": 0.0001 },
    "failure_codes": []
  },

  "layer2": {
    "score_normalized": 0.80,
    "dimensions": [
      {
        "dimension": "contextual_awareness",
        "score": 4,
        "max": 5,
        "method": "expert_assisted",
        "evidence": "Trajectory shows Note 2 access; normalized reclassification"
      },
      {
        "dimension": "footnote_utilization",
        "score": 5,
        "max": 5,
        "method": "trajectory_diff",
        "evidence": "Matched gold minimal_section_set"
      },
      {
        "dimension": "forecast_bounding",
        "score": null,
        "max": 5,
        "method": "n/a",
        "evidence": "Not applicable for footnote task"
      }
    ],
    "trajectory_similarity": 0.78
  },

  "layer3": {
    "score": 0.90,
    "citation_audit": {
      "claims_total": 8,
      "claims_fully_cited": 7,
      "completeness_pct": 87.5,
      "pass_threshold": 90,
      "pass": false
    },
    "uncertainty_calibration": {
      "pass": true,
      "hallucinated_gaps": 0
    },
    "finra": {
      "pass": true,
      "violations": []
    },
    "mandate": {
      "profile": "no_speculative_language",
      "pass": true,
      "violations": []
    },
    "veto": false
  },

  "aggregate_score": 0.82,
  "stage_pass": {
    "stage_1": true,
    "stage_2": true,
    "stage_3": true,
    "stage_4": true
  },
  "fracture_codes": [],
  "failure_codes": ["L3_CITATION_INCOMPLETE"]
}
```

---

## 4. Layer 1 — Technical & Tabular Accuracy

### Rubric matrix

| Metric | Pass | Fail | Weight |
|--------|------|------|--------|
| Data point extraction | Value + unit match filing exactly | Wrong period (annualized vs quarterly) | **High** |
| Sign & directionality | Outflows negative in CF calcs | CapEx/buybacks positive → inflated FCF | **Critical** |
| Mathematical precision | Within ±0.01% of Python verification | Formula/rounding errors | **Medium** |

### Scoring logic

```
layer1_score = weighted_mean(metric_passes)

CRITICAL OVERRIDE:
  if sign_error → layer1_score = 0; aggregate capped
```

### Programmatic checks

1. Extract numeric claims from structured final output
2. Match to ground truth `extracted_values` and `computed_values`
3. Re-run `verification_script_ref` with agent's inputs
4. Apply sign rules on cash flow fields

### Layer 1 automation target

≥80% of scorable claims automated for MVD.

---

## 5. Layer 2 — Domain Reasoning & Judgment

### Rubric matrix

| Dimension | Score 4–5 (High) | Score 1–2 (Poor) |
|-----------|------------------|------------------|
| Contextual awareness | Normalizes non-recurring items | Accepts headline GAAP blindly |
| Forecast bounding | WACC/multiples peer-bounded | Unrealistic sector multiples |
| Footnote utilization | Read Commitments/Contingencies | Summary statements only |

### Scoring methods

| Method | Description | Automation level |
|--------|-------------|------------------|
| `trajectory_diff` | Compare section access vs gold `minimal_section_set` | Fully automated |
| `cot_rubric` | NLP-assisted CoT analysis against anchors | Assisted |
| `expert_assisted` | Pre-filled score + expert confirm/override | Human-in-loop |
| `n/a` | Dimension not applicable to archetype | Skipped |

### Trajectory similarity components

```
similarity = (
  0.4 × tool_sequence_overlap +
  0.4 × section_access_jaccard +
  0.2 × stage_completion_match
)
```

Expert final score can adjust ±1 point with logged rationale.

### Layer 2 expert sampling (MVD)

- 100% scoring for pilot (first 15 tasks)
- 20% spot-check for remaining 30 tasks
- Inter-rater calibration on 10 tasks (target κ ≥ 0.7)

---

## 6. Layer 3 — Traceability & Enterprise Safety

### Rubric matrix

| Metric | Pass | Fail |
|--------|------|------|
| Source grounding | Every metric → `{doc_id, page, snippet}` | Broad/missing citation |
| Uncertainty calibration | Flags gaps; no interpolation | Fake trends / assumed values |
| Compliance guardrails | Fact/opinion split + disclosures | Guaranteed returns language |

### FINRA baseline rules (`finra_v1`)

| Rule ID | Check |
|---------|-------|
| FIN-001 | No guaranteed returns |
| FIN-002 | Fact vs opinion separated |
| FIN-003 | Risk disclosures present |
| FIN-004 | No personalized advice framing |
| FIN-005 | Material limitations noted |
| FIN-006 | Past performance disclaimer if cited |

**FINRA fail → `veto: true` → aggregate_score = 0**

### Mandate profiles (`mandate_v1`)

| Profile ID | Key rules |
|------------|-----------|
| `long_only_equity` | No short language; Hold/Sell framing |
| `conservative_income` | Dividend/FCF sustainability addressed |
| `no_speculative_language` | Bounded assumptions; no certainty phrasing |

**Mandate fail → Layer 3 capped at 0.3 OR task fail** (configurable per rule severity).

---

## 7. Aggregate Scoring

### Per-run

```
aggregate = w1×layer1 + w2×layer2_norm + w3×layer3

Defaults: w1=0.40, w2=0.35, w3=0.25

Overrides:
  FINRA veto           → aggregate = 0
  sign_error (L1)      → aggregate = 0
  mandate_fail (severe)→ aggregate = min(aggregate, 0.30)
```

### Three-run aggregation

```json
{
  "task_id": "GOOGL_footnote_reconciliation",
  "model_id": "tier_a_model_x",
  "runs": [
    { "run_index": 1, "aggregate_score": 0.72 },
    { "run_index": 2, "aggregate_score": 0.68 },
    { "run_index": 3, "aggregate_score": 0.74 }
  ],
  "reported_aggregate": 0.72,
  "aggregation_method": "median",
  "variance": 0.06,
  "high_variance_flag": false,
  "layer3_compliance": "worst_run_wins",
  "any_finra_veto": false,
  "fracture_codes_union": ["BLOAT_CTX"]
}
```

| Metric | Aggregation rule |
|--------|------------------|
| Aggregate score | Median of 3 runs |
| Layer 1 per-metric | Median; or pass if ≥2/3 pass |
| Layer 3 FINRA | **Fail if any run fails** |
| Layer 3 mandate | **Worst run score** |
| Fracture codes | Union; tag if in ≥2/3 runs |

---

## 8. Compliance Linter (shared with Eval Orchestrator)

The Scoring Engine **owns rule definitions**; Eval Orchestrator **invokes at Stage 4**.

```
POST /api/v1/scoring/lint

Request:
{
  "memo": { ... structured output ... },
  "finra_version": "finra_v1",
  "mandate_profile": "conservative_income"
}

Response:
{
  "finra": { "pass": true, "violations": [] },
  "mandate": { "pass": false, "violations": [
    { "rule_id": "INC-002", "message": "Dividend sustainability not addressed" }
  ]},
  "suggestions": [ ... ]
}
```

---

## 9. API Contract

Base path: `/api/v1/scoring`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/score/run/{run_id}` | Score single run |
| `POST` | `/score/campaign/{campaign_id}` | Batch score all completed runs |
| `GET` | `/scores/run/{run_id}` | Reward vector |
| `GET` | `/scores/task/{task_id}/model/{model_id}` | 3-run aggregated result |
| `GET` | `/leaderboard/{campaign_id}` | Full leaderboard |
| `POST` | `/lint` | Compliance lint (Stage 4) |
| `GET` | `/rubrics/{version}` | Rubric config export |

### Leaderboard row schema

```json
{
  "model_id": "tier_a_frontier_1",
  "tier": "A",
  "tasks_scored": 45,
  "median_aggregate": 0.68,
  "layer1_mean": 0.75,
  "layer2_mean": 0.62,
  "layer3_mean": 0.71,
  "finra_pass_rate": 0.98,
  "mandate_pass_rate": 0.93,
  "fracture_rate": 0.22,
  "avg_tool_calls": 14.2,
  "avg_tokens": 42000,
  "rank": 1
}
```

---

## 10. Rubric Versioning

```
rubrics/
├── rubric_v1/
│   ├── layer1_rules.json
│   ├── layer2_dimensions.json
│   ├── layer2_anchors.json      # score 1–5 examples per dimension
│   ├── finra_v1.json
│   ├── mandate_v1/
│   │   ├── long_only_equity.json
│   │   ├── conservative_income.json
│   │   └── no_speculative_language.json
│   └── weights.json
```

Rubric version locked per campaign; changes require new benchmark version.

---

## 11. Acceptance Criteria

### AC-1: Layer 1 automation
- [ ] ≥80% of ground truth metrics auto-scored
- [ ] Sign check catches known failure test cases
- [ ] Python verification re-runs successfully in sandbox

### AC-2: Layer 2 scoring
- [ ] Trajectory diff operational for all archetypes
- [ ] Expert assisted UI pre-fills ≥70% of dimensions
- [ ] Inter-rater κ ≥ 0.7 on calibration set (10 tasks)

### AC-3: Layer 3 / compliance
- [ ] FINRA linter: 6 rules operational
- [ ] 3 mandate profiles operational
- [ ] FINRA veto sets aggregate to 0 in test cases
- [ ] Citation auditor flags broad/missing citations

### AC-4: Aggregation
- [ ] 3-run median computed correctly
- [ ] Worst-run-wins for Layer 3 compliance verified
- [ ] High-variance flag when spread > 0.15

### AC-5: Discrimination
- [ ] MVD campaign produces ≥15pt spread between best/worst Tier A model
- [ ] Fracture taxonomy: ≥10 distinct codes observed

### AC-6: Integration
- [ ] Auto-scores on campaign completion
- [ ] Leaderboard export matches manual audit on 5 sample tasks

---

## 12. Timeline

| Week | Milestone |
|------|-----------|
| 8–10 | Layer 1 scorer + verification scripts |
| 9–11 | Layer 3 linter (FINRA + mandates) |
| 9–11 | Layer 2 trajectory diff + expert UI |
| 11–12 | Full scoring on dry-run campaign |
| 13–14 | Calibration + weight tuning |

---

*See also: `docs/ZSTATE_EQUITY_RESEARCH_BENCHMARK_FRAMEWORK.md`*
