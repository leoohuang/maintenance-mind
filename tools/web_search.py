"""Public web search tool backed by DuckDuckGo."""
from __future__ import annotations

from tools.registry import Tool, ToolRegistry


def web_search(query: str, max_results: int = 5) -> dict:
    """Search public web snippets through DuckDuckGo."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {"error": "ddgs not installed"}

    try:
        with DDGS() as ddgs:
            raw_results = list(
                ddgs.text(query, max_results=min(max(max_results, 1), 8))
            )
    except Exception as error:
        return {"error": f"Web search failed: {type(error).__name__}: {error}"}

    results = [
        {
            "title": result.get("title", ""),
            "url": result.get("href", ""),
            "snippet": result.get("body", ""),
        }
        for result in raw_results
    ]
    return {"results": results, "count": len(results)}


def register(registry: ToolRegistry):
    registry.register(
        Tool(
            name="web_search",
            description=(
                "Search the public web for information not present in internal "
                "work orders or manuals. Use this after internal retrieval or "
                "for recent external information."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific web search query.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results, default 5 and max 8.",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 8,
                    },
                },
                "required": ["query"],
            },
            handler=web_search,
        )
    )
