"""OpenAI-compatible tool definitions for Track A benchmark tasks."""

from __future__ import annotations

from agent_output_contract import googl_gold_values, pep_gold_values

CORPUS_TOOLS = frozenset({"Search_Filing", "PDF_Parser", "Python_Interpreter"})


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


def build_tool_definitions(task: dict, bundle: dict) -> list[dict]:
    task_id = task["task_id"]
    ticker = task["ticker"]
    period = task["required_documents"][0]["fiscal_period"]
    section_slugs = [entry["section_slug"] for entry in bundle.get("section_registry", [])]
    section_enum = section_slugs or ["note_1"]

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
    ]

    metric_props = _metric_properties(task_id)
    tools.append({
        "type": "function",
        "function": {
            "name": "submit_structured_output",
            "description": "Submit final structured numeric output for Layer 1 scoring. Ends the task.",
            "parameters": {
                "type": "object",
                "properties": metric_props,
                "required": list(metric_props.keys()),
            },
        },
    })
    return tools
