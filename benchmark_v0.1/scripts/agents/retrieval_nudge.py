"""Inject a one-shot user nudge when the agent stalls after filing retrievals."""

from __future__ import annotations

RETRIEVAL_TOOLS = frozenset({"Search_Filing", "PDF_Parser"})
NUDGE_AFTER_RETRIEVALS = 3

NUDGE_TEXT = (
    "You have retrieved filing sections but have not yet computed or submitted. "
    "Use Python_Interpreter for any arithmetic checks, then call submit_structured_output "
    "with metric values and verbatim citations copied from tool output."
)


class RetrievalNudgeTracker:
    def __init__(self) -> None:
        self.retrieval_count = 0
        self.python_used = False
        self.nudge_sent = False

    def on_tool_result(self, name: str) -> str | None:
        if name == "Python_Interpreter":
            self.python_used = True
        if name in RETRIEVAL_TOOLS:
            self.retrieval_count += 1
        if name == "submit_structured_output":
            return None
        if (
            not self.nudge_sent
            and self.retrieval_count >= NUDGE_AFTER_RETRIEVALS
            and not self.python_used
        ):
            self.nudge_sent = True
            return NUDGE_TEXT
        return None
