#!/usr/bin/env python3
"""
Track A benchmark agent loop — scripted replay and mock weak agent.

No PM FSM (no pm_turn / send_message_to_pm). Writes structured output + trajectory trace.

Usage:
  python benchmark_agent_loop.py --agent scripted --task GOOGL_footnote_reconciliation \\
    --plan ../examples/agents/googl_good_plan.json --out-dir /tmp/bench --run-index 1
  python benchmark_agent_loop.py --agent mock --task GOOGL_footnote_reconciliation \\
    --out-dir /tmp/bench --run-index 2
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import agent_output_path, amzn_gold_submission, googl_gold_submission, load_json, pep_gold_submission, resolve_bench_path  # noqa: E402
from benchmark_tool_backend import BenchmarkToolBackend, load_bundle  # noqa: E402


class StepAgent(Protocol):
    def next_action(self, context: dict[str, Any]) -> dict | None: ...


def load_task(task_id: str) -> dict:
    path = BENCH / "tasks" / f"{task_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Task not found: {path}")
    task = load_json(path)
    if task["task_id"] != task_id:
        raise ValueError(f"Task file {path.name} has task_id {task['task_id']!r}, expected {task_id!r}")
    return task


def resolve_output_paths(
    task_id: str,
    run_index: int,
    *,
    out_dir: Path | None,
    campaign: dict | None,
    model_id: str | None,
) -> tuple[Path, Path]:
    stem = f"{task_id}_run{run_index:02d}"
    if out_dir is not None:
        base = out_dir.resolve()
        return base / f"{stem}.json", base / f"{stem}_trace.json"
    if campaign is None or model_id is None:
        raise ValueError("--out-dir or (--campaign and --model-id) required for output paths")
    agent_path = agent_output_path(campaign, model_id, task_id, run_index)
    trace_path = agent_path.with_name(f"{stem}_trace.json")
    return agent_path, trace_path


def build_trace(
    task_id: str,
    agent_mode: str,
    termination: str,
    steps: list[dict],
    submission: dict,
    tool_log: list[dict],
    *,
    model_id: str | None = None,
    plan_id: str | None = None,
) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{agent_mode}_{task_id}_{ts}"
    return {
        "trajectory_id": run_id,
        "episode_or_task_id": task_id,
        "run_id": run_id,
        "track": "benchmark",
        "model_id": model_id,
        "agent_mode": agent_mode,
        "plan_id": plan_id,
        "termination": termination,
        "turns_used": len(steps),
        "steps": steps,
        "tool_log": tool_log,
        "submission": submission,
    }


def run_benchmark_task(
    task_id: str,
    agent: StepAgent,
    *,
    agent_mode: str,
    model_id: str | None = None,
    plan_id: str | None = None,
) -> tuple[dict, dict]:
    task = load_task(task_id)
    backend = BenchmarkToolBackend(load_bundle(task_id))
    max_steps = task.get("execution_limits", {}).get("max_tool_calls", 30) + 5

    steps: list[dict] = []
    termination = "timeout"
    submission: dict = {"submitted": False}
    structured_output: dict | None = None
    agent_submission: dict | None = None
    context: dict[str, Any] = {"task": task, "steps": steps}

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

        if action["type"] == "agent_message":
            steps.append({"type": "agent_message", "text": action.get("text", "")})
            context["steps"] = steps
            continue

        if action["type"] == "submit_structured_output":
            if hasattr(agent, "record_tool_result") and action.get("_tool_call_id"):
                agent.record_tool_result(
                    action["_tool_call_id"],
                    "submit_structured_output",
                    "Structured output submitted.",
                )
            structured_output = action.get("structured_output", action.get("values", {}))
            agent_submission = action.get("submission")
            if agent_submission and isinstance(agent_submission.get("metrics"), dict):
                structured_output = agent_submission["metrics"]
            submission = {"submitted": True, "structured_output": structured_output}
            if agent_submission:
                submission["agent_submission"] = agent_submission
            steps.append({
                "type": "submit_structured_output",
                "structured_output": structured_output,
                "has_submission": agent_submission is not None,
            })
            termination = "submit"
            break

        raise ValueError(f"Unknown action type: {action['type']!r}")

    trace = build_trace(
        task_id,
        agent_mode,
        termination,
        steps,
        submission,
        backend.log,
        model_id=model_id,
        plan_id=plan_id,
    )
    if structured_output is None:
        structured_output = {}
    return trace, structured_output, agent_submission


def _ensure_plan_submission(task_id: str, plan: dict) -> None:
    actions = plan.get("actions", [])
    if not actions or actions[-1].get("type") != "submit_structured_output":
        return
    if actions[-1].get("submission"):
        return
    builders = {
        "GOOGL_footnote_reconciliation": googl_gold_submission,
        "PEP_fx_organic_growth": pep_gold_submission,
        "AMZN_footnote_reconciliation": amzn_gold_submission,
    }
    builder = builders.get(task_id)
    if builder:
        actions[-1]["submission"] = builder()


def run_scripted_task(
    task_id: str,
    plan_path: Path,
    *,
    model_id: str | None = None,
) -> tuple[dict, dict, dict | None]:
    plan = load_json(plan_path)
    _ensure_plan_submission(task_id, plan)

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

    return run_benchmark_task(
        task_id,
        _PlanAgent(),
        agent_mode="scripted",
        model_id=model_id or plan.get("model_id"),
        plan_id=plan.get("plan_id"),
    )


class MockBlindSumAgent:
    """Weak GOOGL agent — sums segments, omits hedging reconciling item."""

    plan_id = "mock_blind_sum_v1"

    def __init__(self, task: dict) -> None:
        self.task = task
        self._step = 0
        ticker = task["ticker"]
        period = task["required_documents"][0]["fiscal_period"]
        self._actions: list[dict] = [
            {
                "type": "tool_call",
                "tool": "Search_Filing",
                "input": {"ticker": ticker, "period": period, "section": "segment_financials"},
            },
            {
                "type": "tool_call",
                "tool": "Search_Filing",
                "input": {"ticker": ticker, "period": period, "section": "revenue_disaggregation"},
            },
            {
                "type": "tool_call",
                "tool": "Python_Interpreter",
                "input": {"expression": "89637 + 20028 + 411"},
            },
            {
                "type": "submit_structured_output",
                "structured_output": {
                    "google_services_revenue": 89_637,
                    "google_cloud_revenue": 20_028,
                    "other_bets_revenue": 411,
                    "hedging_gains_losses": None,
                    "consolidated_total_revenue": 110_076,
                },
            },
        ]

    def next_action(self, _context: dict[str, Any]) -> dict | None:
        if self._step >= len(self._actions):
            return None
        action = self._actions[self._step]
        self._step += 1
        return action


def run_mock_task(task_id: str) -> tuple[dict, dict, dict | None]:
    if task_id != "GOOGL_footnote_reconciliation":
        raise NotImplementedError(f"mock agent supports GOOGL_footnote_reconciliation only, got {task_id!r}")
    task = load_task(task_id)
    agent = MockBlindSumAgent(task)
    return run_benchmark_task(
        task_id,
        agent,
        agent_mode="mock",
        model_id="mock_blind_sum_v1",
        plan_id=agent.plan_id,
    )


def run_openai_task(
    task_id: str,
    *,
    model_id: str | None = None,
    eval_mode: bool | None = None,
) -> tuple[dict, dict, dict | None]:
    from agents.openai_benchmark_agent import OpenAIBenchmarkAgent

    task = load_task(task_id)
    bundle = load_bundle(task_id)
    agent = OpenAIBenchmarkAgent(task, bundle, model=model_id, eval_mode=eval_mode)
    return run_benchmark_task(
        task_id,
        agent,
        agent_mode="openai",
        model_id=agent.model,
        plan_id=None,
    )


def run_anthropic_task(
    task_id: str,
    *,
    model_id: str | None = None,
    eval_mode: bool | None = None,
) -> tuple[dict, dict, dict | None]:
    from agents.anthropic_benchmark_agent import AnthropicBenchmarkAgent

    task = load_task(task_id)
    bundle = load_bundle(task_id)
    agent = AnthropicBenchmarkAgent(task, bundle, model=model_id, eval_mode=eval_mode)
    return run_benchmark_task(
        task_id,
        agent,
        agent_mode="anthropic",
        model_id=agent.model,
        plan_id=None,
    )


def run_live_task(
    task_id: str,
    *,
    model_id: str | None = None,
    eval_mode: bool | None = None,
) -> tuple[dict, dict, dict | None, str]:
    from agents.benchmark_tool_specs import is_anthropic_model

    if model_id and is_anthropic_model(model_id):
        trace, structured_output, agent_submission = run_anthropic_task(
            task_id, model_id=model_id, eval_mode=eval_mode
        )
        return trace, structured_output, agent_submission, "anthropic"
    trace, structured_output, agent_submission = run_openai_task(
        task_id, model_id=model_id, eval_mode=eval_mode
    )
    return trace, structured_output, agent_submission, "openai"


TASK_SCRIPTED_PLANS: dict[str, Path] = {
    "GOOGL_footnote_reconciliation": BENCH / "examples/agents/googl_good_plan.json",
    "PEP_fx_organic_growth": BENCH / "examples/agents/pep_good_plan.json",
    "AMZN_footnote_reconciliation": BENCH / "examples/agents/amzn_good_plan.json",
}


def write_outputs(
    structured_output: dict,
    trace: dict,
    agent_path: Path,
    trace_path: Path,
    *,
    agent_submission: dict | None = None,
) -> None:
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text(json.dumps(structured_output, indent=2) + "\n", encoding="utf-8")
    trace_path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote agent output: {agent_path}")
    print(f"Wrote trace: {trace_path}")
    if agent_submission is not None:
        submission_path = agent_path.with_name(f"{agent_path.stem}_submission.json")
        submission_path.write_text(json.dumps(agent_submission, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote submission: {submission_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run benchmark_v0.1 Track A agent loop")
    parser.add_argument("--task", required=True, help="Task id, e.g. GOOGL_footnote_reconciliation")
    parser.add_argument(
        "--agent",
        choices=("scripted", "mock", "openai", "anthropic", "auto"),
        required=True,
    )
    parser.add_argument("--plan", type=Path, help="JSON plan for scripted agent")
    parser.add_argument("--out-dir", type=Path, help="Output directory (smoke tests / ad hoc runs)")
    parser.add_argument("--campaign", type=Path, help="Campaign JSON for contract output paths")
    parser.add_argument("--model-id", default=None, help="Model id for campaign output path")
    parser.add_argument("--run-index", type=int, default=1, help="Run index NN in output filename")
    args = parser.parse_args()

    campaign = None
    if args.campaign:
        campaign = load_json(resolve_bench_path(args.campaign))

    agent_submission: dict | None = None
    if args.agent == "scripted":
        if not args.plan:
            parser.error("--plan required for scripted agent")
        plan_path = args.plan.resolve() if args.plan.is_absolute() else (
            args.plan.resolve() if args.plan.exists() else (BENCH / args.plan).resolve()
        )
        trace, structured_output, agent_submission = run_scripted_task(
            args.task, plan_path, model_id=args.model_id
        )
    elif args.agent == "mock":
        trace, structured_output, agent_submission = run_mock_task(args.task)
    elif args.agent == "anthropic":
        trace, structured_output, agent_submission = run_anthropic_task(args.task, model_id=args.model_id)
    elif args.agent == "auto":
        trace, structured_output, agent_submission, _mode = run_live_task(args.task, model_id=args.model_id)
    else:
        trace, structured_output, agent_submission = run_openai_task(args.task, model_id=args.model_id)

    agent_path, trace_path = resolve_output_paths(
        args.task,
        args.run_index,
        out_dir=args.out_dir,
        campaign=campaign,
        model_id=args.model_id,
    )
    write_outputs(structured_output, trace, agent_path, trace_path, agent_submission=agent_submission)
    return 0


if __name__ == "__main__":
    sys.exit(main())
