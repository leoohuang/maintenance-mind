"""End-to-end agent smoke checks that use the configured LLM."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.core import Agent

TEST_CASES = [
    {
        "question": "Tablet press #2 weight variation problem. What should I check?",
        "expect_tool": "search_work_orders",
    },
    {
        "question": "What is the procedure for calibrating a tablet press?",
        "expect_tool": "search_manuals",
    },
]


def main():
    agent = Agent(verbose=False)
    for index, case in enumerate(TEST_CASES, start=1):
        print(f"\n=== Test {index}: {case['question'][:60]}... ===")
        agent.reset()
        run = agent.run(case["question"])
        tool_calls = [step for step in run.steps if step.kind == "tool_call"]
        reflections = [step for step in run.steps if step.kind == "reflection"]
        called = {step.content["name"] for step in tool_calls}
        print(f"  Iterations: {run.iterations}")
        print(f"  Tool calls: {sorted(called)}")
        print(f"  Reflections: {len(reflections)}")
        print(f"  Final length: {len(run.final_answer)} chars")
        print(f"  Expected tool called: {case['expect_tool'] in called}")


if __name__ == "__main__":
    main()
