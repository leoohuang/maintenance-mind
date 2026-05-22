"""Persistent JSON memory for the MaintenanceMind agent."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.llm import client

MEMORY_PATH = Path(__file__).resolve().parent.parent / "memory" / "memory.json"
DEFAULT_MEMORY = {
    "facts": [],
    "recent_issues": [],
    "preferences": {},
    "last_updated": None,
}


def _default_memory() -> dict[str, Any]:
    return {
        "facts": [],
        "recent_issues": [],
        "preferences": {},
        "last_updated": None,
    }


def load_memory() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return _default_memory()
    try:
        return json.loads(MEMORY_PATH.read_text())
    except json.JSONDecodeError:
        return _default_memory()


def save_memory(memory: dict[str, Any]):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_PATH.write_text(json.dumps(memory, indent=2, ensure_ascii=False))


def memory_as_prompt(memory: dict[str, Any]) -> str:
    """Render durable memory as a compact system-prompt supplement."""
    if not memory.get("facts") and not memory.get("recent_issues"):
        return ""

    lines = ["## What I remember about this user/site"]
    for fact in memory.get("facts", [])[-10:]:
        lines.append(f"- {fact}")

    recent_issues = memory.get("recent_issues", [])[-5:]
    if recent_issues:
        lines.append("\nRecent issues investigated:")
        for issue in recent_issues:
            lines.append(f"- {issue.get('date', '?')}: {issue.get('summary', '')}")

    preferences = memory.get("preferences", {})
    if preferences:
        lines.append(f"\nUser preferences: {preferences}")
    return "\n".join(lines)


EXTRACTION_PROMPT = """You extract durable facts and preferences from a maintenance
conversation.

Look at the user message and the assistant's final response. Extract only facts
that are specific to the user's work context, likely useful later, and clearly
stated rather than inferred. Do not extract generic technical knowledge.

Respond with only a JSON object:
{
  "new_facts": ["fact 1", "fact 2"],
  "issue_summary": "one short issue summary or empty string",
  "preferences_update": {"key": "value"}
}
Return empty arrays or objects when nothing should be stored."""


def extract_and_update(
    user_message: str,
    assistant_message: str,
    memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract durable memory from a finished conversation turn."""
    if memory is None:
        memory = load_memory()

    extraction = client.chat_json(
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {
                "role": "user",
                "content": f"USER: {user_message}\n\nASSISTANT: {assistant_message}",
            },
        ],
        temperature=0.0,
    )

    existing_facts = set(memory.get("facts", []))
    for fact in extraction.get("new_facts", []) or []:
        if fact and fact not in existing_facts:
            memory.setdefault("facts", []).append(fact)
            existing_facts.add(fact)

    issue_summary = extraction.get("issue_summary", "")
    if issue_summary:
        memory.setdefault("recent_issues", []).append(
            {
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "summary": issue_summary,
            }
        )
        memory["recent_issues"] = memory["recent_issues"][-20:]

    preferences_update = extraction.get("preferences_update", {}) or {}
    if preferences_update:
        memory.setdefault("preferences", {}).update(preferences_update)

    save_memory(memory)
    return memory
