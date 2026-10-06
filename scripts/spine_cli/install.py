"""Symlink and rsync install orchestration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from spine_cli import docs as docs_seed
from spine_cli import graphify_setup, mkdocs_setup
from spine_cli.gitignore import adjust_install_gitignore
from spine_cli.log import Log, SpineExit, die
from spine_cli.opencode_merge import merge_project_opencode
from spine_cli.options import Options
from spine_cli.paths import (
    is_spine_root,
    package_spine_root,
    resolve_project_root,
    resolve_spine_dir,
    same_path,
)
from spine_cli.skills import resolve_skills
from spine_cli.vendor_copy import copy_rsync_tree, write_canonical_source
from spine_cli.wiring import (
    add_one_skill,
    cleanup_dangling,
    install_selected_targets,
    install_skills,
    list_skills,
    parse_targets,
    publish_workflow_skills,
    remove_one_skill,
)


def _reject_removed_flags(options: Options) -> None:
    if options.global_mode or options.project_mode:
        die(
            "--global and --project were removed in v1.3.0.\n"
            "       Install is project-only. "
            "Run: python3 /path/to/spine/scripts/spine.py install"
        )


def _install_side_command(options: Options) -> bool:
    """Return True for install flags that are not a full project install."""
    return bool(
        options.list_skills
        or options.add_skill
        or options.remove_skill
        or options.graphify_uninstall
        or options.mkdocs_uninstall
    )


def windows_install_uses_vendor(options: Options) -> bool:
    """Return True when ``install`` should copy a vendored tree.

    Windows has no reliable symlink privilege, so a plain ``install`` uses
    vendor mode. Linux and macOS stay on symlink wiring unless the user
    runs the ``vendor`` subcommand.

    Args:
        options: Parsed install flags.

    Returns:
        True on Windows for a full install.
    """
    if sys.platform != "win32":
        return False
    return not _install_side_command(options)


def _run_windows_vendor_install(options: Options) -> int:
    """Run vendor install for a Windows ``install`` invocation.

    Args:
        options: Parsed flags. ``--spine-dir`` defaults to this Spine clone.

    Returns:
        Process exit code from ``run_vendor``.
    """
    if options.copy_mode or options.rsync_mode:
        die(
            "On Windows, install uses vendor mode (real files, no symlinks).\n"
            "       Omit --copy and --rsync."
        )
    if options.spine_dir is None:
        options.spine_dir = package_spine_root()
    print("Windows detected: install uses vendor mode.")
    if options.with_graphify or options.with_mkdocs or options.graphify_hooks:
        print("Graphify and MkDocs are not co-installed by vendor mode.")
    return run_vendor(options)


def _prompt_yes(question: str) -> bool:
    while True:
        try:
            response = input(question).strip().lower()
        except EOFError:
            return False
        if response in {"y", "yes", ""}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _maybe_prompt_graphify(project: Path, options: Options) -> None:
    if options.no_graphify_prompt or options.with_graphify or options.dry_run:
        return
    if options.list_skills or options.add_skill or options.remove_skill:
        return
    if not sys.stdin.isatty():
        return
    import spine_validate

    quiet = spine_validate.Report(quiet=True)
    if spine_validate.validate_graphify(project, "cursor,opencode,claude", quiet).passed:
        print("\nGraphify: integration complete (graph + Cursor/OpenCode/Claude). Skipping opt-in prompt.")
        return
    graph_exists = (project / "graphify-out" / "graph.json").is_file()
    title = "Complete Graphify integration?" if graph_exists else "Optional: Graphify"
    question = (
        "Complete Graphify integration for this project? [Y/n]: "
        if graph_exists
        else "Enable Graphify for this project? [Y/n]: "
    )
    print(f"\n===========================================\n  {title}\n===========================================\n")
    print("Graphify is an optional code-structure layer (Spine owns docs/memory; Graphify maps source).")
    print("Recommended for medium/large codebases. The memory bank remains the source of truth.\n")
    if _prompt_yes(question):
        options.with_graphify = True
        options.graphify_init = True
        print("\nGraphify: enabled (graph build + tri-platform co-install)")
    else:
        print("\nGraphify: skipped. Re-run with --with-graphify")


def _maybe_prompt_mkdocs(options: Options) -> None:
    if options.no_mkdocs_prompt or options.with_mkdocs or options.dry_run:
        return
    if options.list_skills or options.add_skill or options.remove_skill:
        return
    if not sys.stdin.isatty():
        return
    print("\n===========================================\n  Optional: MkDocs\n===========================================\n")
    print("MkDocs is the public-facing layer. The memory bank remains the source of truth.\n")
    if _prompt_yes("Enable MkDocs for this project? [Y/n]: "):
        options.with_mkdocs = True
        print("\nMkDocs: enabled (template seed + initial build)")
    else:
        print("\nMkDocs: skipped. Re-run with --with-mkdocs")


def _link_spine(project: Path, spine: Path, log: Log, *, force: bool) -> None:
    link = project / ".spine"
    if link.is_symlink():
        current = os.readlink(link)
        resolved = (link.parent / current).resolve() if not current.startswith("/") else Path(current).resolve()
        if same_path(resolved, spine):
            log.skip(f".spine symlink (already linked to {spine})")
            return
        if not force:
            die(f".spine points to {current}, expected {spine}. Use --force to replace.", code=2)
        if log.dry_run:
            log.dry(f"Would replace .spine symlink: {current} -> {spine}")
            return
        link.unlink()
    elif link.is_dir():
        return
    elif link.exists():
        die(f"{link} exists and is not a symlink. Remove it and re-run.", code=3)
    else:
        if log.dry_run:
            log.dry(f"Would link: {link} -> {spine}")
            return
        try:
            link.symlink_to(spine)
        except OSError as exc:
            die(f"Cannot create symlink {link} ({exc}). Use: python3 scripts/spine.py vendor")
        log.plus(f".spine -> {spine}")
        return

    if not log.dry_run:
        try:
            link.symlink_to(spine)
        except OSError as exc:
            die(f"Cannot create symlink {link} ({exc}). Use: python3 scripts/spine.py vendor")
        log.plus(f".spine (replaced) -> {spine}")


def _populate_rsync(project: Path, spine: Path, log: Log, *, force: bool) -> Path:
    dest = project / ".spine"
    if dest.is_symlink():
        if not force:
            die(
                ".spine is a symlink (symlink mode). "
                "Re-run with --force to replace with rsync mode.",
                code=3,
            )
        if not log.dry_run:
            dest.unlink()
            log.warn(".spine symlink removed")
    elif dest.is_dir():
        if not force:
            die(
                ".spine already exists as a real directory. "
                "Re-run with --force to replace.",
                code=3,
            )
    elif dest.exists():
        die(f"{dest} exists and is not a symlink or directory.", code=3)

    print("\nRsync .spine/ from canonical clone:")
    copy_rsync_tree(spine, dest, log, delete=True)
    write_canonical_source(dest, spine, log)
    return dest


def ensure_layout(project: Path, spine: Path, options: Options, log: Log) -> Path:
    """Create ``.spine`` when missing and return the tree wiring should read.

    Args:
        project: Consumer project root.
        spine: Spine clone that contains this installer.
        options: Install flags.
        log: Progress logger.

    Returns:
        Directory whose ``rules/``, ``skills/``, and ``commands/`` are wired.
    """
    if options.copy_mode and options.rsync_mode:
        die("--copy and --rsync cannot be combined.")

    link = project / ".spine"
    if options.rsync_mode:
        content = _populate_rsync(project, spine, log, force=options.force)
        if not log.dry_run and not is_spine_root(content):
            die(f".spine is missing rules/, skills/, or commands/ in {content}")
        return spine if log.dry_run else content

    if link.is_dir() and not link.is_symlink() and options.copy_mode:
        die(
            "--copy requires .spine to be a symlink (not a real directory).\n"
            "       For a fully vendored tree use: python3 scripts/spine.py vendor"
        )

    if not link.exists() and not link.is_symlink():
        _link_spine(project, spine, log, force=options.force)
    elif link.is_symlink():
        _link_spine(project, spine, log, force=options.force)
    elif link.is_dir():
        log.skip(".spine (rsync mode) OK")

    content = link if link.is_dir() else spine
    if not log.dry_run and link.exists() and not is_spine_root(content):
        die(".spine is missing rules/, skills/, or commands/")
    return content


def run_install(options: Options) -> int:
    """Install Spine into a consumer project.

    ``install --update`` reconciles wiring. It does not ``git pull``.

    Args:
        options: Parsed flags.

    Returns:
        Process exit code.
    """
    log = Log(dry_run=options.dry_run)
    try:
        _reject_removed_flags(options)
        if windows_install_uses_vendor(options):
            return _run_windows_vendor_install(options)
        project = resolve_project_root(
            str(options.project_root) if options.project_root else None
        )
        spine = resolve_spine_dir(str(options.spine_dir) if options.spine_dir else None)
        if options.list_skills:
            list_skills(project, spine)
            return 0
        if options.remove_skill:
            remove_one_skill(project, options.remove_skill, log)
            return 1 if log.warnings else 0
        if options.add_skill:
            existing = project / ".spine"
            if existing.is_dir():
                skill_source = existing
            else:
                skill_source = ensure_layout(project, spine, options, log)
            add_one_skill(
                project,
                skill_source,
                options.add_skill,
                log,
                copy_mode=options.copy_mode,
                force=options.force,
            )
            return 0
        if options.graphify_uninstall:
            content = ensure_layout(project, spine, options, log)
            graphify_setup.uninstall_graphify(
                project,
                log,
                targets=options.targets,
                purge=options.purge_graphify,
            )
            del content
            return 0
        if options.mkdocs_uninstall:
            ensure_layout(project, spine, options, log)
            mkdocs_setup.uninstall_mkdocs(project, log, purge=options.purge_mkdocs)
            return 0

        content = ensure_layout(project, spine, options, log)

        print("Spine Project Installer")
        print(f"Repository: {spine}")
        print(f"Project:    {project}")
        print(f"Targets:    {options.targets}")
        if options.force:
            print("Mode: force (will replace existing symlinks/copies)")
        if options.update_mode:
            print("Mode: update (install + cleanup dangling)")
        if options.copy_mode:
            print("Mode: copy (physical files; .spine stays symlink)")
        if options.rsync_mode:
            print("Mode: rsync (real .spine directory, relative IDE symlinks)")
        if options.dry_run:
            print("Mode: dry-run (preview only)")

        skill_names = resolve_skills(content if content.is_dir() else spine, options.skills)
        print("\nSkills to install:")
        for name in skill_names:
            print(f"  - {name}")

        install_skills(
            project,
            content,
            skill_names,
            log,
            copy_mode=options.copy_mode,
            force=options.force or options.update_mode,
            update_mode=options.update_mode,
        )
        publish_workflow_skills(
            project,
            content,
            parse_targets(options.targets),
            log,
            copy_mode=options.copy_mode,
            force=options.force or options.update_mode,
        )
        install_selected_targets(
            project,
            content,
            parse_targets(options.targets),
            log,
            copy_mode=options.copy_mode,
            force=options.force or options.update_mode,
        )
        docs_seed.seed_docs(project, content if (content / "templates").is_dir() else spine, log)
        merge_project_opencode(
            content if (content / "templates" / "opencode.json").is_file() else spine,
            project,
            log,
        )
        adjust_install_gitignore(project, options.copy_mode, log)

        _maybe_prompt_graphify(project, options)
        if options.with_graphify or options.graphify_init:
            graphify_setup.setup_graphify(
                project,
                spine,
                log,
                targets=options.targets,
                init_graph=options.graphify_init or options.with_graphify,
                hooks=options.graphify_hooks,
            )
        _maybe_prompt_mkdocs(options)
        if options.with_mkdocs:
            mkdocs_setup.setup_mkdocs(project, spine, log)

        if options.update_mode:
            cleanup_dangling(project, log)

        print("\n===========================================")
        print("  Spine Project Install Summary")
        print("===========================================")
        print(f"\n  Conflicts: {log.conflicts}")
        print(f"  Warnings : {log.warnings}")
        if log.conflicts:
            print(f"\n{log.conflicts} conflict(s) detected.")
            print("  Use --force to replace conflicting targets.")
        if options.dry_run:
            print("\nThis was a dry run. No changes were made.")
        print("\nNext step (IDE): /spine-bootstrap")
    except SpineExit as exc:
        return exc.code
    return 0


def _symlink_mode_detected(project: Path) -> bool:
    spine = project / ".spine"
    if spine.is_symlink():
        return True
    if (project / ".spine-vendor").is_file():
        return False
    skills = project / ".agents" / "skills"
    if skills.is_dir() and any(child.is_symlink() for child in skills.iterdir()):
        return True
    return any(
        (project / relative).is_symlink()
        for relative in (".cursor/skills", ".claude/skills")
    )


def _drop_symlink_hubs(project: Path, log: Log) -> None:
    spine = project / ".spine"
    if spine.is_symlink() and not log.dry_run:
        spine.unlink()
        log.plus("removed symlink: .spine")
    for relative in (".cursor/skills", ".claude/skills"):
        path = project / relative
        if path.is_symlink() and not log.dry_run:
            path.unlink()
            log.plus(f"removed symlink: {relative}")
    skills = project / ".agents" / "skills"
    if skills.is_dir():
        for child in list(skills.iterdir()):
            if child.is_symlink() and not log.dry_run:
                child.unlink()


def run_vendor(options: Options) -> int:
    """Copy Spine into the project and materialize IDE trees as real files.

    Args:
        options: Parsed flags. ``--update`` requires ``--spine-dir``.

    Returns:
        Process exit code. ``3`` when symlink mode is refused without ``--force``.
    """
    from spine_cli.uninstall import run_uninstall
    from spine_cli.gitignore import adjust_vendor_gitignore
    from spine_cli.vendor_copy import copy_vendor_tree, write_vendor_marker

    log = Log(dry_run=options.dry_run)
    try:
        project = resolve_project_root(
            str(options.project_root) if options.project_root else None
        )
        if options.update_mode and options.spine_dir is None:
            die(
                "--update requires --spine-dir=PATH "
                "(source must differ from vendored .spine)."
            )

        source = (
            resolve_spine_dir(str(options.spine_dir))
            if options.spine_dir is not None
            else None
        )
        dest = project / ".spine"
        if source is None and dest.is_symlink():
            raw = os.readlink(dest)
            guessed = Path(raw) if raw.startswith("/") else (dest.parent / raw).resolve()
            if is_spine_root(guessed):
                source = guessed
                log.info(f"Using symlink target as --spine-dir: {source}")
        if source is None:
            source = resolve_spine_dir(None)

        if dest.is_dir() and not dest.is_symlink() and same_path(dest, source):
            die(
                f"--spine-dir points at the project's vendored .spine ({dest}).\n"
                "       Pass the upstream Spine clone path."
            )
        if _symlink_mode_detected(project):
            if not options.force:
                die(
                    f"Symlink-mode Spine detected in {project}\n"
                    "       .spine is a symlink or IDE paths contain symlinks.\n"
                    "       Vendor install refuses to mix modes.\n"
                    "       Re-run with --force to convert to vendor mode.",
                    code=3,
                )
            _drop_symlink_hubs(project, log)

        print("Spine Vendor Installer")
        print(f"Source:  {source}")
        print(f"Project: {project}")
        delete = options.update_mode or (dest.exists() and not dest.is_symlink())
        copy_vendor_tree(source, dest, log, delete=delete)
        content = source if log.dry_run or not dest.is_dir() else dest
        skill_names = resolve_skills(source, options.skills)
        install_skills(
            project,
            content,
            skill_names,
            log,
            copy_mode=True,
            force=True,
            update_mode=options.update_mode,
        )
        publish_workflow_skills(
            project,
            content,
            parse_targets(options.targets),
            log,
            copy_mode=True,
            force=True,
        )
        install_selected_targets(
            project,
            content,
            parse_targets(options.targets),
            log,
            copy_mode=True,
            force=True,
        )
        docs_seed.seed_docs(project, source, log)
        merge_project_opencode(source, project, log)
        adjust_vendor_gitignore(project, log)
        write_vendor_marker(project, source, log)
        print("\nVendor install complete. .spine-vendor written.")
    except SpineExit as exc:
        return exc.code
    return 0


def run_install_uninstall(options: Options) -> int:
    """Remove applied artefacts and keep ``.spine`` unless vendor mode is active.

    Args:
        options: Parsed flags.

    Returns:
        Process exit code.
    """
    from spine_cli.uninstall import run_uninstall

    return run_uninstall(options)
