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


def check_fracture_taxonomy_registry() -> None:
    """Benchmark verify scripts must only emit codes registered in fracture_taxonomy_v1.json."""
    taxonomy = json.loads((ROOT / "schemas" / "fracture_taxonomy_v1.json").read_text())
    registry = {entry["code"] for entry in taxonomy["codes"]}

    bench_scripts = ROOT / "benchmark_v0.1" / "scripts"
    sys.path.insert(0, str(bench_scripts))
    from verify_fx_organic_growth import FAILURE_FRACTURE as pep_fractures  # noqa: E402
    from verify_googl_footnote_reconciliation import FAILURE_FRACTURE as googl_fractures  # noqa: E402
    from validate_agent_submission import FAILURE_FRACTURE as l3_fractures  # noqa: E402

    emitted = set(googl_fractures.values()) | set(pep_fractures.values()) | set(l3_fractures.values())
    missing = emitted - registry
    assert not missing, f"Fracture codes not in registry: {sorted(missing)}"


def check_corpus_manifest() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_corpus_manifest.py",
    ])
    assert report["all_pass"] is True, report
    assert report["pilot_tickers"] == 5


def check_corpus_bundles() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_corpus_bundle.py",
        "--all",
    ])
    assert report["all_pass"] is True, report


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


def check_benchmark_agent_contract() -> None:
    """Directory contract + trap payloads propagate fracture codes through verify scripts."""
    contract_dir = ROOT / "benchmark_v0.1" / "contract_fixtures"

    trap_specs = [
        ("GOOGL_footnote_reconciliation_trap_googl_sign.json", [
            sys.executable,
            "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
            "--period", "q1_2026",
            "--agent-output", str(contract_dir / "GOOGL_footnote_reconciliation_trap_googl_sign.json"),
        ], ["SIGN_ERR"], ["sign_error"]),
        ("GOOGL_footnote_reconciliation_trap_googl_blind_sum.json", [
            sys.executable,
            "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
            "--period", "q1_2026",
            "--agent-output", str(contract_dir / "GOOGL_footnote_reconciliation_trap_googl_blind_sum.json"),
        ], ["RECON_OMIT"], ["blind_sum"]),
        ("PEP_fx_organic_growth_trap_pep_reported_only.json", [
            sys.executable,
            "benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py",
            "--agent-output", str(contract_dir / "PEP_fx_organic_growth_trap_pep_reported_only.json"),
        ], ["CC_OMIT"], ["reported_only"]),
        ("PEP_fx_organic_growth_trap_pep_wrong_region.json", [
            sys.executable,
            "benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py",
            "--agent-output", str(contract_dir / "PEP_fx_organic_growth_trap_pep_wrong_region.json"),
        ], ["SCOPE_ERR"], ["wrong_region"]),
    ]

    if not contract_dir.exists():
        subprocess.run(
            [sys.executable, "benchmark_v0.1/scripts/mock_agent_stub.py", "--write-contract-fixtures"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )

    for filename, cmd, expect_fractures, expect_failures in trap_specs:
        path = contract_dir / filename
        assert path.exists(), f"missing contract fixture {path}"
        report = run(cmd)
        assert report.get("all_pass") is False or report.get("l1_pass") is False, report
        for code in expect_fractures:
            assert code in report.get("fracture_codes", []), report
        for mode_id in expect_failures:
            assert mode_id in report.get("failure_modes", []), report

    gold_googl = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
        "--period", "q1_2026",
        "--agent-output", str(contract_dir / "GOOGL_footnote_reconciliation_gold.json"),
    ])
    assert gold_googl["all_pass"] is True
    assert gold_googl["fracture_codes"] == []

    gold_pep = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_pep_fx_organic_growth.py",
        "--agent-output", str(contract_dir / "PEP_fx_organic_growth_gold.json"),
    ])
    assert gold_pep["all_pass"] is True
    assert gold_pep["fracture_codes"] == []

    import tempfile

    campaign = json.loads(
        (ROOT / "benchmark_v0.1" / "campaigns" / "pilot_eval_campaign_v1.json").read_text()
    )
    with tempfile.TemporaryDirectory() as tmp:
        mini = {
            **campaign,
            "runs_dir": tmp,
            "models": ["gpt-4o"],
            "tasks": ["GOOGL_footnote_reconciliation"],
            "runs_per_task": 2,
        }
        mini_path = Path(tmp) / "mini_campaign.json"
        mini_path.write_text(json.dumps(mini), encoding="utf-8")
        runs_root = Path(tmp)
        slot_dir = runs_root / "gpt-4o"
        slot_dir.mkdir(parents=True)
        (slot_dir / "GOOGL_footnote_reconciliation_run01.json").write_text("{bad json", encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/run_benchmark_campaign.py",
                "--campaign",
                str(mini_path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1, proc.stderr or proc.stdout
        result = json.loads((runs_root / f"{mini['campaign_id']}.json").read_text())
        assert result["summary"]["missing"] == 1
        assert result["summary"]["scored"] == 1
        malformed = next(r for r in result["runs"] if r["run_index"] == 1)
        assert malformed["status"] == "scored"
        assert "error" in malformed["verify"]


def check_section_retrieval_contract() -> None:
    """v1.1 — backend rejects unknown section slugs; canonical slugs resolve."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from benchmark_tool_backend import BenchmarkToolBackend, NOT_FOUND_PREFIX, load_bundle  # noqa: E402

    googl = BenchmarkToolBackend(load_bundle("GOOGL_footnote_reconciliation"))
    pep = BenchmarkToolBackend(load_bundle("PEP_fx_organic_growth"))

    ok = googl.call("Search_Filing", ticker="GOOGL", period="2026Q1", section="note_15")
    assert NOT_FOUND_PREFIX not in ok, ok
    assert googl.log[-1].get("doc_id") == "GOOGL_10Q_2026Q1"
    assert googl.log[-1].get("section_slug") == "note_15"

    ok2 = pep.call("Search_Filing", ticker="PEP", period="FY2025", section="mdna_organic")
    assert NOT_FOUND_PREFIX not in ok2, ok2
    assert pep.log[-1].get("section_slug") == "mdna_organic"

    drift = googl.call("Search_Filing", ticker="GOOGL", period="2026Q1", section="Note 15")
    assert drift.startswith(NOT_FOUND_PREFIX), drift
    assert "unknown section slug" in drift

    wrong_period = googl.call("Search_Filing", ticker="GOOGL", period="FY2025", section="note_15")
    assert wrong_period.startswith(NOT_FOUND_PREFIX), wrong_period

    invented = googl.call("Search_Filing", ticker="GOOGL", period="2026Q1", section="note_99")
    assert invented.startswith(NOT_FOUND_PREFIX), invented


def check_benchmark_agent_loop() -> None:
    """Track A scripted + mock agent loop against corpus bundles (Agent B dependency)."""
    corpus_dir = ROOT / "benchmark_v0.1" / "corpus"
    googl_bundle = corpus_dir / "googl_q1_2026_bundle.json"
    pep_bundle = corpus_dir / "pep_fy2025_bundle.json"
    if not googl_bundle.exists() or not pep_bundle.exists():
        print("SKIP  Benchmark agent loop (corpus bundles not yet created)")
        return

    import tempfile

    plan = ROOT / "benchmark_v0.1" / "examples" / "agents" / "googl_good_plan.json"
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "GOOGL_footnote_reconciliation",
                "--plan", str(plan),
                "--out-dir", str(out_dir),
                "--run-index", "1",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout

        agent_out = out_dir / "GOOGL_footnote_reconciliation_run01.json"
        trace_out = out_dir / "GOOGL_footnote_reconciliation_run01_trace.json"
        assert agent_out.exists(), agent_out
        assert trace_out.exists(), trace_out

        trace = json.loads(trace_out.read_text())
        assert trace["track"] == "benchmark"
        assert trace["termination"] == "submit"
        assert not any(s.get("type") in ("pm_turn", "send_message_to_pm") for s in trace["steps"])

        report = run([
            sys.executable,
            "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
            "--period", "q1_2026",
            "--agent-output", str(agent_out),
        ])
        assert report["all_pass"] is True, report
        assert report["fracture_codes"] == []

        submission_out = out_dir / "GOOGL_footnote_reconciliation_run01_submission.json"
        assert submission_out.exists(), submission_out
        l3 = run([
            sys.executable,
            "benchmark_v0.1/scripts/validate_agent_submission.py",
            "--task", "GOOGL_footnote_reconciliation",
            "--submission", str(submission_out),
        ])
        assert l3["l3_pass"] is True, l3

        mock_proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "mock",
                "--task", "GOOGL_footnote_reconciliation",
                "--out-dir", str(out_dir),
                "--run-index", "2",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert mock_proc.returncode == 0, mock_proc.stderr or mock_proc.stdout

        mock_out = out_dir / "GOOGL_footnote_reconciliation_run02.json"
        mock_report = run([
            sys.executable,
            "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
            "--period", "q1_2026",
            "--agent-output", str(mock_out),
        ])
        assert mock_report["all_pass"] is False, mock_report
        assert "RECON_OMIT" in mock_report.get("fracture_codes", []), mock_report


def check_campaign_execute_scripted() -> None:
    """P2-04f — campaign --execute with scripted agent writes contract paths (no API key)."""
    import tempfile

    campaign = json.loads(
        (ROOT / "benchmark_v0.1" / "campaigns" / "pilot_eval_campaign_v1.json").read_text()
    )
    with tempfile.TemporaryDirectory() as tmp:
        mini = {
            **campaign,
            "campaign_id": "smoke_execute_scripted",
            "runs_dir": tmp,
            "models": ["gpt-4o"],
            "tasks": ["GOOGL_footnote_reconciliation"],
            "runs_per_task": 1,
        }
        mini_path = Path(tmp) / "mini_campaign.json"
        mini_path.write_text(json.dumps(mini), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/run_benchmark_campaign.py",
                "--campaign",
                str(mini_path),
                "--execute",
                "--agent",
                "scripted",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout

        agent_path = Path(tmp) / "gpt-4o" / "GOOGL_footnote_reconciliation_run01.json"
        trace_path = Path(tmp) / "gpt-4o" / "GOOGL_footnote_reconciliation_run01_trace.json"
        assert agent_path.exists(), agent_path
        assert trace_path.exists(), trace_path
        submission_path = Path(tmp) / "gpt-4o" / "GOOGL_footnote_reconciliation_run01_submission.json"
        assert submission_path.exists(), submission_path

        trace = json.loads(trace_path.read_text())
        assert trace["termination"] == "submit"
        assert trace["agent_mode"] == "scripted"

        report = run([
            sys.executable,
            "benchmark_v0.1/scripts/verify_googl_footnote_reconciliation.py",
            "--period", "q1_2026",
            "--agent-output", str(agent_path),
        ])
        assert report["all_pass"] is True, report

        result = json.loads((Path(tmp) / f"{mini['campaign_id']}.json").read_text())
        assert result["summary"]["missing"] == 0
        assert result["summary"]["l1_all_pass_count"] == 1
        assert result.get("execution") is not None
        assert any(r.get("status") == "executed" for r in result["execution"])


def check_composite_scoring() -> None:
    """P2-04e — L1+L2+L3 composite via score_benchmark_run.py."""
    import tempfile

    plan = ROOT / "benchmark_v0.1" / "examples" / "agents" / "googl_good_plan.json"
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "GOOGL_footnote_reconciliation",
                "--plan", str(plan),
                "--out-dir", str(out_dir),
                "--run-index", "1",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout

        agent_out = out_dir / "GOOGL_footnote_reconciliation_run01.json"
        trace_out = out_dir / "GOOGL_footnote_reconciliation_run01_trace.json"
        submission_out = out_dir / "GOOGL_footnote_reconciliation_run01_submission.json"

        full = run([
            sys.executable,
            "benchmark_v0.1/scripts/score_benchmark_run.py",
            "--task", "GOOGL_footnote_reconciliation",
            "--agent-output", str(agent_out),
            "--trace", str(trace_out),
            "--submission", str(submission_out),
        ])
        assert full["composite_score"] >= 0.95, full
        assert full["l1"]["all_pass"] is True
        assert full["l2"]["l2_pass"] is True
        assert full["l3"]["l3_pass"] is True

        l1_only = run([
            sys.executable,
            "benchmark_v0.1/scripts/score_benchmark_run.py",
            "--task", "GOOGL_footnote_reconciliation",
            "--agent-output", str(agent_out),
        ])
        assert l1_only["l1"]["all_pass"] is True
        assert l1_only["l2"]["l2_score"] == 0.0
        assert l1_only["l3"]["l3_score"] == 0.0
        assert l1_only["composite_score"] < full["composite_score"]


def check_openai_submit_schema() -> None:
    """OpenAI submit tool exposes agent_submission_v1 wrapper (metrics + citations)."""
    import os

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.benchmark_tool_specs import SUBMIT_TOOL, build_tool_definitions, parse_submission_args  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    googl_task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "GOOGL_footnote_reconciliation.json").read_text()
    )
    pep_task = json.loads((ROOT / "benchmark_v0.1" / "tasks" / "PEP_fx_organic_growth.json").read_text())

    for task in (googl_task, pep_task):
        bundle = load_bundle(task["task_id"])
        tools = build_tool_definitions(task, bundle)
        submit = next(t for t in tools if t["function"]["name"] == SUBMIT_TOOL)
        params = submit["function"]["parameters"]
        assert "metrics" in params["properties"], params
        assert "citations" in params["properties"], params
        assert "metrics" in params["required"] and "citations" in params["required"]
        n_metrics = len(submit["function"]["parameters"]["properties"]["metrics"]["required"])
        cite = params["properties"]["citations"]
        assert cite["minItems"] == n_metrics and cite.get("maxItems") == n_metrics

    from agents.benchmark_tool_specs import citation_guidance_for_task  # noqa: E402

    pep_guidance = citation_guidance_for_task("PEP_fx_organic_growth")
    assert "Reported growth" in pep_guidance and "EMEA" in pep_guidance
    pep_gold = ROOT / "benchmark_v0.1" / "contract_fixtures" / "PEP_fx_organic_growth_submission_gold.json"
    pep_l3 = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_agent_submission.py",
        "--task", "PEP_fx_organic_growth",
        "--submission", str(pep_gold),
    ])
    assert pep_l3["l3_pass"] is True, pep_l3

    googl_bundle = load_bundle("GOOGL_footnote_reconciliation")
    gold_sub = json.loads(
        (ROOT / "benchmark_v0.1" / "contract_fixtures" / "GOOGL_footnote_reconciliation_submission_gold.json").read_text()
    )
    metrics, submission = parse_submission_args(
        {
            "metrics": gold_sub["metrics"],
            "citations": gold_sub["citations"],
            "policy_acknowledgements": gold_sub.get("policy_acknowledgements", []),
        },
        googl_task,
    )
    assert submission is not None
    assert submission["schema_version"] == "agent_submission_v1"
    assert metrics == gold_sub["metrics"]

    if not os.environ.get("OPENAI_API_KEY"):
        return

    import tempfile

    campaign = json.loads(
        (ROOT / "benchmark_v0.1" / "campaigns" / "pilot_eval_1x1x1.json").read_text()
    )
    with tempfile.TemporaryDirectory() as tmp:
        mini = {**campaign, "campaign_id": "smoke_openai_pilot", "runs_dir": tmp}
        mini_path = Path(tmp) / "pilot.json"
        mini_path.write_text(json.dumps(mini), encoding="utf-8")
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/run_benchmark_campaign.py",
                "--campaign", str(mini_path),
                "--execute", "--agent", "openai",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        agent_path = Path(tmp) / "gpt-4o-mini" / "GOOGL_footnote_reconciliation_run01.json"
        submission_path = agent_path.with_name("GOOGL_footnote_reconciliation_run01_submission.json")
        assert agent_path.exists(), agent_path
        assert submission_path.exists(), submission_path
        l3 = run([
            sys.executable,
            "benchmark_v0.1/scripts/validate_agent_submission.py",
            "--task", "GOOGL_footnote_reconciliation",
            "--submission", str(submission_path),
        ])
        assert "l3_pass" in l3


def check_anthropic_adapter() -> None:
    """P2-04h — Anthropic tool schema + model routing (offline)."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.benchmark_tool_specs import (  # noqa: E402
        build_system_prompt,
        build_tool_definitions,
        is_anthropic_model,
        to_anthropic_tools,
    )
    from agents.anthropic_benchmark_agent import AnthropicBenchmarkAgent  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    from agents.llm_retry import retry_sleep_seconds  # noqa: E402

    assert retry_sleep_seconds(429, "Please try again in 1.148s", 0) >= 1.6
    assert is_anthropic_model("claude-sonnet-4-5") is True
    assert is_anthropic_model("gpt-4o") is False

    task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "GOOGL_footnote_reconciliation.json").read_text()
    )
    bundle = load_bundle(task["task_id"])
    openai_tools = build_tool_definitions(task, bundle)
    anthropic_tools = to_anthropic_tools(openai_tools)
    assert len(anthropic_tools) == len(openai_tools)
    for tool in anthropic_tools:
        assert "name" in tool and "input_schema" in tool
        assert "function" not in tool

    prompt = build_system_prompt(task, bundle)
    assert "GOOGL" in prompt or "footnote" in prompt.lower()

    agent = AnthropicBenchmarkAgent(task, bundle, model="claude-sonnet-4-5", api_key="test-key")
    assert agent.tools[0]["name"] == "Search_Filing"
    assert agent.messages[0]["role"] == "user"


def check_agent_submission_validator() -> None:
    """P2-04d — L3 submission validator + gold/trap contract fixtures."""
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_agent_submission.py",
        "--all",
    ])
    assert report["all_pass"] is True, report
    assert report["gold_pass_count"] == 2
    assert report["trap_fail_count"] == 4

    fixture_dir = ROOT / "benchmark_v0.1" / "contract_fixtures"
    trap_specs = [
        (
            "GOOGL_footnote_reconciliation_submission_trap_fake_snippet.json",
            ["CITE_HALLUC"],
            ["cite_halluc"],
        ),
        (
            "GOOGL_footnote_reconciliation_submission_trap_wrong_slug.json",
            ["SECTION_MISS"],
            ["cite_slug_err"],
        ),
        (
            "PEP_fx_organic_growth_submission_trap_missing_policy.json",
            ["POLICY_OMIT"],
            ["policy_omit"],
        ),
        (
            "PEP_fx_organic_growth_submission_trap_halluc_snippet.json",
            ["CITE_HALLUC"],
            ["cite_halluc"],
        ),
    ]
    for filename, expect_fractures, expect_failures in trap_specs:
        path = fixture_dir / filename
        assert path.exists(), path
        task_id = filename.split("_submission_", 1)[0]
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/validate_agent_submission.py",
                "--task", task_id,
                "--submission", str(path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 1, proc.stdout
        one = json.loads(proc.stdout)
        for code in expect_fractures:
            assert code in one.get("fracture_codes", []), one
        for mode in expect_failures:
            assert mode in one.get("failure_modes", []), one


def check_eval_mode_prompts() -> None:
    """P2-09 — eval_mode strips task-specific citation cheat-sheets."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.benchmark_tool_specs import build_system_prompt, citation_guidance_for_task  # noqa: E402
    from benchmark_eval_mode import eval_mode_enabled  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    assert eval_mode_enabled(True) is True
    assert eval_mode_enabled(False) is False

    task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "PEP_fx_organic_growth.json").read_text()
    )
    bundle = load_bundle(task["task_id"])
    dev_guidance = citation_guidance_for_task("PEP_fx_organic_growth", eval_mode=False)
    eval_guidance = citation_guidance_for_task("PEP_fx_organic_growth", eval_mode=True)
    assert "Reported growth" in dev_guidance
    assert "Reported growth" not in eval_guidance
    assert "eval mode" in eval_guidance.lower()

    dev_prompt = build_system_prompt(task, bundle, eval_mode=False)
    eval_prompt = build_system_prompt(task, bundle, eval_mode=True)
    assert "Reported growth" in dev_prompt
    assert "Reported growth" not in eval_prompt


def check_discrimination_scoring() -> None:
    """P2-09 — L2 gold-path components + L3 partial credit."""
    import tempfile

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from score_benchmark_run import score_l2_section_recall, score_run  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402
    from agent_output_contract import load_json  # noqa: E402

    plan = ROOT / "benchmark_v0.1" / "examples" / "agents" / "googl_good_plan.json"
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "GOOGL_footnote_reconciliation",
                "--plan", str(plan),
                "--out-dir", str(out_dir),
                "--run-index", "1",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        trace = json.loads((out_dir / "GOOGL_footnote_reconciliation_run01_trace.json").read_text())
        bundle = load_bundle("GOOGL_footnote_reconciliation")
        gold_path = load_json(ROOT / "benchmark_v0.1" / "gold_paths" / "GOOGL_footnote_reconciliation.json")
        l2 = score_l2_section_recall(trace, task_id="GOOGL_footnote_reconciliation", gold_path=gold_path, bundle=bundle)
        assert l2["l2_score"] >= 0.95, l2
        assert l2["components"]["section_recall"] == 1.0
        assert l2["components"]["section_order"] == 1.0
        assert l2["components"]["tool_coverage"] == 1.0

        full = score_run(
            "GOOGL_footnote_reconciliation",
            out_dir / "GOOGL_footnote_reconciliation_run01.json",
            trace_path=out_dir / "GOOGL_footnote_reconciliation_run01_trace.json",
            submission_path=out_dir / "GOOGL_footnote_reconciliation_run01_submission.json",
        )
        assert full["composite_score"] >= 0.95

    trap = ROOT / "benchmark_v0.1" / "contract_fixtures" / "PEP_fx_organic_growth_submission_trap_missing_policy.json"
    trap_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_agent_submission.py",
        "--task", "PEP_fx_organic_growth",
        "--submission", str(trap),
    ])
    assert trap_report["l3_pass"] is False
    assert 0.0 < trap_report["l3_score"] < 1.0, trap_report

    campaign_path = ROOT / "benchmark_v0.1" / "campaigns" / "pilot_eval_discrimination_v1.json"
    campaign = json.loads(campaign_path.read_text())
    assert campaign.get("eval_mode") is True


def main() -> int:
    checks = [
        ("GOOGL ground truth L1", check_googl_gt),
        ("PEP FX ground truth L1", check_pep_fx_gt),
        ("Fracture taxonomy registry", check_fracture_taxonomy_registry),
        ("Corpus manifest", check_corpus_manifest),
        ("Corpus bundles", check_corpus_bundles),
        ("Section retrieval contract", check_section_retrieval_contract),
        ("Benchmark agent output contract", check_benchmark_agent_contract),
        ("PM FSM fallback escalation", check_pm_fsm_fallback_escalation),
        ("Env demo traces + schema", check_env_traces),
        ("Frontier v2 rescore traps", check_frontier_v2_rescore),
        ("Scripted agent loop", check_scripted_agent),
        ("Mock LLM agent loop", check_mock_agent),
        ("Benchmark agent loop", check_benchmark_agent_loop),
        ("Agent submission L3 validator", check_agent_submission_validator),
        ("Composite run scoring", check_composite_scoring),
        ("OpenAI submit schema", check_openai_submit_schema),
        ("Anthropic adapter", check_anthropic_adapter),
        ("Eval mode prompts", check_eval_mode_prompts),
        ("Discrimination scoring", check_discrimination_scoring),
        ("Campaign execute scripted", check_campaign_execute_scripted),
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
