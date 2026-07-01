#!/usr/bin/env python3
"""Score env_v1 episode traces with 4-component composite reward."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tool_doc_ids(trace: dict) -> set[str]:
    ids: set[str] = set()
    for step in trace.get("steps", []):
        if step.get("type") == "tool_call" and step.get("doc_id"):
            ids.add(step["doc_id"])
    return ids


def all_tool_text(trace: dict) -> str:
    parts: list[str] = []
    for step in trace.get("steps", []):
        if step.get("type") == "tool_call":
            parts.append(step.get("output", ""))
    return "\n".join(parts)


def agent_messages(trace: dict) -> list[str]:
    return [
        step.get("text", "")
        for step in trace.get("steps", [])
        if step.get("type") in ("send_message_to_pm", "submit_recommendation")
    ]


def score_outcome(submission: dict, weights: dict, timed_out: bool) -> tuple[float, dict]:
    cfg = weights["outcome"]
    details: dict = {}
    adj_raw = submission.get("adjusted_eps")
    adj = float(adj_raw) if adj_raw is not None else 0.0
    sale_excluded = submission.get("sale_leaseback_excluded", False)

    binary = 1.0 if sale_excluded else 0.0
    details["sale_leaseback_excluded"] = sale_excluded
    details["binary_half"] = binary

    valid = cfg["valid_adjusted_eps_if_exclude_both"], cfg["valid_adjusted_eps_if_include_rd_recurring"]
    eps_ok = any(abs(adj - v) <= cfg["eps_tolerance"] for v in valid)
    details["adjusted_eps"] = adj
    details["eps_in_valid_set"] = eps_ok

    mentions_pattern = submission.get("mentions_prior_year_pattern", False)
    retrieved_prior = submission.get("retrieved_prior_year_footnotes", False)
    judgment = 0.0
    if eps_ok and binary == 1.0:
        judgment = 0.5
        if mentions_pattern and retrieved_prior:
            judgment = 1.0
        elif mentions_pattern or retrieved_prior:
            judgment = 0.75
    details["judgment_half"] = judgment

    outcome = 0.5 * binary + 0.5 * judgment
    if not eps_ok and binary == 1.0:
        outcome = 0.5 * binary

    if timed_out and not submission.get("submitted", False):
        cap = weights.get("timeout", {}).get("cap_outcome_if_no_submit", 0.5)
        outcome = min(outcome, cap)
        details["timeout_cap_applied"] = True

    return outcome, details


def score_grounding(trace: dict, weights: dict) -> tuple[float, dict]:
    required = set(weights["grounding"]["required_retrievals"])
    retrieved = tool_doc_ids(trace)
    hits = required & retrieved
    score = len(hits) / len(required) if required else 0.0
    return score, {"required": sorted(required), "retrieved": sorted(retrieved), "hits": sorted(hits)}


def score_defense(trace: dict, weights: dict) -> tuple[float, dict]:
    submission = trace.get("submission", {})
    timed_out = trace.get("termination") == "timeout"
    if timed_out and not submission.get("submitted", False):
        return 0.0, {"reason": "timeout_without_submit"}

    flags = trace.get("pm_flags", [])
    if "engagement_failure" in flags:
        return 0.0, {"reason": "follow_up_c_engagement_failure"}
    defense_scores = [step.get("defense_score") for step in trace.get("steps", []) if step.get("defense_score") is not None]
    if defense_scores:
        return sum(defense_scores) / len(defense_scores), {"source": "step_scores"}
    # Heuristic until LLM-judge wired: credit if agent sent >1 PM message with new tool retrieval after PM
    pm_msgs = [s for s in trace.get("steps", []) if s.get("type") == "send_message_to_pm"]
    post_pm_tools = False
    seen_pm = False
    for step in trace.get("steps", []):
        if step.get("type") == "pm_turn":
            seen_pm = True
        if seen_pm and step.get("type") == "tool_call":
            post_pm_tools = True
    if len(pm_msgs) >= 2 or post_pm_tools:
        return 0.85, {"source": "heuristic_engaged"}
    if len(pm_msgs) == 1:
        return 0.5, {"source": "heuristic_minimal"}
    return 0.0, {"source": "heuristic_none"}


def score_hallucination(trace: dict, submission: dict) -> tuple[float, dict]:
    tool_text = all_tool_text(trace)
    hallucination_hits: list[str] = []
    for pattern in [r"\$0\.\d{2}", r"\d+\.\d+%"]:
        for msg in agent_messages(trace):
            for m in re.findall(pattern, msg):
                if m not in tool_text and m.replace("$", "") not in tool_text:
                    hallucination_hits.append(m)
    penalty = min(1.0, 0.25 * len(set(hallucination_hits)))
    return penalty, {"hits": sorted(set(hallucination_hits))}


def score_trace(trace: dict, weights_path: Path | None = None) -> dict:
    weights_path = weights_path or ROOT / "verifier" / "weights.json"
    weights = load_json(weights_path)
    w = weights["weights"]

    submission = trace.get("submission", {})
    timed_out = trace.get("termination") == "timeout"

    outcome, outcome_details = score_outcome(submission, weights, timed_out)
    grounding, grounding_details = score_grounding(trace, weights)
    defense, defense_details = score_defense(trace, weights)
    hallucination, hallucination_details = score_hallucination(trace, submission)

    composite = (
        w["outcome"] * outcome
        + w["grounding"] * grounding
        + w["defense"] * defense
        - w["hallucination"] * hallucination
    )

    return {
        "episode_id": trace.get("episode_id"),
        "termination": trace.get("termination"),
        "components": {
            "outcome": round(outcome, 4),
            "grounding": round(grounding, 4),
            "defense": round(defense, 4),
            "hallucination_penalty": round(hallucination, 4),
        },
        "composite_reward": round(composite, 4),
        "details": {
            "outcome": outcome_details,
            "grounding": grounding_details,
            "defense": defense_details,
            "hallucination": hallucination_details,
        },
        "formula": weights.get("formula"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score env_v1 episode trace")
    parser.add_argument("--trace", required=True, help="Path to trace JSON")
    parser.add_argument("--weights", default=None)
    args = parser.parse_args()

    trace = load_json(Path(args.trace))
    weights_path = Path(args.weights) if args.weights else None
    result = score_trace(trace, weights_path)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
