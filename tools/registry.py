"""Registry for MaintenanceMind tools and OpenAI function schemas."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Any]

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        tool = self.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}"}
        try:
            return tool.handler(**arguments)
        except Exception as error:
            return {
                "error": (
                    f"Tool {name} failed: {type(error).__name__}: {error}"
                )
            }


registry = ToolRegistry()


def register_all() -> ToolRegistry:
    """Import and register all tools once."""
    if registry.names():
        return registry

    from tools import manuals, web_search, work_orders

    work_orders.register(registry)
    manuals.register(registry)
    web_search.register(registry)
    return registry
