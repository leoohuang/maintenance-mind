"""Tool for semantic search over equipment manuals."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tools.registry import Tool, ToolRegistry

if TYPE_CHECKING:
    from agent.retriever import VectorIndex

INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "indices"
_index: VectorIndex | None = None


def _get_index() -> VectorIndex | None:
    global _index
    if _index is None:
        from agent.retriever import VectorIndex

        index = VectorIndex("manuals")
        if not index.load(INDEX_DIR):
            return None
        _index = index
    return _index


def search_manuals(query: str, top_k: int = 3) -> dict:
    """Search manual chunks for procedures and troubleshooting guidance."""
    index = _get_index()
    if index is None:
        return {"error": "Manual index not built. Run scripts/build_index.py"}

    formatted = []
    for result in index.search(query, top_k=min(max(top_k, 1), 5)):
        metadata = result["metadata"]
        formatted.append(
            {
                "source": metadata.get("source"),
                "chunk_id": metadata.get("chunk_id"),
                "content": result["text"],
                "relevance": round(result["score"], 3),
            }
        )
    return {"results": formatted, "count": len(formatted)}


def register(registry: ToolRegistry):
    registry.register(
        Tool(
            name="search_manuals",
            description=(
                "Search equipment manuals for relevant procedures, "
                "specifications, and troubleshooting guidance."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query about a procedure or specification.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results, default 3 and max 5.",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 5,
                    },
                },
                "required": ["query"],
            },
            handler=search_manuals,
        )
    )
