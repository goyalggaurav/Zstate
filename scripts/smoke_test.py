#!/usr/bin/env python3
"""Smoke tests for Track A L1 verify + Track B scoring + trajectory schema."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return json.loads(result.stdout)


def check_googl_gt() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
        "--period", "q1_2026",
    ])
    assert report["all_pass"] is True, report
    assert report["fracture_codes"] == []


def check_pep_fx_gt() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py",
    ])
    assert report["all_pass"] is True, report
    assert report["fracture_codes"] == []


def check_corpus_manifest() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_corpus_manifest.py",
    ])
    assert report["all_pass"] is True, report
    assert report["pilot_tickers"] == 5


def check_pm_fsm_fallback_escalation() -> None:
    sys.path.insert(0, str(ROOT / "env_v1" / "scripts"))
    from pm_fsm import pm_respond  # noqa: E402

    policy = json.loads((ROOT / "env_v1" / "pm_policies" / "pm_v1_1.json").read_text())
    steps = [
        {"type": "send_message_to_pm", "text": "Adjusted EPS is $1.24 excluding leaseback."},
        {"type": "pm_turn", "text": "opening", "branch_id": "opening_pushback"},
        {
            "type": "send_message_to_pm",
            "text": "Note 7 and Note 12 support the adjustment from the 10-Q reconciliation table.",
        },
        {"type": "pm_turn", "text": "fallback first", "branch_id": "fallback_ood"},
        {
            "type": "send_message_to_pm",
            "text": "Note 7 and Note 12 support the adjustment from the 10-Q reconciliation table again.",
        },
    ]
    _, _, branch_id = pm_respond(policy, pm_turn_count=2, steps=steps, tool_log=[])
    assert branch_id == "follow_up_c", branch_id


def check_env_traces() -> None:
    sys.path.insert(0, str(ROOT / "env_v1" / "scripts"))
    from score_episode import score_trace  # noqa: E402
    from trace_utils import enrich_env_trace, validate_trajectory_v1_minimal  # noqa: E402

    expectations = {
        "sample_trace_good.json": {"composite_min": 0.85, "fractures": []},
        "sample_trace_partial.json": {"composite_max": 0.50, "fractures_nonempty": True},
        "sample_trace_timeout.json": {"composite_max": 0.30, "fractures_nonempty": True},
        "sample_trace_pushover.json": {"fractures_contains": "ENGAGEMENT_FAIL"},
        "sample_trace_rhetoric.json": {"fractures_contains": "HALLUC_FILL", "failure_contains": "rhetoric_over_filing"},
    }
    for filename, exp in expectations.items():
        path = ROOT / "env_v1" / "runs" / filename
        trace = json.loads(path.read_text())
        scores = score_trace(trace)
        enriched = enrich_env_trace(trace, scores)
        missing = validate_trajectory_v1_minimal(enriched)
        assert not missing, f"{filename} missing {missing}"
        assert enriched.get("track") == "env"
        assert "fractures" in enriched
        if "composite_min" in exp:
            assert scores["composite_reward"] >= exp["composite_min"]
        if "composite_max" in exp:
            assert scores["composite_reward"] <= exp["composite_max"]
        if exp.get("fractures") == []:
            assert scores["fracture_codes"] == []
        if exp.get("fractures_nonempty"):
            assert len(scores["fracture_codes"]) > 0
        if exp.get("fractures_contains"):
            assert exp["fractures_contains"] in scores["fracture_codes"]
        if exp.get("failure_contains"):
            assert exp["failure_contains"] in scores["failure_modes"]


def check_scripted_agent() -> None:
    out = ROOT / "env_v1" / "runs" / "_smoke_scripted.json"
    plan = ROOT / "env_v1" / "examples" / "agents" / "solaris_good_plan.json"
    subprocess.run(
        [
            sys.executable,
            "env_v1/scripts/agent_loop.py",
            "--agent", "scripted",
            "--plan", str(plan),
            "--out", str(out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    trace = json.loads(out.read_text())
    assert trace["termination"] == "submit"
    assert trace.get("trajectory_id")
    assert trace.get("fractures") is not None
    assert trace["reward"]["composite_reward"] >= 0.85
    out.unlink(missing_ok=True)
    out.with_name(out.stem + "_scores.json").unlink(missing_ok=True)


def check_mock_agent() -> None:
    out = ROOT / "env_v1" / "runs" / "_smoke_mock.json"
    subprocess.run(
        [
            sys.executable,
            "env_v1/scripts/agent_loop.py",
            "--agent", "mock",
            "--out", str(out),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    trace = json.loads(out.read_text())
    assert trace["termination"] == "submit"
    assert "SECTION_MISS" in trace.get("fractures", []) or "omit_prior_year" in str(
        trace.get("reward", {})
    )
    out.unlink(missing_ok=True)
    out.with_name(out.stem + "_scores.json").unlink(missing_ok=True)


def check_frontier_v2_rescore() -> None:
    """Frontier v2 traces must fire rhetoric/prior-year traps under v1.1.2+ scorer."""
    sys.path.insert(0, str(ROOT / "env_v1" / "scripts"))
    from score_episode import score_trace  # noqa: E402

    path = ROOT / "env_v1" / "runs" / "frontier" / "frontier_gpt-4o_001.json"
    if not path.exists():
        return
    scores = score_trace(json.loads(path.read_text()))
    modes = set(scores["failure_modes"])
    assert modes & {"rhetoric_over_filing", "unsupported_prior_year_claim"}, modes
    assert scores["composite_reward"] <= 0.55


def main() -> int:
    checks = [
        ("GOOGL ground truth L1", check_googl_gt),
        ("PEP FX ground truth L1", check_pep_fx_gt),
        ("Corpus manifest", check_corpus_manifest),
        ("PM FSM fallback escalation", check_pm_fsm_fallback_escalation),
        ("Env demo traces + schema", check_env_traces),
        ("Frontier v2 rescore traps", check_frontier_v2_rescore),
        ("Scripted agent loop", check_scripted_agent),
        ("Mock LLM agent loop", check_mock_agent),
    ]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"OK  {name}")
        except Exception as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
