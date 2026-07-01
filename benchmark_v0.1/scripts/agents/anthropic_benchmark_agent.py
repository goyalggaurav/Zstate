"""Anthropic Messages API agent for Track A benchmark tasks (no PM)."""

from __future__ import annotations

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from typing import Any

from agents.benchmark_tool_specs import (
    CORPUS_TOOLS,
    SUBMIT_TOOL,
    build_system_prompt,
    build_tool_definitions,
    parse_submission_args,
    to_anthropic_tools,
)
from agents.llm_retry import retry_sleep_seconds

USER_START = (
    "Begin the task. Retrieve filing sections with tools, verify arithmetic, then submit "
    "metrics + verbatim citations (copy-paste from tool output, never paraphrase headers) "
    "and any required policy acknowledgements."
)


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class AnthropicBenchmarkAgent:
    def __init__(
        self,
        task: dict,
        bundle: dict,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.task = task
        self.bundle = bundle
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = (base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")).rstrip("/")
        self.system = build_system_prompt(task, bundle)
        self.tools = to_anthropic_tools(build_tool_definitions(task, bundle))
        self.messages: list[dict[str, Any]] = [
            {"role": "user", "content": USER_START},
        ]
        self.pending_tool_calls: list[dict] | None = None
        self._pending_index = 0
        self._pending_tool_results: list[dict] = []

    def _request(self, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set. Use --agent scripted/mock for offline runs.")
        body = json.dumps(payload).encode("utf-8")
        timeout = int(os.environ.get("ANTHROPIC_TIMEOUT_SECONDS", "300"))
        max_retries = int(os.environ.get("ANTHROPIC_MAX_RETRIES", "5"))
        api_version = os.environ.get("ANTHROPIC_API_VERSION", "2023-06-01")
        last_error: Exception | None = None

        for attempt in range(max_retries):
            req = urllib.request.Request(
                f"{self.base_url}/messages",
                data=body,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": api_version,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                if e.code in (429, 500, 502, 503, 504, 529) and attempt < max_retries - 1:
                    wait = retry_sleep_seconds(e.code, detail, attempt)
                    time.sleep(wait)
                    last_error = e
                    continue
                raise RuntimeError(f"Anthropic API error {e.code}: {detail}") from e
            except (TimeoutError, socket.timeout) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"Anthropic request timed out after {max_retries} attempts") from e
            except urllib.error.URLError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"Anthropic network error: {e.reason}") from e
        raise RuntimeError(f"Anthropic request failed after {max_retries} attempts") from last_error

    def _flush_tool_results(self) -> None:
        if self._pending_tool_results:
            self.messages.append({"role": "user", "content": list(self._pending_tool_results)})
            self._pending_tool_results = []

    def _parse_tool_calls(self, content: list[dict]) -> list[dict]:
        parsed: list[dict] = []
        for block in content or []:
            if block.get("type") != "tool_use":
                continue
            parsed.append({
                "id": block.get("id"),
                "name": block.get("name", ""),
                "arguments": block.get("input") or {},
            })
        return parsed

    def next_action(self, context: dict[str, Any]) -> dict | None:
        if self.pending_tool_calls is not None:
            if self._pending_index >= len(self.pending_tool_calls):
                self.pending_tool_calls = None
                self._pending_index = 0
                self._flush_tool_results()
            else:
                call = self.pending_tool_calls[self._pending_index]
                self._pending_index += 1
                return self._tool_call_to_action(call)

        payload = {
            "model": self.model,
            "max_tokens": int(os.environ.get("ANTHROPIC_MAX_TOKENS", "8192")),
            "system": self.system,
            "messages": self.messages,
            "tools": self.tools,
            "temperature": 0,
        }
        data = self._request(payload)
        content = data.get("content") or []
        self.messages.append({"role": "assistant", "content": content})

        tool_calls = self._parse_tool_calls(content)
        if tool_calls:
            corpus_first = [c for c in tool_calls if c["name"] in CORPUS_TOOLS]
            submit_last = [c for c in tool_calls if c["name"] == SUBMIT_TOOL]
            other = [c for c in tool_calls if c not in corpus_first and c not in submit_last]
            self.pending_tool_calls = corpus_first + other + submit_last
            self._pending_index = 0
            return self.next_action(context)

        text_parts = [
            block.get("text", "")
            for block in content
            if block.get("type") == "text"
        ]
        content_text = "\n".join(part.strip() for part in text_parts if part.strip())
        if content_text:
            return {"type": "agent_message", "text": content_text}
        return None

    def record_tool_result(self, tool_call_id: str | None, name: str, output: str) -> None:
        self._pending_tool_results.append({
            "type": "tool_result",
            "tool_use_id": tool_call_id,
            "content": output[:8000],
        })

    def _tool_call_to_action(self, call: dict) -> dict:
        name = call["name"]
        args = call["arguments"]
        if name == SUBMIT_TOOL:
            metrics, submission = parse_submission_args(args, self.task)
            action: dict = {
                "type": "submit_structured_output",
                "structured_output": metrics,
                "_tool_call_id": call.get("id"),
            }
            if submission is not None:
                action["submission"] = submission
            return action
        if name in CORPUS_TOOLS:
            backend_tool = "Python_Interpreter" if name == "Python_Interpreter" else name
            inp = args if name == "Python_Interpreter" else {
                "ticker": args.get("ticker", self.task["ticker"]),
                "period": args.get("period", self.task["required_documents"][0]["fiscal_period"]),
                "section": args.get("section", ""),
            }
            return {
                "type": "tool_call",
                "tool": backend_tool,
                "input": inp,
                "_tool_call_id": call.get("id"),
            }
        raise ValueError(f"Unknown tool from model: {name!r}")
