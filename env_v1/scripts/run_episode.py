#!/usr/bin/env python3
"""Run env_v1 dual-control episode — demo modes + shared trace write path."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pm_features import extract_pm_hints  # noqa: E402
from tool_backend import ToolBackend, load_corpus  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pm_respond(
    policy: dict,
    pm_turn_count: int,
    steps: list[dict],
    tool_log: list[dict],
    *,
    submission_hints: dict | None = None,
) -> tuple[str, list[str], str]:
    hints = submission_hints if submission_hints is not None else extract_pm_hints(steps, tool_log)
    flags: list[str] = []
    branch_id = "fallback_ood"

    if pm_turn_count == 0:
        branch_id = "opening_pushback"
    elif hints.get("engagement_failure"):
        branch_id = "follow_up_c"
    elif hints.get("mentions_prior_year_pattern") and hints.get("substantive_reasoning"):
        branch_id = "follow_up_b"
    elif hints.get("rd_credit_excluded") and not hints.get("mentions_prior_year_pattern"):
        branch_id = "follow_up_a"

    branch = next(b for b in policy["branches"] if b["branch_id"] == branch_id)
    flags = list(branch.get("flags", []))
    return branch["message"], flags, branch_id


def _episode_context(episode_id: str) -> tuple[dict, dict, ToolBackend]:
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = load_json(ep_path)
    policy = load_json((ep_path.parent / ep["pm_policy_ref"]).resolve())
    backend = ToolBackend(load_corpus(episode_id))
    return ep, policy, backend


def run_sample_episode(episode_id: str) -> dict:
    _, policy, backend = _episode_context(episode_id)
    steps: list[dict] = []
    pm_turn_count = 0
    pm_flags: list[str] = []

    def tool(name: str, **kwargs) -> None:
        out = backend.call(name, **kwargs)
        doc_id = backend.log[-1].get("doc_id") if backend.log else None
        steps.append({"type": "tool_call", "tool": name, "input": kwargs, "output": out, "doc_id": doc_id})

    tool("get_filing", doc_type="10-Q", period="2025Q2")
    tool("get_consensus", metric="eps", period="2025Q2")
    tool("get_filing", doc_type="10-K", period="FY2024")
    tool("get_filing", doc_type="10-K", period="FY2023")
    tool("calculator", expression="1.42 - 0.18 - 0.04")

    steps.append({
        "type": "send_message_to_pm",
        "text": (
            "Adjusted EPS $1.20. Excluding $0.18 sale-leaseback (Note 7, one-time) and $0.04 R&D credit true-up. "
            "FY2024 had a $0.02 similar true-up; FY2023 had none — pattern is intermittent, I exclude both for core earnings."
        ),
    })
    pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    pm_turn_count += 1
    pm_flags.extend(flags)
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})

    steps.append({
        "type": "send_message_to_pm",
        "text": (
            "Magnitude differs: FY2024 true-up was $0.02 vs $0.04 this quarter, and CFO stated true-ups depend on "
            "return finalization — not a steady operating item. Core view remains $1.20."
        ),
        "defense_score": 0.9,
    })
    pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    pm_flags.extend(flags)
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})
    if branch_id == "follow_up_b":
        steps.append({"type": "pm_turn", "text": policy["acceptance"]["message"], "branch_id": "acceptance"})

    submission = {
        "adjusted_eps": 1.20,
        "classification": "exclude_both_one_time_items",
        "rationale": "Sale-leaseback non-recurring per Note 7; R&D true-up disclosed with prior-year pattern analysis.",
        "sale_leaseback_excluded": True,
        "rd_credit_treatment": "exclude_one_time",
        "mentions_prior_year_pattern": True,
        "retrieved_prior_year_footnotes": True,
        "submitted": True,
    }
    steps.append({"type": "submit_recommendation", **submission})

    return _trace(episode_id, "sample", "submit", steps, submission, backend.log, pm_flags)


def run_partial_episode(episode_id: str) -> dict:
    _, policy, backend = _episode_context(episode_id)
    steps: list[dict] = []
    pm_turn_count = 0
    pm_flags: list[str] = []

    def tool(name: str, **kwargs) -> None:
        out = backend.call(name, **kwargs)
        doc_id = backend.log[-1].get("doc_id") if backend.log else None
        steps.append({"type": "tool_call", "tool": name, "input": kwargs, "output": out, "doc_id": doc_id})

    tool("get_filing", doc_type="10-Q", period="2025Q2")
    tool("get_consensus", metric="eps", period="2025Q2")
    tool("calculator", expression="1.42 - 0.18 - 0.04")

    repeat_msg = (
        "Adjusted EPS $1.20. I exclude the $0.18 sale-leaseback and $0.04 R&D credit per the 10-Q reconciliation."
    )
    steps.append({"type": "send_message_to_pm", "text": repeat_msg})
    pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    pm_turn_count += 1
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})

    steps.append({"type": "send_message_to_pm", "text": repeat_msg})
    pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    pm_flags.extend(flags)
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})

    submission = {
        "adjusted_eps": 1.20,
        "classification": "exclude_both_one_time_items",
        "rationale": "Excluded lease gain and R&D credit from 10-Q only.",
        "sale_leaseback_excluded": True,
        "rd_credit_treatment": "exclude_one_time",
        "mentions_prior_year_pattern": False,
        "retrieved_prior_year_footnotes": False,
        "submitted": True,
    }
    steps.append({"type": "submit_recommendation", **submission})

    return _trace(episode_id, "partial", "submit", steps, submission, backend.log, pm_flags)


def run_timeout_episode(episode_id: str) -> dict:
    _, policy, backend = _episode_context(episode_id)
    steps: list[dict] = []
    pm_turn_count = 0

    def tool(name: str, **kwargs) -> None:
        out = backend.call(name, **kwargs)
        doc_id = backend.log[-1].get("doc_id") if backend.log else None
        steps.append({"type": "tool_call", "tool": name, "input": kwargs, "output": out, "doc_id": doc_id})

    tool("get_filing", doc_type="10-Q", period="2025Q2")
    tool("get_transcript", period="2025Q2")
    tool("get_consensus", metric="eps", period="2025Q2")
    tool("get_filing", doc_type="10-K", period="FY2024")
    tool("calculator", expression="1.42 - 0.18")

    steps.append({
        "type": "send_message_to_pm",
        "text": "Still reviewing the beat components — lease gain is $0.18 per the 10-Q. Need more time before final adjusted EPS.",
    })
    pm_msg, _, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    pm_turn_count += 1
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})

    tool("get_filing", doc_type="10-K", period="FY2023")
    tool("calculator", expression="1.42 - 0.18 - 0.04")

    steps.append({
        "type": "send_message_to_pm",
        "text": "Working through the adjustments — will submit shortly.",
    })
    pm_msg, _, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
    steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})

    submission = {"submitted": False, "adjusted_eps": None, "sale_leaseback_excluded": False}

    return _trace(episode_id, "timeout", "timeout", steps, submission, backend.log, [], turns_used=8)


def _trace(
    episode_id: str,
    mode: str,
    termination: str,
    steps: list[dict],
    submission: dict,
    tool_log: list[dict],
    pm_flags: list[str],
    turns_used: int | None = None,
) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"sample_{mode}_{ts}"
    return {
        "trajectory_id": run_id,
        "episode_or_task_id": episode_id,
        "episode_id": episode_id,
        "run_id": run_id,
        "track": "env",
        "mode": mode,
        "agent_mode": mode,
        "termination": termination,
        "turns_used": turns_used or len(steps),
        "pm_flags": pm_flags,
        "steps": steps,
        "submission": submission,
        "tool_log": tool_log,
    }


MODES = {
    "sample": ("sample_trace_good.json", run_sample_episode),
    "partial": ("sample_trace_partial.json", run_partial_episode),
    "timeout": ("sample_trace_timeout.json", run_timeout_episode),
}


def write_trace(trace: dict, out_path: Path) -> dict:
    from score_episode import score_trace
    from trace_utils import enrich_env_trace, validate_trajectory_v1_minimal

    scores = score_trace(trace)
    enriched = enrich_env_trace(trace, scores)
    missing = validate_trajectory_v1_minimal(enriched)
    if missing:
        print(f"Warning: trajectory missing required fields: {missing}", file=sys.stderr)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
    print(f"Wrote trace: {out_path}")

    score_path = out_path.with_name(out_path.stem + "_scores.json")
    score_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    print(f"Wrote scores: {score_path}")
    print(json.dumps({"composite_reward": scores["composite_reward"], "fractures": scores["fracture_codes"]}, indent=2))
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Run env_v1 episode demo trajectories")
    parser.add_argument("--episode", default="solaris_adj_eps_dispute_v1")
    parser.add_argument("--mode", choices=[*MODES.keys(), "all"], default="sample")
    parser.add_argument("--out", default=None, help="Output path (single mode only)")
    args = parser.parse_args()

    if args.mode == "all":
        for mode, (filename, runner) in MODES.items():
            print(f"\n--- {mode} ---")
            trace = runner(args.episode)
            write_trace(trace, ROOT / "runs" / filename)
        return

    filename, runner = MODES[args.mode]
    trace = runner(args.episode)
    out_path = Path(args.out) if args.out else ROOT / "runs" / filename
    write_trace(trace, out_path)


if __name__ == "__main__":
    main()
