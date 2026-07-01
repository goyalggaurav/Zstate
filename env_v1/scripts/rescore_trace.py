#!/usr/bin/env python3
"""Re-score env_v1 trace JSON files in place (updates *_scores.json and trace reward fields)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "env_v1" / "scripts"))

from score_episode import score_trace  # noqa: E402
from trace_utils import enrich_env_trace  # noqa: E402


def rescore(path: Path) -> dict:
    trace = json.loads(path.read_text(encoding="utf-8"))
    scores = score_trace(trace)
    enriched = enrich_env_trace(trace, scores)
    path.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
    score_path = path.with_name(path.stem + "_scores.json")
    score_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    return scores


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-score env_v1 trace files")
    parser.add_argument("traces", nargs="+", help="Trace JSON paths")
    args = parser.parse_args()
    for p in args.traces:
        path = Path(p)
        scores = rescore(path)
        print(
            f"{path.name}: composite={scores['composite_reward']} "
            f"fractures={scores['fracture_codes']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
