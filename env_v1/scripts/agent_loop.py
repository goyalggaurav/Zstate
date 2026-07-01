#!/usr/bin/env python3
"""
Agent loop for env_v1 dual-control episodes.

Agent modes:
  scripted  — replay JSON plan (regression / gold path)
  repl      — interactive stdin
  mock      — deterministic weak agent (offline, no API key)
  openai    — OpenAI-compatible chat + tools (OPENAI_API_KEY required)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pm_features import extract_pm_hints, infer_submission_fields  # noqa: E402
from pm_fsm import pm_respond, should_append_acceptance  # noqa: E402
from tool_backend import ToolBackend, load_corpus  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class StepAgent(Protocol):
    def next_action(self, context: dict[str, Any]) -> dict | None: ...


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


def run_agent_episode(
    episode_id: str,
    agent: StepAgent,
    *,
    agent_mode: str,
    model_id: str | None = None,
    plan_id: str | None = None,
) -> dict:
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = load_json(ep_path)
    policy = load_json((ep_path.parent / ep["pm_policy_ref"]).resolve())
    backend = ToolBackend(load_corpus(episode_id))
    max_steps = ep.get("execution_limits", {}).get("max_turns", 8) * 3

    steps: list[dict] = []
    pm_flags: list[str] = []
    pm_turn_count = 0
    termination = "timeout"
    submission: dict = {"submitted": False}
    context: dict[str, Any] = {"episode": ep, "steps": steps}

    while len(steps) < max_steps:
        action = agent.next_action(context)
        if action is None:
            break

        if action["type"] == "tool_call":
            tool = action["tool"]
            inp = action.get("input", {})
            out = backend.call(tool, **inp)
            doc_id = backend.log[-1].get("doc_id") if backend.log else None
            steps.append({
                "type": "tool_call",
                "tool": tool,
                "input": inp,
                "output": out,
                "doc_id": doc_id,
            })
            if hasattr(agent, "record_tool_result"):
                agent.record_tool_result(action.get("_tool_call_id"), tool, out)
            context["steps"] = steps
            continue

        if action["type"] == "send_message_to_pm":
            if hasattr(agent, "record_tool_result") and action.get("_tool_call_id"):
                agent.record_tool_result(
                    action["_tool_call_id"], "send_message_to_pm", "Message delivered to PM."
                )
            steps.append({"type": "send_message_to_pm", "text": action["text"]})
            pm_msg, flags, branch_id = pm_respond(policy, pm_turn_count, steps, backend.log)
            pm_turn_count += 1
            pm_flags.extend(flags)
            steps.append({"type": "pm_turn", "text": pm_msg, "branch_id": branch_id})
            if should_append_acceptance(policy, branch_id):
                steps.append({
                    "type": "pm_turn",
                    "text": policy["acceptance"]["message"],
                    "branch_id": "acceptance",
                })
            if hasattr(agent, "record_pm_message"):
                agent.record_pm_message(pm_msg)
            context["steps"] = steps
            continue

        if action["type"] == "submit_recommendation":
            if hasattr(agent, "record_tool_result") and action.get("_tool_call_id"):
                agent.record_tool_result(
                    action["_tool_call_id"], "submit_recommendation", "Recommendation submitted."
                )
            sub = {k: v for k, v in action.items() if k not in ("type", "_tool_call_id")}
            sub.setdefault("submitted", True)
            steps.append({"type": "submit_recommendation", **sub})
            submission = sub
            termination = "submit"
            break

        raise ValueError(f"Unknown action: {action}")

    if termination != "submit":
        submission = infer_submission_fields(steps, backend.log)
        submission["submitted"] = False
    else:
        hints = extract_pm_hints(steps, backend.log)
        for key in (
            "mentions_prior_year_pattern",
            "retrieved_prior_year_footnotes",
            "sale_leaseback_excluded",
        ):
            submission.setdefault(key, hints.get(key, False))

    return build_trace(
        episode_id,
        agent_mode,
        termination,
        steps,
        submission,
        backend.log,
        pm_flags,
        model_id=model_id,
        plan_id=plan_id,
    )


def run_scripted_episode(episode_id: str, plan_path: Path, *, model_id: str | None = None) -> dict:
    plan = load_json(plan_path)

    class _PlanAgent:
        def __init__(self) -> None:
            self.i = 0
            self.actions = plan["actions"]

        def next_action(self, _context: dict) -> dict | None:
            if self.i >= len(self.actions):
                return None
            action = self.actions[self.i]
            self.i += 1
            return action

    return run_agent_episode(
        episode_id,
        _PlanAgent(),
        agent_mode="scripted",
        model_id=model_id or plan.get("plan_id"),
        plan_id=plan.get("plan_id"),
    )


def run_repl_episode(episode_id: str) -> dict:
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = load_json(ep_path)
    max_turns = ep.get("execution_limits", {}).get("max_turns", 8)
    print(f"Episode: {episode_id} | REPL | max_steps≈{max_turns * 3}")
    print('Actions: {"type":"tool_call",...} | send_message_to_pm | submit_recommendation\n')

    class _ReplAgent:
        def next_action(self, _context: dict) -> dict | None:
            try:
                line = input("agent> ").strip()
            except EOFError:
                return None
            if not line:
                return None
            return json.loads(line)

    return run_agent_episode(episode_id, _ReplAgent(), agent_mode="repl")


def run_mock_episode(episode_id: str) -> dict:
    from agents.mock_agent import MockWeakAgent

    agent = MockWeakAgent()
    return run_agent_episode(
        episode_id,
        agent,
        agent_mode="mock",
        model_id="mock_weak_v1",
        plan_id=agent.plan_id,
    )


def run_openai_episode(episode_id: str, *, model: str | None = None) -> dict:
    from agents.openai_agent import OpenAICompatAgent

    ep = load_json(ROOT / "episodes" / f"{episode_id}.json")
    agent = OpenAICompatAgent(ep, model=model)

    class _OpenAIWrapper:
        def __init__(self, inner: OpenAICompatAgent) -> None:
            self.inner = inner

        def next_action(self, context: dict) -> dict | None:
            return self.inner.next_action(context)

        def record_tool_result(self, tool_call_id: str | None, name: str, output: str) -> None:
            self.inner.record_tool_result(tool_call_id, name, output)

        def record_pm_message(self, text: str) -> None:
            self.inner.messages.append({"role": "user", "content": f"Portfolio Manager: {text}"})

    wrapped = _OpenAIWrapper(agent)
    return run_agent_episode(
        episode_id,
        wrapped,
        agent_mode="openai",
        model_id=agent.model,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run env_v1 agent loop")
    parser.add_argument("--episode", default="solaris_adj_eps_dispute_v1")
    parser.add_argument(
        "--agent",
        choices=("scripted", "repl", "mock", "openai"),
        required=True,
    )
    parser.add_argument("--plan", type=Path, help="JSON plan for scripted agent")
    parser.add_argument("--out", type=Path, help="Output trace path")
    parser.add_argument("--model-id", default=None, help="LLM model id (openai agent)")
    args = parser.parse_args()

    if args.agent == "scripted":
        if not args.plan:
            parser.error("--plan required for scripted agent")
        trace = run_scripted_episode(args.episode, args.plan, model_id=args.model_id)
    elif args.agent == "repl":
        trace = run_repl_episode(args.episode)
    elif args.agent == "mock":
        trace = run_mock_episode(args.episode)
    else:
        trace = run_openai_episode(args.episode, model=args.model_id)

    from run_episode import write_trace

    out = args.out or ROOT / "runs" / f"agent_{trace['agent_mode']}_{trace['run_id']}.json"
    write_trace(trace, out)


if __name__ == "__main__":
    main()
