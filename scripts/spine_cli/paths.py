"""Project and Spine repository path resolution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from spine_cli.log import die


def package_spine_root() -> Path:
    """Return the Spine clone that contains this package.

    Returns:
        Absolute path of the repository root (parent of ``scripts/``).
    """
    return Path(__file__).resolve().parents[2]


def is_spine_root(path: Path) -> bool:
    """Return True when ``path`` has rules, skills, and commands.

    Args:
        path: Candidate Spine repository root.

    Returns:
        True when the three required directories exist.
    """
    return (
        (path / "rules").is_dir()
        and (path / "skills").is_dir()
        and (path / "commands").is_dir()
    )


def expand_user_path(raw: str) -> Path:
    """Expand ``~`` and return a path without requiring it to exist.

    Args:
        raw: User-supplied path string.

    Returns:
        Expanded path.
    """
    return Path(os.path.expanduser(raw))


def resolve_spine_dir(explicit: str | None) -> Path:
    """Resolve the Spine clone used as install source.

    Args:
        explicit: ``--spine-dir`` value, or None for this package's repo.

    Returns:
        Absolute Spine root.

    Raises:
        SpineExit: When the path is missing or is not a Spine root.
    """
    if explicit:
        candidate = expand_user_path(explicit)
        if not candidate.is_dir():
            die(f"--spine-dir not found: {explicit}")
        spine = candidate.resolve()
    else:
        spine = package_spine_root()
    if not is_spine_root(spine):
        die(f"Cannot find rules/, skills/, or commands/ in {spine}")
    return spine


def resolve_project_root(explicit: str | None) -> Path:
    """Resolve the consumer project root.

    Args:
        explicit: ``--project-root`` value, or None to use ``git`` toplevel.

    Returns:
        Absolute project root.

    Raises:
        SpineExit: When the path is missing or cwd is not a git checkout.
    """
    if explicit:
        candidate = expand_user_path(explicit)
        if not candidate.is_dir():
            die(f"--project-root not found: {explicit}")
        return candidate.resolve()

    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    root = result.stdout.strip()
    if result.returncode != 0 or not root:
        die(
            "Not inside a git repository.\n"
            "       Run from your consumer project root or pass --project-root=PATH."
        )
    return Path(root).resolve()


def same_path(left: Path, right: Path) -> bool:
    """Return True when two paths refer to the same location.

    Args:
        left: First path.
        right: Second path.

    Returns:
        True when both exist and resolve equal, or their absolute forms match.
    """
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left.absolute() == right.absolute()
