#!/usr/bin/env python3
"""Tests for OpenAI agent tool-call ordering (no API key required)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agents.openai_agent import _order_tool_calls


def test_corpus_tools_before_episode_tools() -> None:
    calls = [
        {"id": "c1", "name": "send_message_to_pm", "arguments": {}},
        {"id": "c2", "name": "get_filing", "arguments": {}},
        {"id": "c3", "name": "submit_recommendation", "arguments": {}},
        {"id": "c4", "name": "get_consensus", "arguments": {}},
    ]
    ordered = _order_tool_calls(calls)
    names = [c["name"] for c in ordered]
    assert names.index("get_filing") < names.index("send_message_to_pm")
    assert names.index("get_consensus") < names.index("submit_recommendation")


if __name__ == "__main__":
    test_corpus_tools_before_episode_tools()
    print("OK openai agent protocol tests")
