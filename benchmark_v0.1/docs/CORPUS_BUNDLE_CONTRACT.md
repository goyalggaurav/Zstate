# Corpus bundle + benchmark runtime contract (v1.1)

**Status:** v1.2 — universal path_role slugs + archetypes (P2-13–15); extends v1.1 with `legacy_section_slugs` for rescore  
**Consumers:** `benchmark_tool_backend.py`, `benchmark_agent_loop.py`, `validate_corpus_bundle.py`, `validate_agent_submission.py` (planned)

---

## 1. Bundle JSON schema

Mirrors `env_v1/corpus/solaris_bundle_v1.json`:

```json
{
  "bundle_id": "googl_q1_2026_bundle",
  "version": "1.0.0",
  "task_id": "GOOGL_footnote_reconciliation",
  "documents": {
    "<doc_key>": {
      "doc_id": "GOOGL_10Q_2026Q1",
      "doc_type": "10-Q",
      "section": "note_15",
      "name": "Note 15 — Segments",
      "excerpt": "..."
    }
  },
  "retrieval_keys": {
    "Search_Filing": {
      "GOOGL:2026Q1:note_15": "<doc_key>",
      "GOOGL:2026Q1:note_2": "<doc_key>"
    }
  }
}
```

| Field | Rule |
|-------|------|
| `doc_id` | Must match GT `citation.doc_id` and task `required_documents[].doc_id` |
| `excerpt` | Redacted filing text; must contain all GT citation snippets (normalized) |
| `section_registry` | **Required v1.1** — canonical slugs; see §1a |
| `policy_notes` | Optional task-level disclosure traps; see §1b |
| `retrieval_keys.Search_Filing` | Key format: `{ticker}:{period}:{section_slug}` — slug **must** exist in `section_registry` |

### 1a. Sectional retrieval (anti query-drift)

Agents MUST NOT pass free-text queries. `Search_Filing` resolves **only** via the composite key:

```
{ticker}:{period}:{section_slug}
```

| Component | Source | Example (GOOGL) | Example (PEP) |
|-----------|--------|-----------------|-----------------|
| `ticker` | Task JSON `ticker` field | `GOOGL` | `PEP` |
| `period` | Task fiscal period slug | `2026Q1` | `FY2025` |
| `section_slug` | `section_registry[].section_slug` | `segment_financials`, `revenue_disaggregation` | `segment_financials`, `narrative_organic` |

**Normalization (backend):** lowercase `section_slug`; replace spaces/hyphens with `_`. Reject display names (e.g. `"Note 15"`). Accept canonical slug or any token in `legacy_section_slugs[]` (resolved to canonical before lookup).

**Registry entry (required per section, v1.2):**

```json
{
  "section_slug": "segment_financials",
  "path_role": "segment_financials",
  "section_id": "GOOGL_10Q_2026Q1_note_15",
  "doc_id": "GOOGL_10Q_2026Q1",
  "document_key": "segment_financials_doc",
  "filing_label": "Note 15 — Information about Segments and Geographic Areas",
  "legacy_section_slugs": ["note_15"],
  "required": true,
  "allowed_tools": ["Search_Filing", "PDF_Parser"]
}
```

| Field | Rule |
|-------|------|
| `section_slug` | Stable API token — canonical value agent should pass as `section` |
| `path_role` | Must equal `section_slug` (v1.2); archetype-validated role from `schemas/archetype_roles_v1.json` |
| `filing_label` | Human-readable note/section title for prompts (issuer-specific) |
| `legacy_section_slugs` | Optional prior slug tokens accepted by backend/L2/L3 rescore (migration only). **Anti sliding-drift:** at most one `note_N` token per registry row; must match `filing_label` / excerpt header note index (validated in `validate_corpus_bundle.py`). |
| `section_id` | Must match `gold_paths/*/minimal_section_set[].section_id` |
| `document_key` | Key in `documents{}` |
| `required` | If true, L2 section-recall expects a tool hit on this slug |
| `decoy_trap` | Optional; must be a known trap type in archetype schema (decoys are never `required`) |

### 1c. Archetypes (v1.2 — universal task design)

| Field | Location | Rule |
|-------|----------|------|
| `archetype` | Task JSON + bundle + gold path | One of `F_exact`, `F_adjustment`, `M_organic` |
| Path order | `gold_paths/*/l2_gold_path.expected_section_order` | List of **path_role** slugs; scoring is archetype-generic |
| L1 verify | `manifest.json` → `verify_script` | Unified `scripts/verify_benchmark_l1.py` routes by archetype |

Per-company customization is **bundle-only** (excerpt text, `filing_label`, decoy slugs). Task prompts, gold paths, and ground truth reference **path_role slugs only** — never filer-specific note numbers.

### 1d. Citation SSOT (GT + L3 — P3-18)

| Layer | Filer-specific note number? | Required fields |
|-------|----------------------------|-----------------|
| Task prompt / gold path workflow | **No** — use `segment_financials`, etc. | path_role slugs |
| Ground truth `citation` | **No** — do not store `Note N` | `doc_id`, `section_slug`, `snippet` |
| Bundle `section_registry.filing_label` | **Yes** — single issuer map | e.g. `Note 20 — Operating Segments` (KO) |
| Bundle `documents.*.excerpt` | **Yes** — must match filing verbatim | includes note header text |
| Agent submission (L3) | Optional display | `section_slug` + `snippet` required; `filing_label` from bundle at fixture gen |

`submission_from_gt()` resolves display labels from the bundle registry — GT must not duplicate note numbers.

### 1e. F_exact reconciliation schema (GT `verification_schema` — universal)

Layer-1 footnote reconciliation uses optional bridge lines so one verifier handles both simple and intersegment filers:

| Field | Required | Role |
|-------|----------|------|
| `segment_metrics[]` | Yes | Per reportable segment net revenue (or net sales) lines |
| `additive_metrics[]` | No | Lines added to bridge (e.g. `corporate_net_revenues`) |
| `elimination_metrics[]` | No | Intersegment eliminations / consolidation adjustments (signed; typically negative) |
| `consolidated_metric` | Yes | Face-statement or Note consolidated total |

**Verifier rule (`verify_footnote_exact.py`):**  
`sum(segment_metrics) + sum(additive_metrics) + sum(elimination_metrics) == consolidated`

| Filer pattern | Example | Schema |
|---------------|---------|--------|
| Segments sum directly | AMZN (3 segments) | `segment_metrics` only |
| Segments + Corporate | Some filers | `segment_metrics` + `additive_metrics` |
| Segments + Corporate + Eliminations | KO Note 20 Total row | all three optional lists |

Task prompts and gold paths stay slug-only; wedge shape is encoded in GT `verification_schema`, not issuer names.

**Drift failures (backend returns, does not guess):**

| Agent input | Result |
|-------------|--------|
| `section: "Note 15"` (display name) | `NOT FOUND` — must pass canonical slug `segment_financials` |
| `section: "note_15"` (legacy) | Resolves to `segment_financials` if listed in `legacy_section_slugs` |
| Valid slug + wrong period `FY2025` | `NOT FOUND` |
| Valid slug never in `retrieval_keys` | Validator fail at bundle build |

**Implementation status:** **Enforced** — `is_canonical_slug()` + `legacy_slug_map()` in `benchmark_tool_backend.py` / `archetype_roles.py`; archetype checks in `validate_corpus_bundle.py`; `check_archetype_roles()` in smoke tests.

### 1b. Policy notes (bundle metadata for traps)

Structured disclosure facts that L3 must acknowledge — not buried in excerpt prose.

```json
"policy_notes": [
  {
    "policy_id": "no_wae_fx_table",
    "doc_id": "PEP_10K_2025",
    "statement": "Filing does not include a weighted-average FX rate table.",
    "agent_ack_required": true,
    "gold_path_key": "wae_absence_acknowledged",
    "anti_pattern": "invent_wae_rates_not_in_filing"
  }
]
```

| Field | Rule |
|-------|------|
| `policy_id` | Stable token; agent cites in `policy_acknowledgements[]` |
| `doc_id` | Must match task `required_documents[].doc_id` |
| `agent_ack_required` | If true, L3 validator fails when ack missing |
| `gold_path_key` | Links to `gold_paths/*.assumption_log_scoring` |

PEP bundle MUST include `no_wae_fx_table`. GOOGL may add `hedging_not_in_segments` (hedging not allocated to reportable segments).

**Implementation status:** **Enforced in bundles** — `policy_notes[]` validated by B3; L3 agent ack check deferred to `validate_agent_submission.py` (Step 2).

---

## 2. Canonical doc_ids

| Task | doc_id | Bundle file |
|------|--------|-------------|
| GOOGL | `GOOGL_10Q_2026Q1` | `corpus/googl_q1_2026_bundle.json` |
| PEP | `PEP_10K_2025` | `corpus/pep_fy2025_bundle.json` |

---

## 3. Tool surface (Track A)

Task JSON `allowed_tools` names — **not** env_v1 `get_filing`:

| Tool | Input | Output |
|------|-------|--------|
| `Search_Filing` | `ticker`, `period`, `section` (e.g. `note_15`, `note_2`, `note_1`, `mdna_organic`) | Excerpt string |
| `PDF_Parser` | Same as `Search_Filing` | Alias — same backend lookup |
| `Python_Interpreter` | `expression` | Numeric result string (reuse env `safe_calc`) |

Backend maintains `tool_log: list[{tool, input, doc_id, output_preview}]`.

---

## 4. Required excerpt content

### GOOGL (`googl_q1_2026_bundle.json`)

Sections (separate document keys or combined with clear headers):

| Section | GT / gold_path anchor | Must contain |
|---------|----------------------|--------------|
| Note 15 | `GOOGL_10Q_2026Q1_note_15` | `89,637` / `89637`, `20,028`, `411`; hedging policy: **not allocated to reportable segments** |
| Note 2 | `GOOGL_10Q_2026Q1_note_2` | `Hedging gains (losses) ... (180)`, `Total revenues $ 109,896` |

### PEP (`pep_fy2025_bundle.json`)

| Section | gold_path anchor | Must contain |
|---------|------------------|--------------|
| Note 1 | `PEP_10K_2025_note_1_segments` | `EMEA $ 18,025`, `16,658`, `LatAm Foods $ 10,549`, `10,568` |
| MD&A | `PEP_10K_2025_mdna_organic_revenue` | EMEA reported **8%**, FX **2%**, organic **6%**; LatAm reported **(0.2)%** or `-0.2%`, FX **(4.7)%**, organic **4.5%** |
| Disclosure note | — | Statement that filing does **not** include weighted-average FX rate table |

---

## 5. Agent loop outputs

### Structured output (L1)

Path (via `agent_output_contract.agent_output_path`):

```
benchmark_v0.1/runs/{run_dir}/{model_slug}/{task_id}_run{NN}.json
```

Schema: `schemas/agent_output_v1.json` — **L1 metrics only** (flat JSON, backward compatible).

For L3 citation audit, agents submit **`schemas/agent_submission_v1.json`** (wrapper):

```json
{
  "schema_version": "agent_submission_v1",
  "metrics": {
    "google_services_revenue": 89637
  },
  "citations": [
    {
      "metric_id": "google_services_revenue",
      "doc_id": "GOOGL_10Q_2026Q1",
      "section_slug": "note_15",
      "note": "Note 15 — Segment Reporting",
      "table_title": "Revenues by segment",
      "column": "Three Months Ended March 31, 2026",
      "snippet": "Google Services $ 89,637"
    }
  ],
  "policy_acknowledgements": ["no_wae_fx_table"]
}
```

#### Citation object rules (v1.1)

| Field | Required | Validation |
|-------|----------|------------|
| `metric_id` | yes | Must match a key in `metrics` or GT `extracted_values` |
| `doc_id` | yes | Must equal task `required_documents[].doc_id` (namespace lock) |
| `section_slug` | yes | Must exist in bundle `section_registry` for that doc |
| `snippet` | yes | Substring of bundle excerpt for that section (normalized) |
| `note`, `table_title`, `column` | recommended | Human audit; not auto-scored in v1 |

**File layout:**

| File | Purpose |
|------|---------|
| `{task_id}_run{NN}.json` | L1 `metrics` only — consumed by `verify_*.py` today |
| `{task_id}_run{NN}_submission.json` | Full submission (metrics + citations + acks) — L3 validator |
| `{task_id}_run{NN}_trace.json` | Tool trajectory — L2 section recall |

Campaign scorer and verify scripts unchanged for L1. `validate_agent_submission.py` (planned) reads `_submission.json`.

**Implementation status:** `validate_agent_submission.py` live; scripted + OpenAI agents emit `_submission.json`.

### Trajectory (L2 prep)

Sibling file:

```
{task_id}_run{NN}_trace.json
```

Required fields:

```json
{
  "trajectory_id": "...",
  "episode_or_task_id": "GOOGL_footnote_reconciliation",
  "track": "benchmark",
  "termination": "submit",
  "steps": [{"type": "tool_call", "tool": "Search_Filing", ...}],
  "tool_log": [...],
  "submission": { "structured_output": { ... } }
}
```

**No** `pm_turn` or `send_message_to_pm` steps.

---

## 6. Agent modes

| Mode | Purpose |
|------|---------|
| `scripted` | Replay JSON plan; calls tools + submit — **integration gate** |
| `mock` | Weak agent (GOOGL blind sum) — verify fails with fracture |
| `openai` | Deferred — stub raises NotImplementedError in v1 |

---

## 7. Verification gates

| Gate | Command / check |
|------|-----------------|
| B1 | `validate_corpus_bundle.py --task GOOGL_footnote_reconciliation` |
| B2 | `validate_corpus_bundle.py --task PEP_fx_organic_growth` |
| A1 | Loop writes contract paths; campaign scorer finds files |
| A2 | `benchmark_agent_loop.py --agent scripted` → output passes `verify_*` without copying `contract_fixtures/` |
| Merge | `scripts/smoke_test.py` includes both |
| B3 | `section_registry` ↔ gold_path ↔ retrieval_keys alignment (v1.1) |
| L3 | `validate_agent_submission.py` — doc_id + section_slug + policy ack (v1.1, planned) |

---

## 8. File ownership (parallel agents)

| Path | Owner |
|------|-------|
| `scripts/benchmark_agent_loop.py`, `benchmark_tool_backend.py` | Agent A |
| `examples/agents/*.json` | Agent A |
| `corpus/*_bundle.json`, `validate_corpus_bundle.py` | Agent B |
| `docs/CORPUS_BUNDLE_CONTRACT.md` | Frozen (this file) |
| `smoke_test.py` | Each agent adds **one** check function |
