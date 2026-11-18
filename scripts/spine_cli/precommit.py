"""Git pre-commit hook: install or remove the Spine memory check block.

The block runs ``spine_validate.py staged`` and lives between two marker lines
inside ``<git rev-parse --git-path hooks>/pre-commit``, so other hook content
is kept and re-running install is idempotent.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from spine_cli.log import Log

HOOK_NAME = "pre-commit"
BLOCK_START = "# >>> spine pre-commit >>>"
BLOCK_END = "# <<< spine pre-commit <<<"
BLOCK = f"""{BLOCK_START}
if [ -f .spine/scripts/spine_validate.py ]; then
  spine_py=$(command -v python3 || command -v python)
  if [ -n "$spine_py" ]; then
    "$spine_py" .spine/scripts/spine_validate.py staged || exit 1
  else
    echo "spine pre-commit: python not found; memory validation skipped" >&2
  fi
else
  echo "spine pre-commit: .spine not found; memory validation skipped" >&2
fi
{BLOCK_END}
"""
NEW_HOOK_SHEBANG = "#!/bin/sh"
HOOK_MODE = 0o755
SHELL_INTERPRETERS = frozenset({"sh", "bash", "zsh"})
HOOK_MANAGER_MARKERS = ("husky", "pre-commit.com", "lefthook")
MANUAL_LINE = "python3 .spine/scripts/spine_validate.py staged || exit 1"

_BLOCK_RE = re.compile(rf"^{re.escape(BLOCK_START)}\n.*?^{re.escape(BLOCK_END)}[ \t]*(?:\n|\Z)", re.MULTILINE | re.DOTALL)


def hook_path(project: Path) -> Path | None:
    """Return the pre-commit hook file git uses for ``project``.

    Honours ``core.hooksPath`` and linked worktrees via ``git rev-parse --git-path hooks``.

    Args:
        project: Consumer project root.

    Returns:
        The hook path, or None when ``project`` is not inside a git work tree.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-path", "hooks"], cwd=project, capture_output=True, text=True, check=False
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return (project / result.stdout.strip()) / HOOK_NAME


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def hook_installed(project: Path) -> bool:
    """Return True when the Spine block is present in the project's pre-commit hook.

    Args:
        project: Consumer project root.

    Returns:
        True when the hook file holds the marked block.
    """
    path = hook_path(project)
    return path is not None and path.is_file() and _BLOCK_RE.search(_read(path)) is not None


def _is_shell_shebang(first_line: str) -> bool:
    if not first_line.startswith("#!"):
        return False
    words = first_line[2:].split()
    if not words:
        return False
    interpreter = Path(words[0]).name
    if interpreter == "env" and len(words) > 1:
        interpreter = Path(words[1]).name
    return interpreter in SHELL_INTERPRETERS


def _is_managed(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in HOOK_MANAGER_MARKERS)


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", errors="surrogateescape")


def install_hook(project: Path, log: Log) -> bool:
    """Install or refresh the Spine block in the pre-commit hook.

    New hook → ``#!/bin/sh`` plus the block, mode 0755. Existing sh/bash/zsh
    hook → block inserted right after the shebang. Existing block → replaced in
    place. Any other hook (no shebang, other interpreter, hook managers) is left
    untouched and a NOTE names the line to add by hand.

    Args:
        project: Consumer project root.
        log: Installer log (``log.dry_run`` previews without writing).

    Returns:
        True when the block is (or would be) in place.
    """
    path = hook_path(project)
    if path is None:
        log.warn("pre-commit memory check skipped: not a git work tree")
        return False
    if not path.is_file():
        if log.dry_run:
            log.dry(f"Would create {path} with the spine pre-commit block")
            return True
        path.parent.mkdir(parents=True, exist_ok=True)
        _write(path, f"{NEW_HOOK_SHEBANG}\n{BLOCK}")
        path.chmod(HOOK_MODE)
        log.plus(f"pre-commit memory check: {path}")
        return True

    text = _read(path)
    if _BLOCK_RE.search(text):
        updated = _BLOCK_RE.sub(lambda _match: BLOCK, text, count=1)
        if updated == text:
            log.skip(f"pre-commit memory check: {path}")
            return True
        action = "refreshed"
    else:
        first_line, _, rest = text.partition("\n")
        if not _is_shell_shebang(first_line) or _is_managed(text):
            print(f"  NOTE: {path} is not a plain sh/bash/zsh hook; left untouched.")
            print(f"        Add this line to it (or to your hook manager): {MANUAL_LINE}")
            return False
        updated = f"{first_line}\n{BLOCK}{rest}"
        action = "added to existing hook"
    if log.dry_run:
        log.dry(f"Would update {path} (spine pre-commit block {action})")
        return True
    _write(path, updated)
    log.plus(f"pre-commit memory check {action}: {path}")
    return True


def uninstall_hook(project: Path, log: Log) -> None:
    """Remove the Spine block from the pre-commit hook; delete the file when nothing else remains.

    Args:
        project: Consumer project root.
        log: Installer log (``log.dry_run`` previews without writing).
    """
    path = hook_path(project)
    if path is None or not path.is_file() or not _BLOCK_RE.search(_read(path)):
        log.skip("pre-commit memory check not installed")
        return
    remaining = _BLOCK_RE.sub("", _read(path), count=1)
    leftover = [line for line in remaining.splitlines() if line.strip()]
    empty = not leftover or (len(leftover) == 1 and leftover[0].startswith("#!"))
    if log.dry_run:
        log.dry(f"Would {'delete' if empty else 'remove the spine block from'} {path}")
        return
    if empty:
        path.unlink()
        log.plus(f"removed pre-commit hook: {path}")
    else:
        _write(path, remaining)
        log.plus(f"removed spine pre-commit block: {path}")
