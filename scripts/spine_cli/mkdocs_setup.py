"""MkDocs co-install and uninstall. The ``mkdocs`` CLI stays an external process."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from spine_cli.gitignore import ensure_mkdocs_gitignore, remove_gitignore_line
from spine_cli.constants import MKDOCS_GITIGNORE_ENTRY
from spine_cli.log import Log


def _runner(project: Path) -> list[str] | None:
    if shutil.which("uv"):
        return ["uv", "run", "--extra", "docs", "mkdocs"]
    venv_mkdocs = project / ".venv" / "bin" / "mkdocs"
    if venv_mkdocs.is_file() and os_access(venv_mkdocs):
        return [str(venv_mkdocs)]
    if shutil.which("mkdocs"):
        return ["mkdocs"]
    return None


def os_access(path: Path) -> bool:
    """Return True when ``path`` is executable.

    Args:
        path: Candidate binary.

    Returns:
        True when the executable bit is set.
    """
    return path.stat().st_mode & 0o111 != 0


def _seed_templates(project: Path, spine: Path, log: Log) -> None:
    print("  - MkDocs templates")
    source = spine / "templates" / "docs" / "mkdocs"
    dest = project / "docs" / "mkdocs"
    if not source.is_dir():
        print(f"    WARNING: template directory not found: {source}", file=sys.stderr)
        return
    if log.dry_run:
        print(f"    [DRY-RUN] Would seed {dest}")
        return
    dest.mkdir(parents=True, exist_ok=True)
    project_name = project.name
    for template in sorted(source.iterdir()):
        if not template.is_file() or template.name == ".gitkeep":
            continue
        target = dest / template.name
        if target.is_file():
            print(f"    exists, preserving: {target}")
            continue
        text = template.read_text(encoding="utf-8")
        target.write_text(text.replace("PROJECT_NAME_PLACEHOLDER", project_name), encoding="utf-8")
        print(f"    copied: {target}")


def _build(project: Path, log: Log) -> None:
    print("  - MkDocs build")
    command = _runner(project)
    if command is None:
        print("    skipped: mkdocs CLI not available")
        print("    Install: pip install mkdocs")
        return
    args = [*command, "build", "-f", "docs/mkdocs/mkdocs.yml", "--strict"]
    if log.dry_run:
        print(f"    [DRY-RUN] Would run: {' '.join(args)}")
        return
    completed = subprocess.run(args, cwd=project, check=False)
    if completed.returncode == 0:
        print("    build passed (--strict)")
    else:
        print("    WARNING: mkdocs build --strict failed. Docs may have issues.", file=sys.stderr)


def setup_mkdocs(project: Path, spine: Path, log: Log) -> None:
    """Seed MkDocs templates, ignore the site directory, and build.

    Args:
        project: Consumer project root.
        spine: Spine repository root.
        log: Progress logger.
    """
    print("  - MkDocs CLI check")
    if _runner(project) is None:
        print("    WARNING: mkdocs CLI not found.")
        print("    Install:")
        print("      pip install mkdocs")
    _seed_templates(project, spine, log)
    ensure_mkdocs_gitignore(project, log)
    _build(project, log)
    if log.dry_run:
        return
    print("  - Integration verify")
    import spine_validate

    report = spine_validate.validate_mkdocs(project)
    if not report.passed:
        print("    WARNING: mkdocs validation reported issues", file=sys.stderr)


def uninstall_mkdocs(project: Path, log: Log, *, purge: bool) -> None:
    """Remove seeded MkDocs files.

    Args:
        project: Consumer project root.
        log: Progress logger.
        purge: Also remove ``docs/mkdocs/site/``.
    """
    print("MkDocs uninstall:")
    dest = project / "docs" / "mkdocs"
    print("  - MkDocs templates")
    if not dest.is_dir():
        print("    no docs/mkdocs/ directory found")
    else:
        for name in ("mkdocs.yml", "index.md", "architecture.md"):
            target = dest / name
            if not target.is_file():
                continue
            if log.dry_run:
                print(f"    [DRY-RUN] Would remove: {target}")
            else:
                target.unlink()
                print(f"    removed: {target}")
        site = dest / "site"
        if purge:
            print("  - Purge MkDocs output")
            if log.dry_run:
                print(f"    [DRY-RUN] Would remove: {site}/")
            elif site.exists():
                shutil.rmtree(site)
                print(f"    removed: {site}/")
        else:
            print("  - Preserved docs/mkdocs/site/ (use --purge-mkdocs to remove)")
        if not log.dry_run and dest.is_dir() and not any(dest.iterdir()):
            dest.rmdir()
            print(f"    removed empty directory: {dest}")
    remove_gitignore_line(project, MKDOCS_GITIGNORE_ENTRY, log)
