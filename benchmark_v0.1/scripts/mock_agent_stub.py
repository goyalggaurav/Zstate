#!/usr/bin/env python3
"""
Integration stub — write agent structured outputs to the campaign directory contract.

SH-07 orchestrator must write the same paths this stub uses. Modes exercise gold and trap
payloads without calling any model API.

Usage:
  python mock_agent_stub.py --mode gold --slot gpt-4o/GOOGL_footnote_reconciliation_run01
  python mock_agent_stub.py --write-contract-fixtures
  python mock_agent_stub.py --mode trap_googl_sign --slot gpt-4o/GOOGL_footnote_reconciliation_run01
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from agent_output_contract import (
    BENCH,
    CONTRACT_MODES,
    agent_output_path,
    load_json,
    parse_slot,
    write_agent_output,
    write_contract_submission_fixtures,
)

DEFAULT_CAMPAIGN = BENCH / "campaigns" / "pilot_eval_campaign_v1.json"
CONTRACT_DIR = BENCH / "contract_fixtures"


def write_contract_fixtures() -> list[Path]:
    campaign = load_json(DEFAULT_CAMPAIGN)
    pep_gt = load_json(BENCH / "ground_truth" / "PEP_fx_organic_growth_gt.json")
    written: list[Path] = []

    for mode, spec in CONTRACT_MODES.items():
        if mode == "gold":
            continue
        for task_id in spec["tasks"]:
            filename = f"{task_id}_{mode}.json"
            path = CONTRACT_DIR / filename
            write_agent_output(path, mode, task_id, pep_gt)
            written.append(path)

    gold_googl = CONTRACT_DIR / "GOOGL_footnote_reconciliation_gold.json"
    gold_pep = CONTRACT_DIR / "PEP_fx_organic_growth_gold.json"
    write_agent_output(gold_googl, "gold", "GOOGL_footnote_reconciliation")
    write_agent_output(gold_pep, "gold", "PEP_fx_organic_growth", pep_gt)
    written.extend([gold_googl, gold_pep])

    malformed = CONTRACT_DIR / "malformed.json"
    write_agent_output(malformed, "malformed", "GOOGL_footnote_reconciliation")
    written.append(malformed)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Mock agent output writer (directory contract stub)")
    parser.add_argument("--campaign", type=Path, default=DEFAULT_CAMPAIGN)
    parser.add_argument(
        "--mode",
        choices=[*CONTRACT_MODES.keys(), "malformed", "missing"],
        help="Output mode: gold, trap_*, malformed, or missing (delete file)",
    )
    parser.add_argument(
        "--slot",
        help="Target path as {model_slug}/{task_id}_run{NN}.json",
    )
    parser.add_argument(
        "--write-contract-fixtures",
        action="store_true",
        help="Write reference trap + gold JSON under contract_fixtures/",
    )
    parser.add_argument(
        "--write-submission-fixtures",
        action="store_true",
        help="Write L3 submission gold + trap fixtures under contract_fixtures/",
    )
    args = parser.parse_args()

    if args.write_submission_fixtures:
        paths = write_contract_submission_fixtures()
        print(f"Wrote {len(paths)} submission fixtures under {CONTRACT_DIR.relative_to(BENCH.parent)}")
        return 0

    if args.write_contract_fixtures:
        paths = write_contract_fixtures()
        sub_paths = write_contract_submission_fixtures()
        print(
            f"Wrote {len(paths)} agent output + {len(sub_paths)} submission fixtures "
            f"under {CONTRACT_DIR.relative_to(BENCH.parent)}"
        )
        return 0

    if not args.mode or not args.slot:
        parser.error("--mode and --slot are required unless --write-contract-fixtures")

    campaign_path = args.campaign if args.campaign.is_absolute() else BENCH / args.campaign
    campaign = load_json(campaign_path)
    model_id, task_id, run_index = parse_slot(args.slot, campaign)
    pep_gt = load_json(BENCH / "ground_truth" / "PEP_fx_organic_growth_gt.json") if task_id == "PEP_fx_organic_growth" else None

    path = agent_output_path(campaign, model_id, task_id, run_index)
    write_agent_output(path, args.mode, task_id, pep_gt)
    action = "deleted" if args.mode == "missing" else f"wrote ({args.mode})"
    print(f"{action}: {path.relative_to(BENCH.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
