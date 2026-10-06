"""Copy a Spine tree into a consumer project without nested git metadata."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from spine_cli.constants import (
    CANONICAL_SOURCE_FILE,
    COPY_SKIP_ANYWHERE,
    RSYNC_SKIP_ROOT,
    VENDOR_MARKER,
    VENDOR_SKIP_ROOT,
)
from spine_cli.log import Log


def _skip(name: str, at_root: bool, root_only: frozenset[str]) -> bool:
    if name in COPY_SKIP_ANYWHERE:
        return True
    return at_root and name in root_only


def _copy_children(
    src: Path,
    dest: Path,
    *,
    delete: bool,
    root_only: frozenset[str],
    at_root: bool,
) -> None:
    present: set[str] = set()
    for child in src.iterdir():
        if _skip(child.name, at_root, root_only):
            continue
        present.add(child.name)
        target = dest / child.name
        if child.is_symlink():
            if target.is_symlink() or target.exists():
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            target.symlink_to(os.readlink(child))
            continue
        if child.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            _copy_children(
                child,
                target,
                delete=delete,
                root_only=root_only,
                at_root=False,
            )
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(child, target)

    if not delete:
        return
    for existing in list(dest.iterdir()):
        if existing.name in present:
            continue
        if at_root and existing.name in {CANONICAL_SOURCE_FILE, VENDOR_MARKER}:
            continue
        if existing.is_dir() and not existing.is_symlink():
            shutil.rmtree(existing)
        else:
            existing.unlink()


def copy_spine_tree(
    source: Path,
    dest: Path,
    log: Log,
    *,
    delete: bool,
    root_only: frozenset[str],
) -> None:
    """Copy ``source`` into ``dest``, then drop a nested ``.git``.

    Args:
        source: Spine clone to copy from.
        dest: Destination ``.spine`` directory.
        log: Progress logger.
        delete: Remove destination entries that are not in the source.
        root_only: Extra directory names skipped only at the source root.
    """
    if log.dry_run:
        log.dry(f"Would copy {source}/ -> {dest}/")
        return
    if dest.is_symlink():
        dest.unlink()
    dest.mkdir(parents=True, exist_ok=True)
    _copy_children(source, dest, delete=delete, root_only=root_only, at_root=True)
    nested_git = dest / ".git"
    if nested_git.exists() or nested_git.is_symlink():
        if nested_git.is_dir() and not nested_git.is_symlink():
            shutil.rmtree(nested_git)
        else:
            nested_git.unlink()
        log.plus("removed nested .git from .spine/")
    log.plus(f".spine/ copied from {source}")


def copy_vendor_tree(source: Path, dest: Path, log: Log, *, delete: bool) -> None:
    """Vendor-copy Spine, excluding ``docs/`` at the clone root.

    Args:
        source: Upstream Spine clone.
        dest: ``project/.spine``.
        log: Progress logger.
        delete: Prune files removed upstream.
    """
    copy_spine_tree(source, dest, log, delete=delete, root_only=VENDOR_SKIP_ROOT)


def copy_rsync_tree(source: Path, dest: Path, log: Log, *, delete: bool) -> None:
    """Rsync-mode copy. Root ``docs/`` is skipped; ``templates/docs`` is kept.

    Args:
        source: Canonical Spine clone.
        dest: ``project/.spine``.
        log: Progress logger.
        delete: Prune files removed upstream.
    """
    copy_spine_tree(source, dest, log, delete=delete, root_only=RSYNC_SKIP_ROOT)


def write_canonical_source(dest: Path, canonical: Path, log: Log) -> None:
    """Record the clone path used to populate an rsync-mode ``.spine``.

    Args:
        dest: ``project/.spine`` directory.
        canonical: Absolute canonical clone path.
        log: Progress logger.
    """
    marker = dest / CANONICAL_SOURCE_FILE
    if log.dry_run:
        log.dry(f"Would write {marker}")
        return
    marker.write_text(f"{canonical}\n", encoding="utf-8")


def read_canonical_source(spine_dir: Path) -> str:
    """Return the first line of ``.spine-canonical-source``, or empty.

    Args:
        spine_dir: Consumer ``.spine`` directory.

    Returns:
        Recorded path, or ``""`` when the file is missing.
    """
    marker = spine_dir / CANONICAL_SOURCE_FILE
    if not marker.is_file():
        return ""
    line = marker.read_text(encoding="utf-8").splitlines()
    return line[0].strip() if line else ""


def write_vendor_marker(project: Path, source: Path, log: Log) -> None:
    """Write ``.spine-vendor`` with the upstream source path.

    Args:
        project: Consumer project root.
        source: Upstream Spine clone.
        log: Progress logger.
    """
    from datetime import datetime, timezone

    marker = project / VENDOR_MARKER
    if log.dry_run:
        log.dry(f"Would write {marker}")
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    marker.write_text(
        f"mode=vendor\nupdated_at={timestamp}\nsource={source}\n",
        encoding="utf-8",
    )
    log.plus(f".spine-vendor (updated_at={timestamp})")
