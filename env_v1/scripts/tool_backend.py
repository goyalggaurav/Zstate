#!/usr/bin/env python3
"""Mock tool backend for env_v1 dual-control episodes."""

from __future__ import annotations

import argparse
import ast
import json
import operator
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_calc(expression: str) -> float:
    node = ast.parse(expression.strip(), mode="eval").body

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return OPS[ast.USub](_eval(n.operand))
        raise ValueError(f"Unsupported expression: {expression}")

    return _eval(node)


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
