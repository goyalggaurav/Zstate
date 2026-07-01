"""OpenAI-compatible tool definitions for Track A benchmark tasks."""

from __future__ import annotations

from agent_output_contract import googl_gold_values, pep_gold_values

CORPUS_TOOLS = frozenset({"Search_Filing", "PDF_Parser", "Python_Interpreter"})
SUBMIT_TOOL = "submit_structured_output"


def _metric_properties(task_id: str) -> dict[str, dict]:
    if task_id == "GOOGL_footnote_reconciliation":
        sample = googl_gold_values()
    elif task_id == "PEP_fx_organic_growth":
        sample = pep_gold_values()
    else:
        raise ValueError(f"No submit schema for task {task_id!r}")
    props: dict[str, dict] = {}
    for key, val in sample.items():
        props[key] = {"type": "integer" if isinstance(val, int) else "number"}
    return props


def metric_keys(task_id: str) -> set[str]:
    return set(_metric_properties(task_id).keys())


def parse_submission_args(args: dict, task: dict) -> tuple[dict, dict | None]:
    """Parse submit tool args into (metrics, agent_submission_v1 | None)."""
    task_id = task["task_id"]
    keys = metric_keys(task_id)

    if "metrics" in args:
        metrics = args["metrics"]
        if not isinstance(metrics, dict):
            raise ValueError("submit metrics must be an object")
        submission = {
            "schema_version": "agent_submission_v1",
            "metrics": metrics,
            "citations": args.get("citations") or [],
            "policy_acknowledgements": args.get("policy_acknowledgements") or [],
        }
        return metrics, submission

    if keys.intersection(args.keys()):
        metrics = {k: args[k] for k in keys if k in args}
        return metrics, None

    raise ValueError(f"submit_structured_output missing metrics for {task_id!r}")


def build_tool_definitions(task: dict, bundle: dict) -> list[dict]:
    task_id = task["task_id"]
    ticker = task["ticker"]
    period = task["required_documents"][0]["fiscal_period"]
    doc_ids = [doc["doc_id"] for doc in task.get("required_documents", []) if doc.get("doc_id")]
    section_slugs = [entry["section_slug"] for entry in bundle.get("section_registry", [])]
    section_enum = section_slugs or ["note_1"]
    policy_ids = [note["policy_id"] for note in bundle.get("policy_notes", [])]
    required_policy_ids = [
        note["policy_id"] for note in bundle.get("policy_notes", []) if note.get("agent_ack_required")
    ]

    search_params = {
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "enum": [ticker]},
            "period": {"type": "string", "enum": [period]},
            "section": {
                "type": "string",
                "enum": section_enum,
                "description": "Canonical section_slug from filing bundle (lowercase, e.g. note_15).",
            },
        },
        "required": ["ticker", "period", "section"],
    }

    metric_props = _metric_properties(task_id)
    metric_ids = sorted(metric_props.keys())
    n_metrics = len(metric_ids)
    citation_item = {
        "type": "object",
        "properties": {
            "metric_id": {"type": "string", "enum": metric_ids},
            "doc_id": {"type": "string", "enum": doc_ids or ["UNKNOWN"]},
            "section_slug": {"type": "string", "enum": section_enum},
            "snippet": {
                "type": "string",
                "description": "Verbatim substring copied from the retrieved section excerpt.",
            },
            "note": {"type": "string"},
            "table_title": {"type": "string"},
            "column": {"type": "string"},
        },
        "required": ["metric_id", "doc_id", "section_slug", "snippet"],
    }

    policy_schema: dict = {"type": "array", "items": {"type": "string"}}
    if policy_ids:
        policy_schema["items"] = {"type": "string", "enum": policy_ids}
    policy_desc = "policy_id tokens from bundle policy_notes[]"
    if required_policy_ids:
        policy_desc += f"; required: {', '.join(required_policy_ids)}"

    submit_required = ["metrics", "citations"]
    if required_policy_ids:
        submit_required.append("policy_acknowledgements")

    submit_params = {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "object",
                "description": f"Flat L1 numeric fields ({n_metrics} required keys).",
                "properties": metric_props,
                "required": metric_ids,
                "additionalProperties": False,
            },
            "citations": {
                "type": "array",
                "description": (
                    f"Exactly {n_metrics} citations — one per metrics key: {', '.join(metric_ids)}. "
                    "Each snippet must be copied verbatim from a retrieved section excerpt."
                ),
                "minItems": n_metrics,
                "maxItems": n_metrics,
                "items": citation_item,
            },
            "policy_acknowledgements": {
                **policy_schema,
                "description": policy_desc,
            },
        },
        "required": submit_required,
    }

    tools: list[dict] = [
        {
            "type": "function",
            "function": {
                "name": "Search_Filing",
                "description": "Retrieve a redacted filing section excerpt from the fixed corpus.",
                "parameters": search_params,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "PDF_Parser",
                "description": "Alias for Search_Filing — same section lookup.",
                "parameters": search_params,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "Python_Interpreter",
                "description": "Evaluate a numeric expression for reconciliation arithmetic.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "e.g. 89637 + 20028 + 411 + (-180)"},
                    },
                    "required": ["expression"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": SUBMIT_TOOL,
                "description": (
                    f"Submit final agent_submission_v1 with all {n_metrics} metrics, "
                    f"{n_metrics} citations (one per metric_id), and required policy acks. Ends the task."
                ),
                "parameters": submit_params,
            },
        },
    ]
    return tools
