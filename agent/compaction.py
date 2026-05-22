"""Compact long conversation histories into an LLM-generated summary."""
from __future__ import annotations

from typing import Any

from agent.llm import client

COMPACTION_THRESHOLD = 12
KEEP_RECENT = 4


def compact_if_needed(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replace older messages with a short summary when history grows."""
    if len(messages) < COMPACTION_THRESHOLD + 1:
        return messages

    system = messages[0]
    middle = messages[1:-KEEP_RECENT]
    recent = messages[-KEEP_RECENT:]
    if not middle:
        return messages

    summary_text = "\n".join(
        f"[{message['role']}] {str(message.get('content', ''))[:200]}"
        for message in middle
    )
    response = client.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Summarize the following conversation segment in 5-8 "
                    "bullet points, preserving facts, tool results, and "
                    "decisions. Be concise."
                ),
            },
            {"role": "user", "content": summary_text},
        ],
        temperature=0.0,
        max_tokens=500,
    )
    summary = response.choices[0].message.content or ""
    return [
        system,
        {
            "role": "user",
            "content": f"[Previous conversation summary]\n{summary}\n[End of summary]",
        },
        *recent,
    ]
