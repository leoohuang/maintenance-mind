"""Tools for semantic search and lookup over historical work orders."""
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

        index = VectorIndex("work_orders")
        if not index.load(INDEX_DIR):
            return None
        _index = index
    return _index


def search_orders(query: str, top_k: int = 5) -> dict:
    """Search historical maintenance work orders by semantic similarity."""
    index = _get_index()
    if index is None:
        return {"error": "Work-order index not built. Run scripts/build_index.py"}

    formatted = []
    for result in index.search(query, top_k=min(max(top_k, 1), 10)):
        metadata = result["metadata"]
        formatted.append(
            {
                "order_id": metadata.get("order_id"),
                "date": metadata.get("date"),
                "equipment": metadata.get("equipment"),
                "equipment_id": metadata.get("equipment_id"),
                "issue": metadata.get("reported_issue"),
                "diagnosis": metadata.get("diagnosis"),
                "root_cause": metadata.get("root_cause"),
                "actions": metadata.get("actions_taken", []),
                "parts_replaced": metadata.get("parts_replaced", []),
                "relevance": round(result["score"], 3),
            }
        )
    return {"results": formatted, "count": len(formatted)}


def get_order(order_id: str) -> dict:
    """Return a full work order by ID."""
    index = _get_index()
    if index is None:
        return {"error": "Work-order index not built."}
    for document in index.documents:
        if document["metadata"].get("order_id") == order_id:
            return document["metadata"]
    return {"error": f"Order {order_id} not found"}


def register(registry: ToolRegistry):
    registry.register(
        Tool(
            name="search_work_orders",
            description=(
                "Semantic search over historical maintenance work orders. "
                "Use this first for equipment-specific issues because past "
                "cases often reveal likely root causes and corrective actions."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language query with equipment and symptoms."
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results, default 5 and max 10.",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
            },
            handler=search_orders,
        )
    )
    registry.register(
        Tool(
            name="get_work_order",
            description=(
                "Retrieve full details of a specific work order by ID after "
                "search_work_orders surfaces a highly relevant case."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Work-order ID such as WO-2024-1234.",
                    }
                },
                "required": ["order_id"],
            },
            handler=get_order,
        )
    )
