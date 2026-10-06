"""``.gitignore`` policies for symlink, hybrid, and vendor installs."""

from __future__ import annotations

from pathlib import Path

from spine_cli.constants import (
    COPY_GITIGNORE_ADD,
    COPY_GITIGNORE_REMOVE,
    MKDOCS_GITIGNORE_ENTRY,
    SYMLINK_GITIGNORE_ADD,
    SYMLINK_GITIGNORE_REMOVE,
    VENDOR_GITIGNORE_STRIP,
)
from spine_cli.log import Log


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _write_lines(path: Path, lines: list[str]) -> None:
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8")


def _exact_present(lines: list[str], entry: str) -> bool:
    return any(line == entry for line in lines)


def adjust_install_gitignore(project: Path, copy_mode: bool, log: Log) -> None:
    """Add mode-specific ignores and drop obsolete ones.

    Args:
        project: Consumer project root.
        copy_mode: Hybrid ``--copy`` install versions ``.agents/``.
        log: Progress logger.
    """
    print("\nGitignore:")
    to_add = COPY_GITIGNORE_ADD if copy_mode else SYMLINK_GITIGNORE_ADD
    to_remove = COPY_GITIGNORE_REMOVE if copy_mode else SYMLINK_GITIGNORE_REMOVE
    gitignore = project / ".gitignore"

    if not gitignore.is_file():
        if log.dry_run:
            log.dry("Would create .gitignore with Spine entries")
            return
        lines = [
            "# Spine: .spine is local (symlink); applied IDE trees may be committed",
            *to_add,
        ]
        _write_lines(gitignore, lines)
        log.plus(".gitignore (created with Spine entries)")
        return

    lines = _read_lines(gitignore)
    removed = 0
    kept: list[str] = []
    for line in lines:
        if line in to_remove:
            removed += 1
            if log.dry_run:
                log.dry(f"Would remove ignore entry: {line}")
            else:
                log.plus(f".gitignore: -{line} (versionable in this install mode)")
            continue
        kept.append(line)

    added = 0
    for entry in to_add:
        if _exact_present(kept, entry):
            log.skip(f".gitignore: {entry} (already present)")
            continue
        added += 1
        if log.dry_run:
            log.dry(f"Would add '{entry}' to .gitignore")
        else:
            kept.append(entry)
            log.plus(f".gitignore: +{entry}")

    if not log.dry_run:
        _write_lines(gitignore, kept)
        if added or removed:
            log.info(f"{added} gitignore entries added, {removed} obsolete ignores removed")


def adjust_vendor_gitignore(project: Path, log: Log) -> None:
    """Strip ignores so vendored trees can be committed.

    Args:
        project: Consumer project root.
        log: Progress logger.
    """
    print("\nGitignore (vendor mode — trees are versioned):")
    gitignore = project / ".gitignore"
    if not gitignore.is_file():
        if log.dry_run:
            log.dry("Would create .gitignore with vendor note (no Spine path ignores)")
            return
        gitignore.write_text(
            "# Spine vendor mode: .spine and IDE trees are versioned (do not ignore them)\n",
            encoding="utf-8",
        )
        log.plus(".gitignore (created with vendor note)")
        return

    lines = _read_lines(gitignore)
    kept: list[str] = []
    for line in lines:
        if line in VENDOR_GITIGNORE_STRIP:
            if log.dry_run:
                log.dry(f"Would remove ignore entry: {line}")
            else:
                log.plus(f".gitignore: -{line}")
            continue
        kept.append(line)
    if not log.dry_run:
        _write_lines(gitignore, kept)


def ensure_gitignore_line(project: Path, entry: str, log: Log) -> None:
    """Append ``entry`` to ``.gitignore`` when the exact line is absent.

    Args:
        project: Consumer project root.
        entry: Ignore line.
        log: Progress logger.
    """
    gitignore = project / ".gitignore"
    if log.dry_run:
        log.dry(f"Would add '{entry}' to .gitignore")
        return
    lines = _read_lines(gitignore)
    if _exact_present(lines, entry):
        print(f"    .gitignore already contains '{entry}'")
        return
    lines.append(entry)
    _write_lines(gitignore, lines)
    print(f"    added '{entry}' to .gitignore")


def remove_gitignore_line(project: Path, entry: str, log: Log) -> None:
    """Remove every line equal to ``entry``.

    Args:
        project: Consumer project root.
        entry: Ignore line.
        log: Progress logger.
    """
    gitignore = project / ".gitignore"
    if log.dry_run:
        log.dry(f"Would remove '{entry}' from .gitignore")
        return
    if not gitignore.is_file():
        return
    lines = _read_lines(gitignore)
    if entry not in lines:
        return
    _write_lines(gitignore, [line for line in lines if line != entry])
    print(f"    removed '{entry}' from .gitignore")


def ensure_mkdocs_gitignore(project: Path, log: Log) -> None:
    """Ignore the MkDocs build output.

    Args:
        project: Consumer project root.
        log: Progress logger.
    """
    ensure_gitignore_line(project, MKDOCS_GITIGNORE_ENTRY, log)
