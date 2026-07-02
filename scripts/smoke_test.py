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


def check_amzn_gt() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task", "AMZN_footnote_reconciliation",
    ])
    assert report["all_pass"] is True, report
    assert report["fracture_codes"] == []

    import tempfile
    trap_values = {
        "north_america_net_sales": 426_305,
        "international_net_sales": 161_894,
        "aws_net_sales": 128_725,
        "consolidated_net_sales": 736_391,
        "international_reported_growth_pct": 13.0,
        "international_cc_growth_pct": 10.0,
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(trap_values, tmp)
        trap_path = tmp.name
    trap_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task", "AMZN_footnote_reconciliation",
        "--agent-output", trap_path,
    ])
    Path(trap_path).unlink(missing_ok=True)
    assert trap_report["all_pass"] is False, trap_report
    assert "treat_sbc_as_segment_line_item" in trap_report["failure_modes"], trap_report
    assert trap_report["fracture_codes"] == ["SBC_ALLOCATION_ERR"], trap_report


def check_nflx_gt() -> None:
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task", "NFLX_guidance_drift",
    ])
    assert report["all_pass"] is True, report
    assert report["fracture_codes"] == []

    import tempfile
    gt_path = ROOT / "benchmark_v0.1" / "ground_truth" / "NFLX_guidance_drift_gt.json"
    gt = json.loads(gt_path.read_text())
    base = {item["metric_id"]: item["value"] for item in gt["extracted_values"]}
    for item in gt["computed_values"]:
        if isinstance(item.get("value"), bool):
            base[item["metric_id"]] = item["value"]

    wrong_ytd = {**base, "ytd_content_cash_payments_usd_m": 7385}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(wrong_ytd, tmp)
        trap_path = tmp.name
    trap_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_guidance_drift.py",
        "--ground-truth", str(gt_path),
        "--agent-output", trap_path,
    ])
    Path(trap_path).unlink(missing_ok=True)
    assert trap_report["all_pass"] is False, trap_report
    assert "wrong_ytd_window" in trap_report["failure_modes"], trap_report
    assert trap_report["fracture_codes"] == ["GUIDANCE_PERIOD_ERR"], trap_report

    amort_trap = {**base, "ytd_content_cash_payments_usd_m": 11658}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(amort_trap, tmp)
        trap_path = tmp.name
    trap_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_guidance_drift.py",
        "--ground-truth", str(gt_path),
        "--agent-output", trap_path,
    ])
    Path(trap_path).unlink(missing_ok=True)
    assert trap_report["all_pass"] is False, trap_report
    assert "amortization_as_cash" in trap_report["failure_modes"], trap_report
    assert trap_report["fracture_codes"] == ["CASH_VS_AMORT_ERR"], trap_report

    float_months = {**base, "ytd_period_months": 9.0}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(float_months, tmp)
        float_path = tmp.name
    float_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_guidance_drift.py",
        "--ground-truth", str(gt_path),
        "--agent-output", float_path,
    ])
    Path(float_path).unlink(missing_ok=True)
    assert float_report["all_pass"] is True, float_report

    rounding_fail = {**base, "q3_content_amortization_usd_m": 4002}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(rounding_fail, tmp)
        rounding_path = tmp.name
    rounding_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_guidance_drift.py",
        "--ground-truth", str(gt_path),
        "--agent-output", rounding_path,
    ])
    Path(rounding_path).unlink(missing_ok=True)
    assert rounding_report["all_pass"] is False, rounding_report
    assert rounding_report["failure_modes"] == [], rounding_report
    assert rounding_report["fracture_codes"] == [], rounding_report


def check_fracture_taxonomy_registry() -> None:
    """Fracture library codes must be registered in fracture_taxonomy_v1.json."""
    taxonomy = json.loads((ROOT / "schemas" / "fracture_taxonomy_v1.json").read_text())
    registry = {entry["code"] for entry in taxonomy["codes"]}

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from fracture_registry import all_registered_fracture_codes  # noqa: E402

    emitted = all_registered_fracture_codes()
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

    gold_amzn = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task", "AMZN_footnote_reconciliation",
        "--agent-output", str(contract_dir / "AMZN_footnote_reconciliation_gold.json"),
    ])
    assert gold_amzn["all_pass"] is True
    assert gold_amzn["fracture_codes"] == []

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
    amzn = BenchmarkToolBackend(load_bundle("AMZN_footnote_reconciliation"))

    ok = googl.call("Search_Filing", ticker="GOOGL", period="2026Q1", section="segment_financials")
    assert NOT_FOUND_PREFIX not in ok, ok
    assert googl.log[-1].get("doc_id") == "GOOGL_10Q_2026Q1"
    assert googl.log[-1].get("section_slug") == "segment_financials"

    ok2 = pep.call("Search_Filing", ticker="PEP", period="FY2025", section="narrative_organic")
    assert NOT_FOUND_PREFIX not in ok2, ok2
    assert pep.log[-1].get("section_slug") == "narrative_organic"

    drift = googl.call("Search_Filing", ticker="GOOGL", period="2026Q1", section="Note 15")
    assert drift.startswith(NOT_FOUND_PREFIX), drift
    assert "unknown section slug" in drift

    amzn_policy = amzn.call("Search_Filing", ticker="AMZN", period="FY2025", section="segment_policy")
    assert NOT_FOUND_PREFIX not in amzn_policy, amzn_policy
    assert amzn.log[-1].get("section_slug") == "segment_policy"

    amzn_sbc = amzn.call("Search_Filing", ticker="AMZN", period="FY2025", section="compensation_disclosure")
    assert NOT_FOUND_PREFIX not in amzn_sbc, amzn_sbc
    assert amzn.log[-1].get("section_slug") == "compensation_disclosure"

    amzn_decoy = amzn.call("Search_Filing", ticker="AMZN", period="FY2025", section="segment_financials_prior_year")
    assert NOT_FOUND_PREFIX not in amzn_decoy, amzn_decoy
    assert "637,959" in amzn_decoy

    wrong_period = googl.call("Search_Filing", ticker="GOOGL", period="FY2025", section="segment_financials")
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


def check_submit_metric_schema_validation() -> None:
    """Reject submit payloads with wrong task metric keys (P3-20 schema fidelity)."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.benchmark_tool_specs import parse_submission_args, validate_task_metrics  # noqa: E402

    ko_task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "KO_footnote_reconciliation.json").read_text()
    )
    amzn_metrics = {
        "north_america_net_sales": 19586,
        "international_net_sales": 18720,
        "aws_net_sales": 5735,
        "consolidated_net_sales": 47941,
        "international_reported_growth_pct": -2,
        "international_cc_growth_pct": 10,
    }
    try:
        parse_submission_args({"metrics": amzn_metrics, "citations": []}, ko_task)
        raise AssertionError("expected schema mismatch for AMZN keys on KO task")
    except ValueError as e:
        assert "schema mismatch" in str(e)
        assert "aws_net_sales" in str(e)

    ko_gold = json.loads(
        (
            ROOT / "benchmark_v0.1" / "contract_fixtures" / "KO_footnote_reconciliation_submission_gold.json"
        ).read_text()
    )
    metrics, submission = parse_submission_args(
        {
            "metrics": ko_gold["metrics"],
            "citations": ko_gold["citations"],
            "policy_acknowledgements": ko_gold.get("policy_acknowledgements", []),
        },
        ko_task,
    )
    assert submission is not None
    validate_task_metrics(metrics, ko_task["task_id"])


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
    amzn_task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "AMZN_footnote_reconciliation.json").read_text()
    )

    for task in (googl_task, pep_task, amzn_task):
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
    from agent_output_contract import load_json  # noqa: E402

    pep_bundle = load_bundle("PEP_fx_organic_growth")
    pep_gold_path = load_json(ROOT / "benchmark_v0.1" / "gold_paths" / "PEP_fx_organic_growth.json")
    pep_guidance = citation_guidance_for_task(
        "PEP_fx_organic_growth", bundle=pep_bundle, gold_path=pep_gold_path
    )
    assert "Preferred retrieval order" in pep_guidance and "narrative_organic" in pep_guidance
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
        combined = (proc.stderr or "") + (proc.stdout or "")
        if proc.returncode != 0 and "network error" in combined.lower():
            return
        assert proc.returncode == 0, combined
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
        is_gemini_model,
        is_openai_model,
        to_anthropic_tools,
    )
    from agents.anthropic_benchmark_agent import AnthropicBenchmarkAgent  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    from agents.llm_retry import retry_sleep_seconds  # noqa: E402

    assert retry_sleep_seconds(429, "Please try again in 1.148s", 0) >= 1.6
    assert is_anthropic_model("claude-sonnet-4-5") is True
    assert is_anthropic_model("gpt-4o") is False
    assert is_gemini_model("gemini-2.0-flash") is True
    assert is_openai_model("gemini-2.0-flash") is False
    assert is_openai_model("gpt-4o") is True

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
    assert "segment_financials" in prompt and "ALLOWED SECTION SLUGS" in prompt

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
    assert report["gold_pass_count"] == 5
    assert report["trap_fail_count"] == 6

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
        (
            "PEP_fx_organic_growth_submission_trap_duplicate_snippet.json",
            ["CITE_BROAD"],
            ["cite_duplicate_snippet"],
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
    from agent_output_contract import load_json  # noqa: E402
    from benchmark_eval_mode import eval_mode_enabled  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    assert eval_mode_enabled(True) is True
    assert eval_mode_enabled(False) is False

    task = json.loads(
        (ROOT / "benchmark_v0.1" / "tasks" / "PEP_fx_organic_growth.json").read_text()
    )
    bundle = load_bundle(task["task_id"])
    gold_path = load_json(ROOT / "benchmark_v0.1" / "gold_paths" / "PEP_fx_organic_growth.json")
    dev_guidance = citation_guidance_for_task(
        "PEP_fx_organic_growth", eval_mode=False, bundle=bundle, gold_path=gold_path
    )
    eval_guidance = citation_guidance_for_task("PEP_fx_organic_growth", eval_mode=True)
    assert "Preferred retrieval order" in dev_guidance
    assert "Preferred retrieval order" not in eval_guidance
    assert "eval mode" in eval_guidance.lower()

    dev_prompt = build_system_prompt(task, bundle, eval_mode=False)
    eval_prompt = build_system_prompt(task, bundle, eval_mode=True)
    assert "Preferred retrieval order" in dev_prompt
    assert "Preferred retrieval order" not in eval_prompt


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


def check_discrimination_v2_rescore() -> None:
    """P2-11 — PEP+AMZN headline composite and weighted per-model scores."""
    proc = subprocess.run(
        [
            sys.executable,
            "benchmark_v0.1/scripts/run_benchmark_campaign.py",
            "--campaign", "benchmark_v0.1/campaigns/pilot_eval_discrimination_v2.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    summary = json.loads(proc.stdout.split("\n\nWrote")[0])
    assert summary["scored"] == 12, summary
    assert summary.get("weighted_composite_by_model"), summary
    assert summary["weighted_composite_by_model"]["gpt-4o"] < summary["weighted_composite_by_model"]["claude-sonnet-4-5"]
    assert summary["by_task_composite_median"]["PEP_fx_organic_growth"] < 1.0


def check_amzn_l2_path() -> None:
    """AMZN third task — four-section gold path with order-weighted L2."""
    import tempfile

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from score_benchmark_run import score_l2_section_recall, score_run  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402
    from agent_output_contract import load_json  # noqa: E402

    plan = ROOT / "benchmark_v0.1" / "examples" / "agents" / "amzn_good_plan.json"
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "AMZN_footnote_reconciliation",
                "--plan", str(plan),
                "--out-dir", str(out_dir),
                "--run-index", "1",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        trace = json.loads((out_dir / "AMZN_footnote_reconciliation_run01_trace.json").read_text())
        bundle = load_bundle("AMZN_footnote_reconciliation")
        gold_path = load_json(ROOT / "benchmark_v0.1" / "gold_paths" / "AMZN_footnote_reconciliation.json")
        l2 = score_l2_section_recall(
            trace, task_id="AMZN_footnote_reconciliation", gold_path=gold_path, bundle=bundle
        )
        assert l2["l2_score"] >= 0.95, l2
        assert l2["components"]["section_order"] == 1.0, l2
        assert len(l2["required_sections"]) == 5, l2

        skip_sbc_plan = {
            **json.loads(plan.read_text()),
            "actions": [
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "segment_policy"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "segment_financials"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "consolidated_primary"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "narrative_fx"}},
                {"type": "tool_call", "tool": "Python_Interpreter", "input": {"expression": "426305 + 161894 + 128725"}},
                {"type": "submit_structured_output", "structured_output": {
                    "north_america_net_sales": 426305,
                    "international_net_sales": 161894,
                    "aws_net_sales": 128725,
                    "consolidated_net_sales": 716924,
                    "international_reported_growth_pct": 13.0,
                    "international_cc_growth_pct": 10.0,
                }},
            ],
        }
        skip_path = out_dir / "skip_sbc_plan.json"
        skip_path.write_text(json.dumps(skip_sbc_plan), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "AMZN_footnote_reconciliation",
                "--plan", str(skip_path),
                "--out-dir", str(out_dir),
                "--run-index", "3",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        skip_trace = json.loads((out_dir / "AMZN_footnote_reconciliation_run03_trace.json").read_text())
        skip_l2 = score_l2_section_recall(
            skip_trace, task_id="AMZN_footnote_reconciliation", gold_path=gold_path, bundle=bundle
        )
        assert "compensation_disclosure" in skip_l2.get("missing_sections", []), skip_l2
        assert skip_l2["l2_score"] < l2["l2_score"], (skip_l2, l2)

        wrong_order_plan = {
            **json.loads(plan.read_text()),
            "actions": [
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "segment_financials"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "segment_policy"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "compensation_disclosure"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "consolidated_primary"}},
                {"type": "tool_call", "tool": "Search_Filing", "input": {"ticker": "AMZN", "period": "FY2025", "section": "narrative_fx"}},
                {"type": "tool_call", "tool": "Python_Interpreter", "input": {"expression": "426305 + 161894 + 128725"}},
                {"type": "submit_structured_output", "structured_output": {
                    "north_america_net_sales": 426305,
                    "international_net_sales": 161894,
                    "aws_net_sales": 128725,
                    "consolidated_net_sales": 716924,
                    "international_reported_growth_pct": 13.0,
                    "international_cc_growth_pct": 10.0,
                }},
            ],
        }
        wrong_path = out_dir / "wrong_plan.json"
        wrong_path.write_text(json.dumps(wrong_order_plan), encoding="utf-8")
        subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                "--agent", "scripted",
                "--task", "AMZN_footnote_reconciliation",
                "--plan", str(wrong_path),
                "--out-dir", str(out_dir),
                "--run-index", "2",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        bad_trace = json.loads((out_dir / "AMZN_footnote_reconciliation_run02_trace.json").read_text())
        bad_l2 = score_l2_section_recall(
            bad_trace, task_id="AMZN_footnote_reconciliation", gold_path=gold_path, bundle=bundle
        )
        assert bad_l2["components"]["section_order"] < 1.0, bad_l2
        assert bad_l2["l2_score"] < l2["l2_score"], (bad_l2, l2)


def check_leaderboard_v0() -> None:
    """P2-06 — actionable leaderboard from scored campaign report."""
    script = ROOT / "benchmark_v0.1" / "scripts" / "generate_leaderboard.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.returncode == 0, proc.stderr
    doc = json.loads((ROOT / "benchmark_v0.1" / "docs" / "LEADERBOARD_v0.json").read_text())
    assert doc["schema_version"] == "leaderboard_v0"
    assert doc["campaign_id"] == "pilot_eval_5task_v1"
    assert len(doc["rankings"]) >= 2
    leader = doc["leader_model_id"]
    assert leader == doc["rankings"][0]["model_id"]
    gpt = next(r for r in doc["rankings"] if r["model_id"] == "gpt-4o")
    assert gpt["gap_task"]["task_id"] in doc["methodology"]["headline_tasks"]
    assert gpt["fracture_intensity"] >= doc["rankings"][0]["fracture_intensity"]


def check_fracture_registry() -> None:
    """P3-08 — central fracture library resolves L1/L2/L3 modes."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from fracture_registry import (  # noqa: E402
        all_registered_fracture_codes,
        fracture_code,
        fracture_codes,
        taxonomy_codes,
    )

    assert fracture_code("cite_halluc", layer="L3") == "CITE_HALLUC"
    assert fracture_code("pushover", layer="ENV") == "ENGAGEMENT_FAIL"
    assert fracture_code("submit_timeout", layer="L1") == "TIMEOUT"
    assert fracture_code("omit_prior_year", layer="ENV") == "SECTION_MISS"
    assert fracture_code("wrong_ytd_window", task_id="NFLX_guidance_drift", layer="L1") == "GUIDANCE_PERIOD_ERR"
    assert fracture_codes(["blind_sum", "sign_error"], task_id="GOOGL_footnote_reconciliation", layer="L1") == [
        "RECON_OMIT",
        "SIGN_ERR",
    ]
    assert all_registered_fracture_codes() <= taxonomy_codes()


def check_shared_runtime() -> None:
    """SH-14 — cross-track safe_calc + LLM retry helpers."""
    sys.path.insert(0, str(ROOT))
    from shared.llm_retry import retry_sleep_seconds  # noqa: E402
    from shared.safe_calc import safe_calc  # noqa: E402
    from shared.trace_utils import validate_trajectory_v1_minimal  # noqa: E402

    assert safe_calc("89637 + 20028 + 411") == 110_076.0
    assert safe_calc("-180") == -180.0
    assert retry_sleep_seconds(429, "try again in 3.2s", 1) >= 3.5
    assert validate_trajectory_v1_minimal({"trajectory_id": "t1", "episode_or_task_id": "x", "track": "benchmark", "termination": "submit", "steps": []}) == []


def check_ko_gt_draft() -> None:
    """P3-18 — KO footnote draft L1 + GT-derived fixtures."""
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task",
        "KO_footnote_reconciliation",
    ])
    assert report["all_pass"] is True, report
    assert report["fracture_codes"] == []

    import tempfile

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agent_output_contract import l1_values_from_gt, submission_from_gt  # noqa: E402

    metrics = l1_values_from_gt("KO_footnote_reconciliation")
    assert metrics["consolidated_net_revenues"] == 47_941
    sub = submission_from_gt("KO_footnote_reconciliation")
    assert sub["schema_version"] == "agent_submission_v1"
    assert len(sub["citations"]) >= 6
    assert "global_ventures_sunset_2025" in sub["policy_acknowledgements"]
    seg_cite = next(c for c in sub["citations"] if c["metric_id"] == "emea_net_revenues")
    assert seg_cite["section_slug"] == "segment_financials"
    assert "Note 20" in seg_cite.get("filing_label", "")

    trap_values = l1_values_from_gt("KO_footnote_reconciliation")
    trap_values["bottling_investments_net_revenues"] = None
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(trap_values, tmp)
        trap_path = tmp.name
    trap_report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_footnote_exact.py",
        "--ground-truth",
        str(ROOT / "benchmark_v0.1" / "ground_truth" / "KO_footnote_reconciliation_gt.json"),
        "--agent-output",
        trap_path,
    ])
    Path(trap_path).unlink(missing_ok=True)
    assert trap_report["all_pass"] is False, trap_report
    assert "omit_bottling_investments" in trap_report["failure_modes"], trap_report


def check_submit_timeout_failure_mode() -> None:
    """Empty agent output maps to submit_timeout → TIMEOUT, not wrong_period."""
    import tempfile

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from verify_common import is_empty_agent_output  # noqa: E402

    assert is_empty_agent_output({}) is True
    assert is_empty_agent_output({"consolidated_net_revenues": None}) is True
    assert is_empty_agent_output({"consolidated_net_revenues": 47_941}) is False

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump({}, tmp)
        empty_path = tmp.name
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/verify_benchmark_l1.py",
        "--task",
        "KO_footnote_reconciliation",
        "--agent-output",
        empty_path,
    ])
    Path(empty_path).unlink(missing_ok=True)
    assert report["all_pass"] is False, report
    assert report["failure_modes"] == ["submit_timeout"], report
    assert report["fracture_codes"] == ["TIMEOUT"], report


def check_retrieval_nudge_tracker() -> None:
    """Post-retrieval nudge fires once after filing pulls without Python/submit."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.retrieval_nudge import NUDGE_AFTER_RETRIEVALS, RetrievalNudgeTracker  # noqa: E402

    tracker = RetrievalNudgeTracker()
    for _ in range(NUDGE_AFTER_RETRIEVALS - 1):
        assert tracker.on_tool_result("Search_Filing") is None
    nudge = tracker.on_tool_result("Search_Filing")
    assert nudge is not None
    assert tracker.on_tool_result("Search_Filing") is None

    tracker2 = RetrievalNudgeTracker()
    for _ in range(NUDGE_AFTER_RETRIEVALS - 1):
        tracker2.on_tool_result("PDF_Parser")
    assert tracker2.on_tool_result("Python_Interpreter") is None
    assert tracker2.nudge_sent is False
    assert tracker2.on_tool_result("Search_Filing") is None


def check_agent_mode_model_filter() -> None:
    """--agent gemini/openai/anthropic must not execute non-matching model slots."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from run_benchmark_campaign import filter_models_for_agent_mode  # noqa: E402

    models = ["gpt-4o", "claude-sonnet-4-5", "gemini-2.5-flash"]
    assert filter_models_for_agent_mode("gemini", models) == ["gemini-2.5-flash"]
    assert filter_models_for_agent_mode("openai", models) == ["gpt-4o"]
    assert filter_models_for_agent_mode("anthropic", models) == ["claude-sonnet-4-5"]
    assert filter_models_for_agent_mode("auto", models) == models


def check_l3_citation_hardening() -> None:
    """P3-29 — column/row-aware L3 rules (9B); KO template + archetype baselines."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from l3_citation_rules import merge_l3_rules, numeric_in_snippet  # noqa: E402

    ko_rules = merge_l3_rules("F_exact", {
        "metric_citation_anchors": {"emea_net_revenues": {"row_label": "EMEA"}},
    })
    assert ko_rules["require_numeric_in_snippet"] is True
    assert "emea_net_revenues" in ko_rules["metric_citation_anchors"]
    assert numeric_in_snippet(-4.7, "(4.7)%") is True

    from l3_citation_rules import row_label_match  # noqa: E402

    assert row_label_match("North America, net | 426,305", {"row_label": "North America"}) is True
    assert row_label_match("NA | 426,305", {"row_label": "North America"}) is False

    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_agent_submission.py",
        "--task",
        "KO_footnote_reconciliation",
        "--submission",
        str(ROOT / "benchmark_v0.1/contract_fixtures/KO_footnote_reconciliation_submission_gold.json"),
    ])
    assert report["l3_pass"] is True, report

    trap = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_agent_submission.py",
        "--task",
        "KO_footnote_reconciliation",
        "--submission",
        str(ROOT / "benchmark_v0.1/contract_fixtures/KO_footnote_reconciliation_submission_trap_note_only.json"),
    ])
    assert trap["l3_pass"] is False, trap
    assert "cite_broad" in trap["failure_modes"] or "cite_halluc" in trap["failure_modes"], trap

    for task_id, fixture in (
        ("AMZN_footnote_reconciliation", "AMZN_footnote_reconciliation_submission_gold.json"),
        ("NFLX_guidance_drift", "NFLX_guidance_drift_submission_gold.json"),
    ):
        amzn_report = run([
            sys.executable,
            "benchmark_v0.1/scripts/validate_agent_submission.py",
            "--task",
            task_id,
            "--submission",
            str(ROOT / "benchmark_v0.1/contract_fixtures" / fixture),
        ])
        assert amzn_report["l3_pass"] is True, (task_id, amzn_report)


def check_mock_agents_published() -> None:
    """P3-16 — weak mock agent runs for all published tasks with expected L1 fractures."""
    import tempfile

    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agents.mock_benchmark_agents import EXPECTED_MOCK_FRACTURES  # noqa: E402
    from task_registry import published_task_ids  # noqa: E402
    from verify_benchmark_l1 import l1_verify_argv  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        out_dir = Path(tmp)
        for task_id in published_task_ids():
            proc = subprocess.run(
                [
                    sys.executable,
                    "benchmark_v0.1/scripts/benchmark_agent_loop.py",
                    "--agent",
                    "mock",
                    "--task",
                    task_id,
                    "--out-dir",
                    str(out_dir),
                    "--run-index",
                    "1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            assert proc.returncode == 0, (task_id, proc.stderr or proc.stdout)

            mock_out = out_dir / f"{task_id}_run01.json"
            report = run(l1_verify_argv(task_id, mock_out))
            assert report["all_pass"] is False, (task_id, report)
            expected = EXPECTED_MOCK_FRACTURES[task_id]
            assert expected <= set(report.get("fracture_codes", [])), (task_id, report)


def check_submission_from_gt_computed() -> None:
    """P3-32 — submission_from_gt builds computed-metric citations from gold_path policy."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agent_output_contract import submission_from_gt  # noqa: E402

    for task_id in ("NFLX_guidance_drift", "KO_footnote_reconciliation"):
        sub = submission_from_gt(task_id)
        report = run([
            sys.executable,
            "benchmark_v0.1/scripts/validate_agent_submission.py",
            "--task",
            task_id,
            "--submission",
            str(ROOT / "benchmark_v0.1/contract_fixtures" / f"{task_id}_submission_gold.json"),
        ])
        assert report["l3_pass"] is True, (task_id, report)
        computed_ids = {
            "NFLX_guidance_drift": {
                "implied_ytd_pace_usd_m",
                "cash_vs_guidance_pace_variance_pct",
                "guidance_pace_under",
            },
            "KO_footnote_reconciliation": {"reconciliation_bridge_total"},
        }[task_id]
        got = {c["metric_id"] for c in sub["citations"]}
        assert computed_ids <= got, (task_id, got)


def check_l3_anchor_regression() -> None:
    """P3-36 — GT + submission-gold citations satisfy resolved L3 anchors."""
    report = run([
        sys.executable,
        "benchmark_v0.1/scripts/validate_l3_anchor_regression.py",
        "--all",
    ])
    assert report["all_pass"] is True, report


def check_synthetic_l3_eval() -> None:
    """P3-15 — decoy bait citation detection when synthetic_l3_eval is enabled."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from agent_output_contract import submission_from_gt  # noqa: E402
    from synthetic_l3 import check_synthetic_l3_submission  # noqa: E402
    from task_registry import load_bundle  # noqa: E402

    bundle = load_bundle("NFLX_guidance_drift")
    good = submission_from_gt("NFLX_guidance_drift")
    assert check_synthetic_l3_submission(good, bundle)["synthetic_l3_pass"] is True

    bad = dict(good)
    bad["citations"] = list(good["citations"])
    bad["citations"][2] = {
        **bad["citations"][2],
        "snippet": "Additions to content assets (cash) $ (7,385,470)",
    }
    hit = check_synthetic_l3_submission(bad, bundle)
    assert hit["synthetic_l3_pass"] is False, hit
    assert "synthetic_l3_bait_cited" in hit["failure_modes"]


def check_scaffold_task() -> None:
    """P3-31 — scaffold_task.py emits archetype skeleton files."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.run(
            [
                sys.executable,
                "benchmark_v0.1/scripts/scaffold_task.py",
                "--task-id",
                "SCAFFOLD_footnote_reconciliation",
                "--archetype",
                "F_exact",
                "--ticker",
                "SCAF",
                "--fiscal-period",
                "FY2025",
                "--out-dir",
                tmp,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, proc.stderr or proc.stdout
        assert (Path(tmp) / "SCAFFOLD_footnote_reconciliation_gt.json").exists()
        gt = json.loads((Path(tmp) / "SCAFFOLD_footnote_reconciliation_gt.json").read_text())
        assert gt["verification_schema"]["archetype"] == "F_exact"


def check_doc_sync() -> None:
    """P3-28 — manifest-driven README/ARCHITECTURE blocks stay in sync."""
    proc = subprocess.run(
        [sys.executable, "benchmark_v0.1/scripts/sync_track_a_docs.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout


def check_task_registry() -> None:
    """P3-11 — manifest-driven task wiring SSOT."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from task_registry import (  # noqa: E402
        all_task_ids,
        corpus_bundle_path,
        load_manifest,
        published_task_ids,
        scripted_plan_path,
    )

    manifest = load_manifest()
    assert manifest["published_tasks"] == 5
    assert manifest["draft_tasks"] == 0
    task_ids = all_task_ids()
    assert len(task_ids) == 5
    for task_id in task_ids:
        path = corpus_bundle_path(task_id)
        assert path.exists(), task_id
    for task_id in (
        "GOOGL_footnote_reconciliation",
        "PEP_fx_organic_growth",
        "AMZN_footnote_reconciliation",
        "NFLX_guidance_drift",
        "KO_footnote_reconciliation",
    ):
        assert scripted_plan_path(task_id) is not None, task_id
    assert len(published_task_ids()) == 5
    assert "KO_footnote_reconciliation" in published_task_ids()


def check_archetype_roles() -> None:
    """P2-13 — path_role slugs + archetype schema alignment."""
    sys.path.insert(0, str(ROOT / "benchmark_v0.1" / "scripts"))
    from archetype_roles import load_archetype_schema, task_archetype, validate_registry  # noqa: E402
    from benchmark_tool_backend import load_bundle  # noqa: E402

    schema = load_archetype_schema()
    assert "F_exact" in schema["archetypes"]
    for task_id in (
        "GOOGL_footnote_reconciliation",
        "PEP_fx_organic_growth",
        "AMZN_footnote_reconciliation",
        "NFLX_guidance_drift",
    ):
        archetype = task_archetype(task_id)
        bundle = load_bundle(task_id)
        checks = validate_registry(bundle, archetype)
        failed = [c for c in checks if not c[2]]
        assert not failed, (task_id, failed)


def main() -> int:
    checks = [
        ("GOOGL ground truth L1", check_googl_gt),
        ("PEP FX ground truth L1", check_pep_fx_gt),
        ("AMZN footnote ground truth L1", check_amzn_gt),
        ("NFLX guidance drift L1", check_nflx_gt),
        ("KO footnote draft L1", check_ko_gt_draft),
        ("Submit timeout failure mode", check_submit_timeout_failure_mode),
        ("Retrieval nudge tracker", check_retrieval_nudge_tracker),
        ("L3 citation hardening (9B)", check_l3_citation_hardening),
        ("Mock agents (published tasks)", check_mock_agents_published),
        ("Submission from GT (computed L3)", check_submission_from_gt_computed),
        ("L3 anchor regression", check_l3_anchor_regression),
        ("Synthetic L3 eval", check_synthetic_l3_eval),
        ("Scaffold task CLI", check_scaffold_task),
        ("Doc sync from manifest", check_doc_sync),
        ("Agent mode model filter", check_agent_mode_model_filter),
        ("Shared runtime (SH-14)", check_shared_runtime),
        ("Fracture taxonomy registry", check_fracture_taxonomy_registry),
        ("Corpus manifest", check_corpus_manifest),
        ("Corpus bundles", check_corpus_bundles),
        ("Task registry SSOT", check_task_registry),
        ("Archetype path roles", check_archetype_roles),
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
        ("Submit metric schema validation", check_submit_metric_schema_validation),
        ("OpenAI submit schema", check_openai_submit_schema),
        ("Anthropic adapter", check_anthropic_adapter),
        ("Eval mode prompts", check_eval_mode_prompts),
        ("Discrimination scoring", check_discrimination_scoring),
        ("Discrimination v2 rescore", check_discrimination_v2_rescore),
        ("AMZN L2 path variance", check_amzn_l2_path),
        ("Campaign execute scripted", check_campaign_execute_scripted),
        ("Leaderboard v0 generator", check_leaderboard_v0),
        ("Fracture registry library", check_fracture_registry),
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
