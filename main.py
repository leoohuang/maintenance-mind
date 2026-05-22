"""CLI entry point for MaintenanceMind."""
from __future__ import annotations

from rich.console import Console
from rich.prompt import Prompt

from agent.core import Agent

console = Console()


def main():
    console.print("[bold cyan]MaintenanceMind[/bold cyan]")
    console.print(
        "Type a maintenance question. Type 'quit' to exit or 'reset' for a "
        "new session.\n"
    )
    agent = Agent(verbose=True)
    while True:
        try:
            question = Prompt.ask("[bold]You[/bold]")
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not question.strip():
            continue
        if question.strip().lower() in {"quit", "exit", "q"}:
            break
        if question.strip().lower() == "reset":
            agent.reset()
            console.print("[dim]Session reset.[/dim]\n")
            continue
        agent.run(question)
        console.print()


if __name__ == "__main__":
    main()
