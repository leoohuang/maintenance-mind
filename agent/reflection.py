"""Self-reflective evidence evaluation after retrieval tool rounds."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent.llm import client

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "skills" / "reflection_prompt.md"
)


@dataclass
class Reflection:
    sufficiency: str
    missing: str
    next_tool: str | None
    next_query: str | None
    conflicts: list[dict[str, Any]]
    confidence: float
    raw: dict[str, Any]

    @property
    def is_sufficient(self) -> bool:
        return self.sufficiency == "sufficient"


def _summarize_history(messages: list[dict[str, Any]]) -> str:
    """Build a compact textual view of user, assistant, and tool messages."""
    lines = []
    for message in messages:
        role = message.get("role")
        if role == "user":
            lines.append(f"USER: {message.get('content', '')}")
        elif role == "assistant":
            if message.get("content"):
                lines.append(f"ASSISTANT (thought): {message['content']}")
            for tool_call in message.get("tool_calls", []) or []:
                function = tool_call.get("function", {})
                lines.append(
                    f"TOOL CALL: {function.get('name')}"
                    f"({function.get('arguments')})"
                )
        elif role == "tool":
            content = message.get("content", "")
            if len(content) > 1500:
                content = content[:1500] + "...[truncated]"
            lines.append(f"TOOL RESULT: {content}")
    return "\n".join(lines)


def reflect(messages: list[dict[str, Any]]) -> Reflection:
    """Ask the LLM to evaluate current evidence sufficiency."""
    reflection_messages = [
        {"role": "system", "content": PROMPT_PATH.read_text()},
        {
            "role": "user",
            "content": (
                "Here is the investigation so far:\n\n"
                + _summarize_history(messages)
                + "\n\nEvaluate now."
            ),
        },
    ]
    parsed = client.chat_json(reflection_messages, temperature=0.1)
    return Reflection(
        sufficiency=parsed.get("sufficiency", "insufficient"),
        missing=parsed.get("missing", ""),
        next_tool=parsed.get("next_tool"),
        next_query=parsed.get("next_query"),
        conflicts=parsed.get("conflicts", []) or [],
        confidence=float(parsed.get("confidence_score", 0.0)),
        raw=parsed,
    )
