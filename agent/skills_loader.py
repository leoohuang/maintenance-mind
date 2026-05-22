"""Load Markdown skills into the MaintenanceMind system prompt."""
from __future__ import annotations

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def load_system_prompt() -> str:
    """Concatenate all skill Markdown files with `system.md` first."""
    if not SKILLS_DIR.exists():
        return "You are a helpful assistant."

    files = sorted(SKILLS_DIR.glob("*.md"))
    system_files = [path for path in files if path.name == "system.md"]
    other_files = [
        path
        for path in files
        if path.name not in {"system.md", "reflection_prompt.md"}
    ]
    return "\n\n---\n\n".join(
        path.read_text() for path in system_files + other_files
    )
