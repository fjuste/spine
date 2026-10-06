"""CLI options shared by installer subcommands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from spine_cli.constants import DEFAULT_TARGETS


@dataclass
class Options:
    """Flags for install, update, vendor, and uninstall.

    Args:
        project_root: Consumer project. None resolves via git.
        spine_dir: Spine clone. None uses the repo that contains spine.py.
        copy_mode: Hybrid install: physical IDE files, ``.spine`` stays a symlink.
        rsync_mode: Populate ``.spine`` as a real directory.
        force: Replace conflicts and convert modes.
        dry_run: Preview without writing.
        update_mode: Reconcile wiring and drop dangling links.
        skills: ``all``, ``core``, or a comma-separated list.
        add_skill: Install one skill and return.
        remove_skill: Remove one skill and return.
        list_skills: Print the skill catalog and return.
        targets: Comma-separated IDE targets.
        with_graphify: Run Graphify co-install.
        graphify_init: Build the graph during Graphify setup.
        graphify_hooks: Install the Graphify git hook.
        graphify_uninstall: Remove Graphify platform artifacts only.
        purge_graphify: Also remove ``graphify-out/`` and ``.graphifyignore``.
        no_graphify_prompt: Do not ask on a TTY.
        with_mkdocs: Run MkDocs setup.
        mkdocs_uninstall: Remove MkDocs templates only.
        purge_mkdocs: Also remove ``docs/mkdocs/site/``.
        no_mkdocs_prompt: Do not ask on a TTY.
        no_pull: Skip ``git pull`` during update.
        replace_opencode: Replace ``opencode.json`` instead of merging.
        global_mode: Rejected v1.3 flag.
        project_mode: Rejected v1.3 flag.
    """

    project_root: Path | None = None
    spine_dir: Path | None = None
    copy_mode: bool = False
    rsync_mode: bool = False
    force: bool = False
    dry_run: bool = False
    update_mode: bool = False
    skills: str = "all"
    add_skill: str = ""
    remove_skill: str = ""
    list_skills: bool = False
    targets: str = DEFAULT_TARGETS
    with_graphify: bool = False
    graphify_init: bool = False
    graphify_hooks: bool = False
    graphify_uninstall: bool = False
    purge_graphify: bool = False
    no_graphify_prompt: bool = False
    with_mkdocs: bool = False
    mkdocs_uninstall: bool = False
    purge_mkdocs: bool = False
    no_mkdocs_prompt: bool = False
    no_pull: bool = False
    replace_opencode: bool = False
    global_mode: bool = False
    project_mode: bool = False
