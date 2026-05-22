"""Smoke checks for the registered MaintenanceMind tools."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.registry import register_all


def main():
    registry = register_all()
    print("Registered tools:", registry.names())

    print("\n=== search_work_orders ===")
    orders = registry.execute(
        "search_work_orders",
        {"query": "tablet press weight problem", "top_k": 2},
    )
    print(orders)

    print("\n=== search_manuals ===")
    manuals = registry.execute(
        "search_manuals",
        {"query": "weight variation troubleshooting", "top_k": 2},
    )
    print(manuals)

    print("\n=== web_search ===")
    web = registry.execute(
        "web_search",
        {"query": "pharmaceutical tablet press maintenance", "max_results": 3},
    )
    print(web)


if __name__ == "__main__":
    main()
