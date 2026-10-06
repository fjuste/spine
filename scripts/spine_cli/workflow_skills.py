"""Publish Spine slash commands as Claude Code and Antigravity skills."""

from __future__ import annotations

from pathlib import Path

WORKFLOW_TARGETS: frozenset[str] = frozenset({"claude", "antigravity"})

_SKILL_TEMPLATE = """\
---
name: {name}
description: {description}
disable-model-invocation: true
---

Follow the Spine workflow in [procedure.md](procedure.md). Arguments passed after the slash command are `$ARGUMENTS`.

When procedure.md names a Spine skill with `@name` (for example `@grill-me`, `@writing-plans`, or `@executing-plans`), load that installed skill and follow it. On Claude Code and Antigravity the slash form is `/name`.
"""


def workflow_names(content: Path) -> list[str]:
    """Return slash-command stems under ``commands/``.

    Args:
        content: Spine tree that holds ``commands/``.

    Returns:
        Sorted command names without the ``.md`` suffix.
    """
    commands = content / "commands"
    if not commands.is_dir():
        return []
    return sorted(path.stem for path in commands.glob("*.md") if path.is_file())


def command_description(path: Path) -> str:
    """Read a command description for skill frontmatter.

    Args:
        path: Command markdown file.

    Returns:
        Frontmatter ``description``, otherwise the first heading, otherwise
        a fallback that names the slash command.
    """
    text = path.read_text(encoding="utf-8")
    from_frontmatter = _frontmatter_description(text)
    if from_frontmatter:
        return from_frontmatter
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                return title
    return f"Run the /{path.stem} Spine workflow."


def render_skill_markdown(name: str, description: str) -> str:
    """Build ``SKILL.md`` text for one Spine workflow.

    Args:
        name: Skill and slash-command name.
        description: When the workflow should run.

    Returns:
        Markdown with Claude Code and Agent Skills frontmatter.
    """
    return _SKILL_TEMPLATE.format(name=name, description=_yaml_quote(description))


def _frontmatter_description(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    for line in text[3:end].splitlines():
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        return value
    return ""


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
