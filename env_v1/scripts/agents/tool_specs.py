"""OpenAI-compatible tool definitions mapped to env_v1 ToolBackend + episode actions."""

from __future__ import annotations

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_filing",
            "description": "Retrieve an excerpt from a Solaris SEC filing in the fixed corpus.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string", "enum": ["10-Q", "10-K"]},
                    "period": {"type": "string", "description": "e.g. 2025Q2, FY2024, FY2023"},
                },
                "required": ["doc_type", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transcript",
            "description": "Retrieve the earnings call transcript excerpt for a period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "description": "e.g. 2025Q2"},
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_consensus",
            "description": "Retrieve sell-side consensus EPS and methodology note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": ["eps"]},
                    "period": {"type": "string", "description": "e.g. 2025Q2"},
                },
                "required": ["metric", "period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a numeric expression for adjusted EPS arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g. 1.42 - 0.18 - 0.04"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_pm",
            "description": "Send a brief to the portfolio manager with adjusted EPS view and reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_recommendation",
            "description": "Submit final adjusted EPS and classification. Ends the episode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "adjusted_eps": {"type": "number"},
                    "classification": {"type": "string"},
                    "rationale": {"type": "string"},
                    "sale_leaseback_excluded": {"type": "boolean"},
                    "rd_credit_treatment": {
                        "type": "string",
                        "enum": ["exclude_one_time", "include_quasi_recurring"],
                    },
                },
                "required": [
                    "adjusted_eps",
                    "classification",
                    "rationale",
                    "sale_leaseback_excluded",
                    "rd_credit_treatment",
                ],
            },
        },
    },
]

CORPUS_TOOLS = frozenset({"get_filing", "get_transcript", "get_consensus", "calculator"})
EPISODE_TOOLS = frozenset({"send_message_to_pm", "submit_recommendation"})
