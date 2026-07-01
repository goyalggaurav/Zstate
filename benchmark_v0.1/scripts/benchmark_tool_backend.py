#!/usr/bin/env python3
"""Mock tool backend for benchmark_v0.1 Track A agent runtime."""

from __future__ import annotations

import argparse
import ast
import json
import operator
import re
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

TASK_BUNDLE: dict[str, str] = {
    "GOOGL_footnote_reconciliation": "googl_q1_2026_bundle.json",
    "PEP_fx_organic_growth": "pep_fy2025_bundle.json",
    "AMZN_footnote_reconciliation": "amzn_fy2025_bundle.json",
}

NOT_FOUND_PREFIX = "NOT FOUND:"


def normalize_section_slug(raw: str) -> str:
    """Lowercase slug with spaces/hyphens → underscores."""
    return re.sub(r"[\s\-]+", "_", raw.strip().lower())


def is_canonical_slug(raw: str) -> bool:
    """Reject display names (e.g. 'Note 15') — agent must pass exact slug token."""
    slug = normalize_section_slug(raw)
    return raw == slug and bool(re.fullmatch(r"[a-z0-9_]+", slug))


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


def load_bundle(task_id: str) -> dict:
    filename = TASK_BUNDLE.get(task_id)
    if not filename:
        raise ValueError(f"No corpus bundle mapped for task {task_id!r}")
    path = BENCH / "corpus" / filename
    if not path.exists():
        raise FileNotFoundError(f"Corpus bundle not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


class BenchmarkToolBackend:
    def __init__(self, corpus: dict) -> None:
        self.corpus = corpus
        self.documents = corpus["documents"]
        self.keys = corpus["retrieval_keys"]
        self.section_registry = corpus.get("section_registry", [])
        self.registry_by_slug = {
            entry["section_slug"]: entry for entry in self.section_registry
        }
        self.registry_slugs = set(self.registry_by_slug)
        from archetype_roles import legacy_slug_map

        self._legacy_slug_map = legacy_slug_map(corpus)
        self.log: list[dict] = []

    def _resolve_slug(self, section_raw: str) -> str | None:
        if not is_canonical_slug(section_raw):
            return None
        slug = section_raw
        canonical = self._legacy_slug_map.get(slug, slug)
        if canonical in self.registry_slugs:
            return canonical
        if slug in self.registry_slugs:
            return slug
        return None

    def _search_filing(self, ticker: str, period: str, section_raw: str) -> tuple[str, str | None, str | None]:
        if not is_canonical_slug(section_raw):
            return (
                f"{NOT_FOUND_PREFIX} unknown section slug {section_raw!r}; "
                f"use canonical slug from section_registry (e.g. {sorted(self.registry_slugs)[:3]})",
                None,
                None,
            )
        slug = self._resolve_slug(section_raw)
        if slug is None:
            return (
                f"{NOT_FOUND_PREFIX} unknown section slug {section_raw!r}; "
                f"allowed: {sorted(self.registry_slugs)}",
                None,
                section_raw,
            )
        key = f"{ticker}:{period}:{slug}"
        doc_key = self.keys["Search_Filing"].get(key)
        if not doc_key:
            return (
                f"{NOT_FOUND_PREFIX} no filing for ticker={ticker!r} period={period!r} section={slug!r}",
                None,
                slug,
            )
        doc = self.documents[doc_key]
        return doc["excerpt"], doc.get("doc_id", doc_key), slug

    def call(self, tool: str, **kwargs) -> str:
        entry: dict = {"tool": tool, "input": kwargs}
        if tool in ("Search_Filing", "PDF_Parser"):
            ticker = kwargs.get("ticker", "")
            period = kwargs.get("period", "")
            section = kwargs.get("section", "")
            result, doc_id, slug = self._search_filing(ticker, period, section)
            if slug:
                entry["section_slug"] = slug
            if doc_id:
                entry["doc_id"] = doc_id
        elif tool == "Python_Interpreter":
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug benchmark_v0.1 tool backend")
    parser.add_argument("--task", default="GOOGL_footnote_reconciliation")
    args = parser.parse_args()
    backend = BenchmarkToolBackend(load_bundle(args.task))
    for cmd in [
        ("Search_Filing", {"ticker": "GOOGL", "period": "2026Q1", "section": "note_15"}),
        ("Python_Interpreter", {"expression": "89637 + 20028 + 411 + (-180)"}),
    ]:
        print(f"\n>>> {cmd[0]}({cmd[1]})")
        print(backend.call(cmd[0], **cmd[1])[:400])


if __name__ == "__main__":
    main()
