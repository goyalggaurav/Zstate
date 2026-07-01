"""OpenAI-compatible agent for Track A benchmark tasks (no PM)."""

from __future__ import annotations

import json
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any

from agents.benchmark_tool_specs import CORPUS_TOOLS, SUBMIT_TOOL, build_tool_definitions, metric_keys, parse_submission_args


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _system_prompt(task: dict, bundle: dict) -> str:
    registry = bundle.get("section_registry", [])
    slug_lines = "\n".join(
        f"  - {e['section_slug']}: {e.get('name', e['section_id'])}"
        for e in registry
    )
    policy_lines = ""
    for note in bundle.get("policy_notes", []):
        if note.get("agent_ack_required"):
            policy_lines += f"\n- REQUIRED policy ack `{note['policy_id']}`: {note['statement']}"
        else:
            policy_lines += f"\n- Policy note `{note['policy_id']}`: {note['statement']}"

    ids = sorted(metric_keys(task["task_id"]))
    metric_list = ", ".join(ids)

    return (
        "You are an equity research analyst agent in a controlled benchmark evaluation.\n"
        "Use ONLY the provided tools against the fixed corpus — no external data.\n"
        "For Search_Filing, pass exact section_slug tokens (lowercase, underscores).\n"
        "Retrieve evidence before stating numbers. Use Python_Interpreter to verify arithmetic.\n"
        "When ready, call submit_structured_output with:\n"
        f"  - metrics: all {len(ids)} required fields ({metric_list})\n"
        f"  - citations: exactly one entry per metrics key ({metric_list}) — no omissions\n"
        "  - each citation snippet must be a verbatim substring from a section you retrieved\n"
        "  - policy_acknowledgements: include every REQUIRED policy_id listed below\n\n"
        f"TASK:\n{task['prompt']['text']}\n\n"
        f"ALLOWED SECTION SLUGS:\n{slug_lines or '  (see tool enum)'}"
        f"{policy_lines}"
    )


class OpenAIBenchmarkAgent:
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
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.tools = build_tool_definitions(task, bundle)
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": _system_prompt(task, bundle)},
            {"role": "user", "content": (
                "Begin the task. Retrieve filing sections with tools, verify arithmetic, then submit "
                "metrics + verbatim citations + any required policy acknowledgements."
            )},
        ]
        self.pending_tool_calls: list[dict] | None = None
        self._pending_index = 0

    def _request(self, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set. Use --agent scripted/mock for offline runs.")
        body = json.dumps(payload).encode("utf-8")
        timeout = int(os.environ.get("OPENAI_TIMEOUT_SECONDS", "300"))
        max_retries = int(os.environ.get("OPENAI_MAX_RETRIES", "3"))
        last_error: Exception | None = None

        for attempt in range(max_retries):
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    last_error = e
                    continue
                raise RuntimeError(f"LLM API error {e.code}: {detail}") from e
            except (TimeoutError, socket.timeout) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"LLM request timed out after {max_retries} attempts") from e
            except urllib.error.URLError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"LLM network error: {e.reason}") from e
        raise RuntimeError(f"LLM request failed after {max_retries} attempts") from last_error

    def _parse_tool_calls(self, message: dict) -> list[dict]:
        parsed: list[dict] = []
        for call in message.get("tool_calls") or []:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            parsed.append({"id": call.get("id"), "name": name, "arguments": args})
        return parsed

    def next_action(self, context: dict[str, Any]) -> dict | None:
        if self.pending_tool_calls is not None:
            if self._pending_index >= len(self.pending_tool_calls):
                self.pending_tool_calls = None
                self._pending_index = 0
            else:
                call = self.pending_tool_calls[self._pending_index]
                self._pending_index += 1
                return self._tool_call_to_action(call)

        payload = {
            "model": self.model,
            "messages": self.messages,
            "tools": self.tools,
            "tool_choice": "auto",
            "temperature": 0,
        }
        data = self._request(payload)
        choice = data["choices"][0]["message"]
        self.messages.append(choice)

        tool_calls = self._parse_tool_calls(choice)
        if tool_calls:
            corpus_first = [c for c in tool_calls if c["name"] in CORPUS_TOOLS]
            submit_last = [c for c in tool_calls if c["name"] == SUBMIT_TOOL]
            other = [c for c in tool_calls if c not in corpus_first and c not in submit_last]
            self.pending_tool_calls = corpus_first + other + submit_last
            self._pending_index = 0
            return self.next_action(context)

        content = (choice.get("content") or "").strip()
        if content:
            return {"type": "agent_message", "text": content}
        return None

    def record_tool_result(self, tool_call_id: str | None, name: str, output: str) -> None:
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": name,
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
