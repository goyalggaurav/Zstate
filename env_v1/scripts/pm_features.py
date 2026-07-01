#!/usr/bin/env python3
"""Heuristic feature extraction from agent messages + tool log for PM FSM branching."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

PRIOR_YEAR_PATTERN = re.compile(
    r"FY20(?:23|24)|fiscal\s+20(?:23|24)|prior[-\s]year|last\s+year|\$0\.02|0\.02\s+per",
    re.IGNORECASE,
)
RD_EXCLUDE_PATTERN = re.compile(
    r"exclude.*?(?:R&D|rd\s+credit|tax\s+credit|true-up)|"
    r"(?:R&D|rd\s+credit).*?exclude|"
    r"adjusted\s+eps\s+\$?1\.20\b",
    re.IGNORECASE,
)
SALE_EXCLUDE_PATTERN = re.compile(
    r"exclude.*?(?:lease|sale-leaseback|0\.18)|(?:lease|sale-leaseback).*?(?:one-time|non-recurring|exclude)",
    re.IGNORECASE,
)
ADJ_EPS_PATTERN = re.compile(r"\$?(1\.(?:20|24|42|28))\b")


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def semantic_overlap(a: str, b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return len(wa & wb) / len(wa | wb)


def tool_doc_ids(steps: list[dict], tool_log: list[dict] | None = None) -> set[str]:
    ids: set[str] = set()
    for step in steps:
        if step.get("type") == "tool_call" and step.get("doc_id"):
            ids.add(step["doc_id"])
    if tool_log:
        for entry in tool_log:
            if entry.get("doc_id"):
                ids.add(entry["doc_id"])
    return ids


def extract_pm_hints(
    steps: list[dict],
    tool_log: list[dict] | None = None,
    *,
    overlap_threshold: float = 0.85,
) -> dict:
    """Derive PM FSM hints from agent messages and retrievals."""
    pm_msgs = [s.get("text", "") for s in steps if s.get("type") == "send_message_to_pm"]
    combined = " ".join(pm_msgs)
    doc_ids = tool_doc_ids(steps, tool_log)

    prior_docs = {"10-K_FY2024_footnote_rd", "10-K_FY2023_footnote_rd"}
    retrieved_prior = prior_docs.issubset(doc_ids)

    hints: dict = {
        "mentions_prior_year_pattern": bool(PRIOR_YEAR_PATTERN.search(combined)),
        "rd_credit_excluded": bool(RD_EXCLUDE_PATTERN.search(combined)),
        "sale_leaseback_excluded": bool(SALE_EXCLUDE_PATTERN.search(combined)),
        "retrieved_prior_year_footnotes": retrieved_prior,
        "substantive_reasoning": len(combined.split()) >= 25,
        "engagement_failure": False,
    }

    if len(pm_msgs) >= 2 and semantic_overlap(pm_msgs[-1], pm_msgs[-2]) >= overlap_threshold:
        # Repeated answer without new tool retrieval after last PM turn
        last_pm_idx = max(i for i, s in enumerate(steps) if s.get("type") == "pm_turn")
        new_tools_after = any(
            s.get("type") == "tool_call" for s in steps[last_pm_idx + 1 :]
        )
        if not new_tools_after:
            hints["engagement_failure"] = True

    eps_values = [float(m) for m in ADJ_EPS_PATTERN.findall(combined)]
    if eps_values:
        hints["mentioned_adjusted_eps"] = eps_values[-1]

    return hints


def infer_submission_fields(steps: list[dict], tool_log: list[dict] | None = None) -> dict:
    """Build submission dict from submit step or infer from last PM message."""
    for step in reversed(steps):
        if step.get("type") == "submit_recommendation":
            sub = {k: v for k, v in step.items() if k != "type"}
            sub.setdefault("submitted", True)
            return sub

    hints = extract_pm_hints(steps, tool_log)
    sub: dict = {
        "submitted": False,
        "adjusted_eps": hints.get("mentioned_adjusted_eps"),
        "sale_leaseback_excluded": hints.get("sale_leaseback_excluded", False),
        "mentions_prior_year_pattern": hints.get("mentions_prior_year_pattern", False),
        "retrieved_prior_year_footnotes": hints.get("retrieved_prior_year_footnotes", False),
    }
    if sub["adjusted_eps"] == 1.20:
        sub["rd_credit_treatment"] = "exclude_one_time"
    elif sub["adjusted_eps"] == 1.24:
        sub["rd_credit_treatment"] = "include_quasi_recurring"
    return sub
