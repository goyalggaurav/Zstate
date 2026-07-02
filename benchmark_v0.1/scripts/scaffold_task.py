#!/usr/bin/env python3
"""Scaffold a new Track A task from archetype template (P3-31).

Usage:
  python scaffold_task.py --task-id EXAMPLE_footnote_reconciliation \\
    --archetype F_exact --ticker EXAMPLE --fiscal-period FY2025
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BENCH = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from archetype_roles import archetype_def, load_archetype_schema  # noqa: E402


def scaffold_task(
    task_id: str,
    *,
    archetype: str,
    ticker: str,
    fiscal_period: str,
    out_dir: Path | None = None,
) -> dict[str, Path]:
    spec = archetype_def(archetype)
    base = out_dir or (BENCH / "_scaffold" / task_id)
    base.mkdir(parents=True, exist_ok=True)

    task_doc = {
        "task_id": task_id,
        "version": "0.0.1-scaffold",
        "status": "draft",
        "benchmark_version": "benchmark_v0.1",
        "ticker": ticker,
        "archetype": archetype,
        "task_type": spec["task_type"],
        "prompt": {"text": f"TODO — {task_id} prompt for {ticker} {fiscal_period}", "constraints": []},
        "required_documents": [
            {
                "doc_id": f"{ticker}_PRIMARY",
                "form_type": "10-K",
                "fiscal_period": fiscal_period,
                "role": "primary",
            }
        ],
        "allowed_tools": ["Search_Filing", "PDF_Parser", "Python_Interpreter"],
        "expected_outputs": {"schema_ref": "forensics_report_v1", "structured_fields": []},
        "scoring": {
            "task_type_weights": {"layer1": 0.55, "layer2": 0.25, "layer3": 0.20},
            "layer2_method": "gold_path_automated",
        },
    }

    gt_doc = {
        "task_id": task_id,
        "fiscal_period": fiscal_period,
        "unit": "USD_millions",
        "extracted_values": [],
        "computed_values": [],
        "failure_modes": [],
    }
    if archetype == "F_exact":
        gt_doc["verification_schema"] = {
            "archetype": "F_exact",
            "segment_metrics": [],
            "consolidated_metric": "consolidated_net_sales",
        }

    path_order = spec.get("default_path_order") or []
    gold_doc = {
        "task_id": task_id,
        "version": "0.0.1-scaffold",
        "archetype": archetype,
        "task_type": spec["task_type"],
        "fiscal_period": fiscal_period,
        "minimal_section_set": [
            {"section_id": f"{slug}_TODO", "name": slug, "required": True, "reason": "TODO"}
            for slug in path_order
        ],
        "required_tool_classes": ["Search_Filing", "Python_Interpreter"],
        "anti_patterns": ["produce_buy_hold_sell_recommendation"],
        "failure_mode_map": [],
        "l2_gold_path": {
            "weights": {"section_recall": 0.35, "section_order": 0.40, "tool_coverage": 0.25},
            "expected_section_order": path_order,
            "required_tools": ["Search_Filing", "Python_Interpreter"],
        },
        "l3_citation_rules": {
            "distinct_snippets_required": True,
            "computed_citations": {},
        },
    }

    paths = {
        "task": base / f"{task_id}.json",
        "ground_truth": base / f"{task_id}_gt.json",
        "gold_path": base / f"{task_id}_gold_path.json",
        "readme": base / "SCAFFOLD_README.md",
    }
    paths["task"].write_text(json.dumps(task_doc, indent=2) + "\n", encoding="utf-8")
    paths["ground_truth"].write_text(json.dumps(gt_doc, indent=2) + "\n", encoding="utf-8")
    paths["gold_path"].write_text(json.dumps(gold_doc, indent=2) + "\n", encoding="utf-8")
    paths["readme"].write_text(
        "\n".join([
            f"# Scaffold — {task_id}",
            "",
            f"- Archetype: `{archetype}`",
            f"- Path order: {' → '.join(path_order)}",
            "",
            "Next steps:",
            "1. Fill GT extracted_values + verification_schema",
            "2. Author corpus bundle + section_registry",
            "3. Add computed_citations in gold_path l3_citation_rules",
            "4. Run validate_publish_task.py before setting manifest status: published",
            "",
        ]) + "\n",
        encoding="utf-8",
    )
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold Track A task files from archetype (P3-31)")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--archetype", required=True, choices=sorted(load_archetype_schema()["archetypes"].keys()))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--fiscal-period", required=True)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    paths = scaffold_task(
        args.task_id,
        archetype=args.archetype,
        ticker=args.ticker.upper(),
        fiscal_period=args.fiscal_period,
        out_dir=args.out_dir,
    )
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
