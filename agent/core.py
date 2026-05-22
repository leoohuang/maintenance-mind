"""MaintenanceMind ReAct loop with reflective evidence evaluation."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from rich.console import Console

from agent.llm import client
from agent.memory import extract_and_update, load_memory, memory_as_prompt
from agent.reflection import reflect
from agent.skills_loader import load_system_prompt
from tools.registry import register_all

console = Console()
MAX_ITERATIONS = 8


@dataclass
class AgentStep:
    """One visible step in an agent run."""

    kind: str
    content: Any
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRun:
    """Result of a single user query."""

    question: str
    steps: list[AgentStep] = field(default_factory=list)
    final_answer: str = ""
    messages: list[dict[str, Any]] = field(default_factory=list)
    iterations: int = 0


class Agent:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.registry = register_all()
        base_prompt = load_system_prompt()
        memory_prompt = memory_as_prompt(load_memory())
        self.system_prompt = (
            f"{base_prompt}\n\n{memory_prompt}" if memory_prompt else base_prompt
        )
        self.history: list[dict[str, Any]] = []

    def _log(self, message: str, style: str = ""):
        if self.verbose:
            console.print(f"[{style}]{message}[/{style}]" if style else message)

    @staticmethod
    def _serialize_tool_result(result: Any) -> str:
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)

    def run(self, user_message: str) -> AgentRun:
        """Investigate one user message and return trace plus final answer."""
        run = AgentRun(question=user_message)
        self.history.append({"role": "user", "content": user_message})
        messages = [{"role": "system", "content": self.system_prompt}, *self.history]
        tools = self.registry.schemas()

        for iteration in range(MAX_ITERATIONS):
            run.iterations = iteration + 1
            self._log(f"\n[iter {iteration + 1}] querying LLM...", "dim")
            response = client.chat(messages=messages, tools=tools)
            message = response.choices[0].message

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]
            messages.append(assistant_message)

            if not message.tool_calls:
                final_answer = message.content or ""
                run.final_answer = final_answer
                run.steps.append(AgentStep(kind="final", content=final_answer))
                self._log(
                    f"\n[bold green]Final answer:[/bold green]\n{final_answer}"
                )
                self.history.append(
                    {"role": "assistant", "content": final_answer}
                )
                run.messages = messages
                try:
                    extract_and_update(user_message, final_answer)
                except Exception as error:
                    self._log(f"[red]memory extraction failed: {error}[/red]")
                return run

            if message.content:
                run.steps.append(AgentStep(kind="thought", content=message.content))
                self._log(f"[yellow]thought:[/yellow] {message.content}")

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                except json.JSONDecodeError:
                    arguments = {}

                self._log(f"[cyan]-> tool:[/cyan] {name}({arguments})")
                run.steps.append(
                    AgentStep(
                        kind="tool_call",
                        content={"name": name, "arguments": arguments},
                        metadata={"call_id": tool_call.id},
                    )
                )
                result = self.registry.execute(name, arguments)
                serialized = self._serialize_tool_result(result)
                run.steps.append(
                    AgentStep(
                        kind="tool_result",
                        content=result,
                        metadata={"call_id": tool_call.id, "tool_name": name},
                    )
                )
                preview = serialized[:200] + (
                    "..." if len(serialized) > 200 else ""
                )
                self._log(f"[dim]<- {preview}[/dim]")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": serialized,
                    }
                )

            self._log("[magenta][reflecting on evidence...][/magenta]")
            reflection = reflect(messages)
            run.steps.append(
                AgentStep(
                    kind="reflection",
                    content=reflection.raw,
                    metadata={
                        "sufficiency": reflection.sufficiency,
                        "confidence": reflection.confidence,
                    },
                )
            )
            self._log(
                "[magenta]reflection:[/magenta] "
                f"sufficiency={reflection.sufficiency}, "
                f"confidence={reflection.confidence:.2f}"
            )
            if reflection.missing:
                self._log(f"[magenta]  missing:[/magenta] {reflection.missing}")
            if reflection.conflicts:
                self._log(
                    "[magenta]  conflicts:[/magenta] "
                    f"{len(reflection.conflicts)} detected"
                )

            if reflection.is_sufficient:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The reflection step assessed the evidence as "
                            f"sufficient (confidence: {reflection.confidence:.2f}). "
                            "Give the final structured answer now and cite "
                            "specific retrieved sources."
                        ),
                    }
                )
            elif reflection.next_tool and reflection.next_query:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The reflection step found the evidence insufficient. "
                            f"Missing: {reflection.missing}. "
                            f"Try calling {reflection.next_tool} with query "
                            f"'{reflection.next_query}'. Conflicts found: "
                            f"{json.dumps(reflection.conflicts) if reflection.conflicts else 'none'}."
                        ),
                    }
                )

        run.final_answer = "Iteration limit reached without sufficient evidence."
        run.steps.append(AgentStep(kind="final", content=run.final_answer))
        run.messages = messages
        self.history.append({"role": "assistant", "content": run.final_answer})
        return run

    def reset(self):
        """Clear in-memory conversation history."""
        self.history = []
