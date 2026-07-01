#!/usr/bin/env python3
"""
Agent loop for env_v1 dual-control episodes.

Modes:
  scripted  — replay actions from a JSON plan (for P1-12 adapter testing)
  repl      — interactive stdin loop (manual tool calls + PM messages)

Demo trajectories (sample/partial/timeout) remain in run_episode.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pm_features import extract_pm_hints, infer_submission_fields  # noqa: E402
from tool_backend import ToolBackend, load_corpus  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pm_respond(policy: dict, pm_turn_count: int, steps: list[dict], tool_log: list[dict]) -> tuple[str, list[str], str]:
    """Select PM branch from extracted agent features."""
    hints = extract_pm_hints(steps, tool_log)
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


def build_trace(
    episode_id: str,
    agent_mode: str,
    termination: str,
    steps: list[dict],
    submission: dict,
    tool_log: list[dict],
    pm_flags: list[str],
    *,
    model_id: str | None = None,
    plan_id: str | None = None,
) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{agent_mode}_{episode_id}_{ts}"
    return {
        "trajectory_id": run_id,
        "episode_or_task_id": episode_id,
        "episode_id": episode_id,
        "run_id": run_id,
        "track": "env",
        "model_id": model_id,
        "agent_mode": agent_mode,
        "plan_id": plan_id,
        "termination": termination,
        "turns_used": len(steps),
        "pm_flags": pm_flags,
        "steps": steps,
        "submission": submission,
        "tool_log": tool_log,
    }


def execute_action(action: dict, backend: ToolBackend, steps: list[dict]) -> bool:
    """Execute one agent action. Returns False if episode should stop (submit)."""
    atype = action["type"]
    if atype == "tool_call":
        out = backend.call(action["tool"], **action.get("input", {}))
        doc_id = backend.log[-1].get("doc_id") if backend.log else None
        steps.append({
            "type": "tool_call",
            "tool": action["tool"],
            "input": action.get("input", {}),
            "output": out,
            "doc_id": doc_id,
        })
        return True
    if atype == "send_message_to_pm":
        steps.append({"type": "send_message_to_pm", "text": action["text"]})
        return True
    if atype == "submit_recommendation":
        sub = {k: v for k, v in action.items() if k != "type"}
        sub.setdefault("submitted", True)
        steps.append({"type": "submit_recommendation", **sub})
        return False
    raise ValueError(f"Unknown action type: {atype}")


def run_scripted_episode(
    episode_id: str,
    plan_path: Path,
    *,
    model_id: str | None = None,
) -> dict:
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = load_json(ep_path)
    policy = load_json((ep_path.parent / ep["pm_policy_ref"]).resolve())
    plan = load_json(plan_path)
    backend = ToolBackend(load_corpus(episode_id))

    max_turns = ep.get("execution_limits", {}).get("max_turns", 8)
    steps: list[dict] = []
    pm_flags: list[str] = []
    pm_turn_count = 0
    termination = "error"
    submission: dict = {}

    actions = list(plan["actions"])
    i = 0
    while i < len(actions):
        if len(steps) >= max_turns * 3:
            termination = "timeout"
            submission = infer_submission_fields(steps, backend.log)
            submission["submitted"] = False
            break

        action = actions[i]
        i += 1

        if action["type"] == "send_message_to_pm":
            steps.append({"type": "send_message_to_pm", "text": action["text"]})
            pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
            pm_turn_count += 1
            pm_flags.extend(flags)
            steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})
            if branch_id == "follow_up_b":
                steps.append({
                    "type": "pm_turn",
                    "text": policy["acceptance"]["message"],
                    "branch_id": "acceptance",
                })
            continue

        if action["type"] == "submit_recommendation":
            sub = {k: v for k, v in action.items() if k != "type"}
            sub.setdefault("submitted", True)
            steps.append({"type": "submit_recommendation", **sub})
            submission = sub
            termination = "submit"
            break

        cont = execute_action(action, backend, steps)
        if not cont:
            submission = infer_submission_fields(steps, backend.log)
            termination = "submit"
            break
    else:
        if termination == "error":
            submission = infer_submission_fields(steps, backend.log)
            if submission.get("submitted"):
                termination = "submit"
            else:
                termination = "timeout"

    return build_trace(
        episode_id,
        "scripted",
        termination,
        steps,
        submission,
        backend.log,
        pm_flags,
        model_id=model_id or plan.get("plan_id"),
        plan_id=plan.get("plan_id"),
    )


def run_repl_episode(episode_id: str) -> dict:
    """Interactive loop — type JSON actions, one per line. Empty line to finish."""
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = load_json(ep_path)
    policy = load_json((ep_path.parent / ep["pm_policy_ref"]).resolve())
    backend = ToolBackend(load_corpus(episode_id))
    max_turns = ep.get("execution_limits", {}).get("max_turns", 8)

    print(f"Episode: {episode_id} | REPL mode | max_turns≈{max_turns}")
    print("Action JSON (one line). Examples:")
    print('  {"type":"tool_call","tool":"get_filing","input":{"doc_type":"10-Q","period":"2025Q2"}}')
    print('  {"type":"send_message_to_pm","text":"Adjusted EPS $1.20 ..."}')
    print('  {"type":"submit_recommendation","adjusted_eps":1.2,"sale_leaseback_excluded":true,"submitted":true}')
    print("Empty line → end episode (timeout if no submit).\n")

    steps: list[dict] = []
    pm_flags: list[str] = []
    pm_turn_count = 0
    termination = "timeout"
    submission: dict = {"submitted": False}

    while len(steps) < max_turns * 3:
        try:
            line = input("agent> ").strip()
        except EOFError:
            break
        if not line:
            break
        action = json.loads(line)

        if action["type"] == "send_message_to_pm":
            steps.append({"type": "send_message_to_pm", "text": action["text"]})
            pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
            pm_turn_count += 1
            pm_flags.extend(flags)
            steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})
            print(f"pm> {pm_msg}")
            continue

        if action["type"] == "submit_recommendation":
            sub = {k: v for k, v in action.items() if k != "type"}
            sub.setdefault("submitted", True)
            steps.append({"type": "submit_recommendation", **sub})
            submission = sub
            termination = "submit"
            break

        execute_action(action, backend, steps)
        if backend.log:
            preview = backend.log[-1].get("output_preview", "")[:120]
            print(f"tool> {preview}...")

    if termination != "submit":
        submission = infer_submission_fields(steps, backend.log)
        submission["submitted"] = False

    return build_trace(episode_id, "repl", termination, steps, submission, backend.log, pm_flags)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run env_v1 agent loop")
    parser.add_argument("--episode", default="solaris_adj_eps_dispute_v1")
    parser.add_argument("--agent", choices=("scripted", "repl"), required=True)
    parser.add_argument("--plan", type=Path, help="JSON plan for scripted agent")
    parser.add_argument("--out", type=Path, help="Output trace path")
    parser.add_argument("--model-id", default=None)
    args = parser.parse_args()

    if args.agent == "scripted":
        if not args.plan:
            parser.error("--plan required for scripted agent")
        trace = run_scripted_episode(args.episode, args.plan, model_id=args.model_id)
    else:
        trace = run_repl_episode(args.episode)

    from run_episode import write_trace

    out = args.out or ROOT / "runs" / f"agent_{trace['agent_mode']}_{trace['run_id']}.json"
    write_trace(trace, out)


if __name__ == "__main__":
    main()
