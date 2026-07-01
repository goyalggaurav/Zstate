"""OpenAI-compatible chat agent with function calling."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

from agents.tool_specs import TOOL_DEFINITIONS


def _ssl_context() -> ssl.SSLContext:
    """Build SSL context with certifi CAs (fixes macOS python.org CERTIFICATE_VERIFY_FAILED)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _system_prompt(episode: dict) -> str:
    return (
        "You are an equity research analyst agent in a controlled evaluation environment.\n"
        "Use ONLY the provided tools — no external data or memory of real filings.\n"
        "Retrieve evidence before stating numbers. Cite notes from tool outputs.\n"
        "When ready, brief the PM then submit via submit_recommendation.\n\n"
        f"EPISODE BRIEF:\n{episode['brief']['text']}"
    )


class OpenAICompatAgent:
    """LLM agent via OpenAI Chat Completions API (or compatible base URL)."""

    def __init__(
        self,
        episode: dict,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.episode = episode
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": _system_prompt(episode)},
            {"role": "user", "content": "Begin the episode. Retrieve filing data and work toward adjusted EPS."},
        ]
        self.pending_tool_calls: list[dict] | None = None
        self._pending_index = 0

    def _request(self, payload: dict) -> dict:
        if not self.api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Export it or use --agent mock for offline runs."
            )
        body = json.dumps(payload).encode("utf-8")
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
            with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API error {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
                raise RuntimeError(
                    "SSL certificate verify failed. Fix: pip3 install certifi "
                    "(then retry), or run macOS 'Install Certificates.command' "
                    "for your Python install. See env_v1/docs/AGENT_ADAPTERS.md."
                ) from e
            raise RuntimeError(f"LLM network error: {e.reason}") from e

    def _parse_tool_calls(self, message: dict) -> list[dict]:
        calls = message.get("tool_calls") or []
        parsed: list[dict] = []
        for call in calls:
            fn = call.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            parsed.append({"id": call.get("id"), "name": name, "arguments": args})
        return parsed

    def next_action(self, context: dict[str, Any]) -> dict | None:
        """Return next env action dict, or None when episode should end."""
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
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "temperature": 0,
        }
        data = self._request(payload)
        choice = data["choices"][0]["message"]
        self.messages.append(choice)

        tool_calls = self._parse_tool_calls(choice)
        if tool_calls:
            self.pending_tool_calls = tool_calls
            self._pending_index = 0
            return self.next_action(context)

        content = (choice.get("content") or "").strip()
        if content:
            return {"type": "send_message_to_pm", "text": content}
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
        self._last_tool_call_id = call.get("id")
        self._last_tool_name = name

        if name == "send_message_to_pm":
            return {"type": "send_message_to_pm", "text": args.get("message", "")}
        if name == "submit_recommendation":
            action = {"type": "submit_recommendation", **args}
            action.setdefault("submitted", True)
            return action
        return {"type": "tool_call", "tool": name, "input": args, "_tool_call_id": call.get("id")}

    @property
    def last_tool_call_id(self) -> str | None:
        return getattr(self, "_last_tool_call_id", None)

    @property
    def last_tool_name(self) -> str | None:
        return getattr(self, "_last_tool_name", None)
