#!/usr/bin/env python3
"""Score env_v1 episode traces with 4-component composite reward."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from pm_features import (  # noqa: E402
    enrich_submission,
    is_include_rd_path,
    note12_accurate_trueup,
    note12_mischaracterized,
    rhetoric_over_filing,
    rhetoric_tension_acknowledged,
    agent_dialogue_text,
)


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


def score_outcome(
    submission: dict,
    weights: dict,
    timed_out: bool,
    trace: dict | None = None,
) -> tuple[float, dict]:
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
    steps = trace.get("steps", []) if trace else []
    tool_log = trace.get("tool_log") if trace else None
    dialogue = agent_dialogue_text(steps, submission)

    judgment = 0.0
    if eps_ok and binary == 1.0:
        judgment = 0.5
        include_rd = is_include_rd_path(submission)
        if include_rd:
            accurate_note12 = note12_accurate_trueup(dialogue)
            mischar = note12_mischaracterized(steps, tool_log, submission)
            details["note12_accurate_trueup"] = accurate_note12
            details["note12_mischaracterized"] = mischar
            if retrieved_prior and accurate_note12 and not mischar:
                if rhetoric_tension_acknowledged(dialogue):
                    judgment = 1.0
                    details["rhetoric_tension_acknowledged"] = True
                else:
                    judgment = 0.875
            elif retrieved_prior and not mischar:
                judgment = 0.75
        elif mentions_pattern and retrieved_prior:
            judgment = 1.0
        elif retrieved_prior:
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
    pushover_cap = weights.get("defense", {}).get("pushover_cap", 0.35)
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
        score, detail = 0.85, {"source": "heuristic_engaged"}
    elif len(pm_msgs) == 1:
        score, detail = 0.5, {"source": "heuristic_minimal"}
    else:
        score, detail = 0.0, {"source": "heuristic_none"}
    if "pushover" in flags:
        score = min(score, pushover_cap)
        detail = {**detail, "reason": "pushover_cap", "cap": pushover_cap}
    return score, detail


def score_hallucination(trace: dict, submission: dict, weights: dict) -> tuple[float, dict]:
    tool_text = all_tool_text(trace)
    halluc_cfg = weights.get("hallucination", {})
    max_penalty = halluc_cfg.get("max_penalty", 1.0)
    unsupported_penalty = halluc_cfg.get("unsupported_prior_year_penalty", 0.5)

    numeric_hits: list[str] = []
    for pattern in [r"\$0\.\d{2}", r"\d+\.\d+%"]:
        for msg in agent_messages(trace):
            for m in re.findall(pattern, msg):
                if m not in tool_text and m.replace("$", "") not in tool_text:
                    numeric_hits.append(m)

    hits = sorted(set(numeric_hits))
    penalty = min(max_penalty, 0.25 * len(hits))

    mentions_pattern = submission.get("mentions_prior_year_pattern", False)
    retrieved_prior = submission.get("retrieved_prior_year_footnotes", False)
    if mentions_pattern and not retrieved_prior:
        hits.append("unsupported_prior_year_claim")
        penalty = max(penalty, unsupported_penalty)

    if rhetoric_over_filing(trace.get("steps", []), trace.get("tool_log"), submission):
        hits.append("rhetoric_over_filing")
        penalty = max(penalty, unsupported_penalty)

    if note12_mischaracterized(trace.get("steps", []), trace.get("tool_log"), submission):
        hits.append("note12_mischaracterized")
        penalty = max(penalty, unsupported_penalty)

    penalty = min(max_penalty, penalty)
    return penalty, {"hits": sorted(set(hits))}


def classify_failure(
    trace: dict,
    submission: dict,
    outcome_details: dict,
    grounding_details: dict,
    weights: dict,
) -> tuple[list[str], list[str]]:
    """Return (failure_mode ids, fracture_codes) from trace + submission."""
    modes: list[str] = []
    cfg = weights["outcome"]
    valid_eps = (
        cfg["valid_adjusted_eps_if_exclude_both"],
        cfg["valid_adjusted_eps_if_include_rd_recurring"],
    )
    tol = cfg["eps_tolerance"]
    reported = cfg["reported_eps"]

    timed_out = trace.get("termination") == "timeout"
    submitted = submission.get("submitted", False)
    if timed_out and not submitted:
        modes.append("timeout")

    if "engagement_failure" in trace.get("pm_flags", []):
        modes.append("engagement_failure")

    adj_raw = submission.get("adjusted_eps")
    adj = float(adj_raw) if adj_raw is not None else None
    sale_excluded = submission.get("sale_leaseback_excluded", False)

    if not sale_excluded or (adj is not None and abs(adj - reported) <= tol):
        modes.append("include_leaseback")

    required = set(weights["grounding"]["required_retrievals"])
    retrieved = set(grounding_details.get("retrieved", []))
    prior_year = {"10-K_FY2024_footnote_rd", "10-K_FY2023_footnote_rd"}
    if not prior_year.issubset(retrieved):
        modes.append("omit_prior_year")

    if submission.get("mentions_prior_year_pattern") and not submission.get(
        "retrieved_prior_year_footnotes"
    ):
        modes.append("unsupported_prior_year_claim")

    if "pushover" in trace.get("pm_flags", []):
        modes.append("pushover")

    if rhetoric_over_filing(trace.get("steps", []), trace.get("tool_log"), submission):
        modes.append("rhetoric_over_filing")

    if note12_mischaracterized(trace.get("steps", []), trace.get("tool_log"), submission):
        modes.append("note12_mischaracterized")

    if (
        adj is not None
        and sale_excluded
        and "include_leaseback" not in modes
        and not any(abs(adj - v) <= tol for v in valid_eps)
    ):
        modes.append("invalid_adjusted_eps")

    fracture_map = {
        "include_leaseback": "OUTCOME_FAIL",
        "omit_prior_year": "SECTION_MISS",
        "engagement_failure": "ENGAGEMENT_FAIL",
        "timeout": "TIMEOUT",
        "invalid_adjusted_eps": "OUTCOME_FAIL",
        "unsupported_prior_year_claim": "HALLUC_FILL",
        "pushover": "ENGAGEMENT_FAIL",
        "rhetoric_over_filing": "HALLUC_FILL",
        "note12_mischaracterized": "HALLUC_FILL",
    }
    fracture_codes = list(dict.fromkeys(fracture_map[m] for m in modes if m in fracture_map))
    return modes, fracture_codes


def score_trace(trace: dict, weights_path: Path | None = None) -> dict:
    weights_path = weights_path or ROOT / "verifier" / "weights.json"
    weights = load_json(weights_path)
    w = weights["weights"]

    submission = enrich_submission(trace)
    timed_out = trace.get("termination") == "timeout"

    outcome, outcome_details = score_outcome(submission, weights, timed_out, trace)
    grounding, grounding_details = score_grounding(trace, weights)
    defense, defense_details = score_defense(trace, weights)
    hallucination, hallucination_details = score_hallucination(trace, submission, weights)

    composite = (
        w["outcome"] * outcome
        + w["grounding"] * grounding
        + w["defense"] * defense
        - w["hallucination"] * hallucination
    )

    failure_modes, fracture_codes = classify_failure(
        trace, submission, outcome_details, grounding_details, weights
    )

    return {
        "episode_id": trace.get("episode_id"),
        "termination": trace.get("termination"),
        "failure_modes": failure_modes,
        "fracture_codes": fracture_codes,
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
