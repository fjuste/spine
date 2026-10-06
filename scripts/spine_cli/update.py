"""Update a symlink or rsync consumer. Vendor projects must use ``vendor --update``."""

from __future__ import annotations

import os
import subprocess
from dataclasses import replace
from pathlib import Path

from spine_cli.constants import CANONICAL_SOURCE_FILE, VENDOR_MARKER
from spine_cli.install import run_install
from spine_cli.log import Log, SpineExit, die
from spine_cli.opencode_merge import merge_project_opencode, replace_project_opencode
from spine_cli.options import Options
from spine_cli.paths import resolve_project_root
from spine_cli.vendor_copy import copy_rsync_tree, read_canonical_source, write_canonical_source


def _git_pull(repo: Path, log: Log) -> None:
    if log.dry_run:
        log.dry(f'Would run: git -C "{repo}" pull')
        return
    completed = subprocess.run(["git", "-C", str(repo), "pull"], check=False)
    if completed.returncode != 0:
        die(f"git pull failed in {repo}")


def _canonical(spine_dir: Path) -> Path:
    recorded = read_canonical_source(spine_dir)
    env_path = os.environ.get("SPINE_CANONICAL_PATH", "").strip()
    raw = recorded or env_path
    if not raw:
        die(
            "Cannot resolve canonical Spine path for rsync mode.\n"
            "       Recorded in .spine/.spine-canonical-source or set SPINE_CANONICAL_PATH."
        )
    path = Path(os.path.expanduser(raw))
    if not path.is_dir():
        die(f"Canonical Spine path is not a directory: {path}")
    return path.resolve()


def run_update(options: Options) -> int:
    """Pull Spine and reconcile wiring.

    This is not ``install --update``. The pull happens here; wiring is an
    ``install --update --force`` pass afterwards.

    Args:
        options: Parsed flags.

    Returns:
        Process exit code.
    """
    log = Log(dry_run=options.dry_run)
    try:
        project = resolve_project_root(
            str(options.project_root) if options.project_root else None
        )
        if (project / VENDOR_MARKER).is_file():
            die(
                "Vendor mode detected (.spine-vendor).\n"
                "       Use: python3 scripts/spine.py vendor --update --spine-dir=PATH"
            )
        spine_path = project / ".spine"
        if spine_path.is_symlink():
            mode = "symlink"
            spine_dir = spine_path.resolve()
            canonical: Path | None = None
        elif spine_path.is_dir():
            mode = "rsync"
            spine_dir = spine_path.resolve()
            canonical = _canonical(spine_dir)
        else:
            die(
                f".spine not found in project root: {project}\n"
                "       Run: python3 /path/to/spine/scripts/spine.py install"
            )

        print("Spine Project Updater")
        print(f"Project: {project}")
        print(f"Mode:    {mode}")
        print(f"Spine:   {spine_dir}")

        if not options.no_pull:
            if mode == "symlink":
                print("Step 1/4: Update Spine repository (git pull via symlink)")
                _git_pull(spine_dir, log)
            else:
                print("Step 1/4: Update canonical Spine + sync .spine/")
                assert canonical is not None
                _git_pull(canonical, log)
                copy_rsync_tree(canonical, spine_path, log, delete=True)
                write_canonical_source(spine_path, canonical, log)
                if (spine_path / CANONICAL_SOURCE_FILE).is_file() or log.dry_run:
                    print(f"  Canonical: {canonical}")
        else:
            print("Step 1/4: Skipped Spine pull (--no-pull)")

        print("\nStep 2/4: Reconcile project symlinks")
        install_options = replace(
            options,
            project_root=project,
            spine_dir=spine_dir,
            update_mode=True,
            force=True,
            rsync_mode=False,
            copy_mode=False,
            no_pull=True,
        )
        code = run_install(install_options)
        if code != 0:
            return code

        print("\nStep 3/4: Sync opencode.json")
        template_root = canonical if mode == "rsync" and canonical is not None else spine_dir
        if options.replace_opencode:
            replace_project_opencode(template_root, project, log)
        else:
            merge_project_opencode(template_root, project, log)

        print("\nStep 4/4: Memory bank")
        if (project / "docs" / "memory").is_dir():
            print("  docs/memory/ present (install seeds missing templates without overwriting)")
        else:
            print("  Note: docs/memory/ still missing — run: python3 .spine/scripts/spine.py install --update")
        print("\nUpdate complete.")
    except SpineExit as exc:
        return exc.code
    return 0
