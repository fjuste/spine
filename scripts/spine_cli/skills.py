"""Skill discovery and selection."""

from __future__ import annotations

from pathlib import Path

from spine_cli.constants import CORE_SKILLS


def available_skills(spine: Path) -> list[str]:
    """Return skill directory names that contain ``SKILL.md``.

    Args:
        spine: Spine repository root.

    Returns:
        Sorted skill names.
    """
    skills_dir = spine / "skills"
    if not skills_dir.is_dir():
        return []
    names: list[str] = []
    for child in skills_dir.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            names.append(child.name)
    return sorted(names)


def installed_skills(project: Path) -> list[str]:
    """Return skill names present under ``.agents/skills``.

    Args:
        project: Consumer project root.

    Returns:
        Sorted installed skill names.
    """
    hub = project / ".agents" / "skills"
    if not hub.is_dir():
        return []
    names: list[str] = []
    for child in hub.iterdir():
        if child.is_symlink() or child.is_dir():
            names.append(child.name)
    return sorted(names)


def resolve_skills(spine: Path, skills_arg: str) -> list[str]:
    """Resolve ``all``, ``core``, or a comma-separated skill list.

    Args:
        spine: Spine repository root.
        skills_arg: Selection string. Empty means ``all``.

    Returns:
        Skill names to install, in catalog order for ``all`` and ``core``.
    """
    arg = (skills_arg or "all").strip()
    if arg == "all":
        return available_skills(spine)
    if arg == "core":
        return list(CORE_SKILLS)
    return [part.strip() for part in arg.split(",") if part.strip()]


def markdown_names(directory: Path) -> list[str]:
    """Return sorted ``*.md`` file names in ``directory``.

    Args:
        directory: Directory to scan.

    Returns:
        File names, empty when the directory is missing.
    """
    if not directory.is_dir():
        return []
    return sorted(path.name for path in directory.glob("*.md") if path.is_file())
