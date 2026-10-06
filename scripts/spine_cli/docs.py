"""Seed consumer ``docs/`` from Spine templates without overwriting."""

from __future__ import annotations

from pathlib import Path

from spine_cli.constants import DOCS_GITKEEP_PATHS, DOCS_SEED_DIRS, DOCS_SEED_PATHS
from spine_cli.log import Log


def seed_docs(project: Path, spine: Path, log: Log) -> None:
    """Copy missing memory-bank templates into ``project``.

    Existing files are left untouched. Sample numbered tasks are never seeded.

    Args:
        project: Consumer project root.
        spine: Spine repository root that holds ``templates/docs``.
        log: Progress logger.
    """
    templates = spine / "templates" / "docs"
    print("\nDocs templates:")
    if not templates.is_dir():
        log.warn(f"templates/docs/ not found in {spine}")
        return

    seeded = 0
    skipped = 0
    missing = 0
    for relative in DOCS_SEED_PATHS:
        rel_under_docs = relative.removeprefix("docs/")
        src = templates / rel_under_docs
        dest = project / relative
        if not src.is_file():
            log.warn(f"template missing: templates/docs/{rel_under_docs}")
            missing += 1
            continue
        if dest.is_file():
            log.skip(f"{relative} (already exists, not overwriting)")
            skipped += 1
            continue
        if log.dry_run:
            log.dry(f"Would copy: {relative}")
            seeded += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
        log.plus(f"{relative} (seeded from templates/)")
        seeded += 1

    for relative in DOCS_SEED_DIRS:
        dest = project / relative
        if log.dry_run:
            log.dry(f"Would ensure directory: {relative}")
        else:
            dest.mkdir(parents=True, exist_ok=True)

    for relative in DOCS_GITKEEP_PATHS:
        dest = project / relative
        if dest.is_file():
            log.skip(f"{relative} (already exists)")
            continue
        if log.dry_run:
            log.dry(f"Would create: {relative}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("", encoding="utf-8")
        log.plus(f"{relative} (created)")

    print(
        f"\n  Docs seed: {seeded} copied, {skipped} skipped (existing), "
        f"{missing} template gaps"
    )
