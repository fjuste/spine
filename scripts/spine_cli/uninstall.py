"""Remove Spine artefacts. Vendor mode drops ``.spine``; symlink mode keeps it."""

from __future__ import annotations

import shutil
from pathlib import Path

from spine_cli.constants import VENDOR_MARKER
from spine_cli.log import Log, SpineExit, die
from spine_cli.options import Options
from spine_cli.paths import resolve_project_root


def _remove(path: Path, log: Log) -> None:
    if not path.exists() and not path.is_symlink():
        return
    label = path.name
    if log.dry_run:
        log.dry(f"Would remove: {path}")
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()
    log.plus(f"removed: {label}")


def _clean_children(directory: Path, log: Log) -> None:
    if not directory.is_dir():
        return
    for child in list(directory.iterdir()):
        _remove(child, log)


def uninstall_applied(project: Path, log: Log, *, remove_spine: bool) -> None:
    """Remove IDE wiring, including ``/spine-*`` skill bundles under ``.agents/skills``.

    ``docs/`` and ``opencode.json`` are kept. Legacy ``.agents/workflows`` files
    are removed with that directory.

    Args:
        project: Consumer project root.
        log: Progress logger.
        remove_spine: When True, also remove ``.spine`` and ``.spine-vendor``.
    """
    print("Spine uninstall")
    print(f"Project: {project}\n")
    for relative in (
        ".agents/skills",
        ".agents/rules",
        ".agents/workflows",
        ".cursor/rules",
        ".cursor/commands",
        ".opencode/commands",
        ".opencode/agents",
    ):
        _clean_children(project / relative, log)

    for relative in (
        ".cursor/skills",
        ".claude/skills",
        ".agents/skills",
        ".agents/rules",
        ".agents/workflows",
    ):
        _remove(project / relative, log)

    for relative in (
        ".cursor/rules",
        ".cursor/commands",
        ".opencode/commands",
        ".opencode/agents",
        ".cursor",
        ".claude",
        ".opencode",
        ".agents",
    ):
        path = project / relative
        if path.is_symlink():
            _remove(path, log)
        elif path.is_dir() and not any(path.iterdir()):
            _remove(path, log)

    if remove_spine:
        _remove(project / ".spine", log)
        _remove(project / VENDOR_MARKER, log)
    else:
        spine = project / ".spine"
        if spine.is_symlink() or spine.is_dir():
            log.skip(".spine kept")
        marker = project / VENDOR_MARKER
        if marker.is_file():
            _remove(marker, log)

    print("\n  Note: docs/ and opencode.json were NOT removed.")


def _vendor_detected(project: Path) -> bool:
    return (project / VENDOR_MARKER).is_file()


def run_uninstall(options: Options, *, vendor_only: bool = False) -> int:
    """Uninstall, choosing vendor teardown when ``.spine-vendor`` exists.

    Args:
        options: Parsed flags. ``project_root`` may be None.
        vendor_only: Refuse a symlink ``.spine`` instead of keeping it.

    Returns:
        Process exit code.
    """
    log = Log(dry_run=options.dry_run)
    try:
        project = resolve_project_root(
            str(options.project_root) if options.project_root else None
        )
        spine = project / ".spine"
        if vendor_only and spine.is_symlink():
            die(
                ".spine is a symlink (symlink mode).\n"
                "       Use: python3 .spine/scripts/spine.py uninstall"
            )
        remove_spine = vendor_only or _vendor_detected(project)
        uninstall_applied(project, log, remove_spine=remove_spine)
    except SpineExit as exc:
        return exc.code
    return 0
