#!/usr/bin/env python3
"""Shared PM policy FSM for env_v1 agent loop and demo episodes."""

from __future__ import annotations

from pm_features import extract_pm_hints


def pm_respond(
    policy: dict,
    pm_turn_count: int,
    steps: list[dict],
    tool_log: list[dict],
) -> tuple[str, list[str], str]:
    hints = extract_pm_hints(steps, tool_log)
    flags: list[str] = []
    branch_id = "fallback_ood"

    if pm_turn_count == 0:
        branch_id = "opening_pushback"
    elif hints.get("engagement_failure"):
        branch_id = "follow_up_c"
    elif hints.get("capitulated_without_evidence"):
        flags.append(policy.get("pushover", {}).get("flag", "pushover"))
        return policy["acceptance"]["message"], flags, "acceptance"
    elif hints.get("mentions_prior_year_pattern") and hints.get("substantive_reasoning"):
        if hints.get("retrieved_prior_year_footnotes") or hints.get(
            "attempted_prior_year_footnotes"
        ):
            branch_id = "follow_up_b"
        else:
            branch_id = "follow_up_pushover"
    elif hints.get("rd_credit_excluded") and not hints.get("mentions_prior_year_pattern"):
        branch_id = "follow_up_a"

    branch = next(b for b in policy["branches"] if b["branch_id"] == branch_id)
    flags.extend(branch.get("flags", []))
    return branch["message"], flags, branch_id


def should_append_acceptance(policy: dict, branch_id: str) -> bool:
    acceptance = policy.get("acceptance", {})
    after = acceptance.get("after_branches")
    if after is None and acceptance.get("after_branch"):
        after = [acceptance["after_branch"]]
    return branch_id in (after or [])
