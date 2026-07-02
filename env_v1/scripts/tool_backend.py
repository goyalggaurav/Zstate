#!/usr/bin/env python3
"""Mock tool backend for env_v1 dual-control episodes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from shared.safe_calc import safe_calc  # noqa: E402


class ToolBackend:
    def __init__(self, corpus: dict) -> None:
        self.corpus = corpus
        self.documents = corpus["documents"]
        self.keys = corpus["retrieval_keys"]
        self.log: list[dict] = []

    def call(self, tool: str, **kwargs) -> str:
        entry = {"tool": tool, "input": kwargs}
        if tool == "get_filing":
            doc_type = kwargs.get("doc_type", "")
            period = kwargs.get("period", "")
            key = f"{doc_type}:{period}"
            doc_id = self.keys["get_filing"].get(key)
            if not doc_id:
                result = f"NOT FOUND: no filing for doc_type={doc_type!r} period={period!r}"
            else:
                result = self.documents[doc_id]["excerpt"]
                entry["doc_id"] = doc_id
        elif tool == "get_transcript":
            period = kwargs.get("period", "")
            doc_id = self.keys["get_transcript"].get(period)
            if not doc_id:
                result = f"NOT FOUND: no transcript for period={period!r}"
            else:
                result = self.documents[doc_id]["excerpt"]
                entry["doc_id"] = doc_id
        elif tool == "get_consensus":
            metric = kwargs.get("metric", "eps")
            period = kwargs.get("period", "")
            key = f"{metric}:{period}"
            doc_id = self.keys["get_consensus"].get(key)
            if not doc_id:
                result = f"NOT FOUND: no consensus for metric={metric!r} period={period!r}"
            else:
                result = self.documents[doc_id]["excerpt"]
                entry["doc_id"] = doc_id
        elif tool == "calculator":
            expr = kwargs.get("expression", "")
            try:
                result = str(safe_calc(expr))
            except (ValueError, SyntaxError, ZeroDivisionError) as e:
                result = f"CALC ERROR: {e}"
        else:
            result = f"UNKNOWN TOOL: {tool}"
        entry["output_preview"] = result[:200]
        entry["output"] = result
        self.log.append(entry)
        return result


def load_corpus(episode_id: str) -> dict:
    ep_path = ROOT / "episodes" / f"{episode_id}.json"
    ep = json.loads(ep_path.read_text(encoding="utf-8"))
    corpus_path = (ep_path.parent / ep["corpus_ref"]).resolve()
    return json.loads(corpus_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug env_v1 tool backend")
    parser.add_argument("--episode", default="solaris_adj_eps_dispute_v1")
    args = parser.parse_args()
    corpus = load_corpus(args.episode)
    backend = ToolBackend(corpus)
    for cmd in [
        ("get_filing", {"doc_type": "10-Q", "period": "2025Q2"}),
        ("get_filing", {"doc_type": "10-K", "period": "FY2024"}),
        ("get_consensus", {"metric": "eps", "period": "2025Q2"}),
        ("calculator", {"expression": "1.42 - 0.18 - 0.04"}),
    ]:
        print(f"\n>>> {cmd[0]}({cmd[1]})")
        print(backend.call(cmd[0], **cmd[1])[:400])


if __name__ == "__main__":
    main()
