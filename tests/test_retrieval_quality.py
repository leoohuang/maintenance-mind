"""Sanity checks for local vector retrieval relevance."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.retriever import VectorIndex


def check(index_name: str, queries: list[tuple[str, str]]):
    index = VectorIndex(index_name)
    if not index.load(Path("data/indices")):
        print(f"\n=== {index_name}: index not built ===")
        return

    print(f"\n=== {index_name} ===")
    for query, expected_keyword in queries:
        results = index.search(query, top_k=3)
        top_text = results[0]["text"].lower() if results else ""
        score = results[0]["score"] if results else 0
        contains = expected_keyword.lower() in top_text
        print(
            f"  {query!r} -> score={score:.2f}, "
            f"contains {expected_keyword!r}: {contains}"
        )


if __name__ == "__main__":
    check(
        "work_orders",
        [
            ("tablet press weight variation", "weight"),
            ("mixer motor overload", "mixer"),
            ("coating uniformity", "coating"),
        ],
    )
    check(
        "manuals",
        [
            ("weight variation troubleshooting", "weight"),
            ("blister sealing defects", "seal"),
        ],
    )
