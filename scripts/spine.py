#!/usr/bin/env python3
"""Spine installer (cross-platform, standard library only).

Usage (from a consumer project, or pass ``--project-root``)::

    python3 /path/to/spine/scripts/spine.py install
    python3 /path/to/spine/scripts/spine.py vendor --project-root=.
    python3 .spine/scripts/spine.py update
    python3 .spine/scripts/spine.py uninstall

``update`` pulls the Spine clone and then reconciles wiring.
``install --update`` only reconciles wiring; it does not run ``git pull``.
``vendor --update`` refreshes a vendored tree and requires ``--spine-dir``.

On Windows, ``install`` uses vendor mode (real files). On Linux and macOS,
``install`` keeps symlink wiring; vendor mode runs only via the ``vendor``
subcommand. Use ``py -3`` or ``python`` when ``python3`` is not on PATH.
Python 3.9+.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from spine_cli.constants import DEFAULT_TARGETS
from spine_cli.install import run_install, run_vendor
from spine_cli.options import Options
from spine_cli.uninstall import run_uninstall
from spine_cli.update import run_update


class _Parser(argparse.ArgumentParser):
    """Argument parser that exits 1 on usage errors, matching the old shell scripts."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)


def _add_project_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=None, help="Consumer project root")
    parser.add_argument("--spine-dir", default=None, help="Spine repository root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")


def _options_from(args: argparse.Namespace) -> Options:
    skills = args.skills if getattr(args, "skills", None) else "all"
    if getattr(args, "core", False) and not getattr(args, "skills", None):
        skills = "core"
    with_graphify = bool(getattr(args, "with_graphify", False) or getattr(args, "graphify_init", False))
    return Options(
        project_root=Path(args.project_root) if getattr(args, "project_root", None) else None,
        spine_dir=Path(args.spine_dir) if getattr(args, "spine_dir", None) else None,
        copy_mode=bool(getattr(args, "copy", False)),
        rsync_mode=bool(getattr(args, "rsync", False)),
        force=bool(args.force),
        dry_run=bool(args.dry_run),
        update_mode=bool(getattr(args, "update", False)),
        skills=skills,
        add_skill=getattr(args, "add_skill", "") or "",
        remove_skill=getattr(args, "remove_skill", "") or "",
        list_skills=bool(getattr(args, "list_skills", False)),
        targets=getattr(args, "targets", None) or DEFAULT_TARGETS,
        with_graphify=with_graphify,
        graphify_init=with_graphify,
        graphify_hooks=bool(getattr(args, "graphify_hooks", False)),
        graphify_uninstall=bool(getattr(args, "graphify_uninstall", False)),
        purge_graphify=bool(getattr(args, "purge_graphify", False)),
        no_graphify_prompt=bool(getattr(args, "no_graphify_prompt", False)),
        with_mkdocs=bool(getattr(args, "with_mkdocs", False)),
        mkdocs_uninstall=bool(getattr(args, "mkdocs_uninstall", False)),
        purge_mkdocs=bool(getattr(args, "purge_mkdocs", False)),
        no_mkdocs_prompt=bool(getattr(args, "no_mkdocs_prompt", False)),
        no_pull=bool(getattr(args, "no_pull", False)),
        replace_opencode=bool(getattr(args, "replace_opencode", False)),
        global_mode=bool(getattr(args, "global_mode", False)),
        project_mode=bool(getattr(args, "project_mode", False)),
    )


def _cmd_install(args: argparse.Namespace) -> int:
    options = _options_from(args)
    if args.uninstall:
        return run_uninstall(options)
    return run_install(options)


def _cmd_vendor(args: argparse.Namespace) -> int:
    options = _options_from(args)
    if args.uninstall:
        return run_uninstall(options, vendor_only=True)
    return run_vendor(options)


def _cmd_update(args: argparse.Namespace) -> int:
    return run_update(_options_from(args))


def _cmd_uninstall(args: argparse.Namespace) -> int:
    return run_uninstall(_options_from(args))


def build_parser() -> argparse.ArgumentParser:
    """Build the spine.py argument parser.

    Returns:
        Configured parser.
    """
    parser = _Parser(prog="spine.py", description="Spine project installer")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Link .spine and wire IDE trees")
    _add_project_flags(install)
    install.add_argument("--copy", action="store_true", help="Physical IDE files; .spine stays a symlink")
    install.add_argument("--rsync", action="store_true", help="Populate .spine as a real directory")
    install.add_argument("--core", action="store_true", help="Install the five core skills only")
    install.add_argument("--skills", default=None, help="all, core, or a comma-separated list")
    install.add_argument("--add-skill", default="", help="Install one skill and exit")
    install.add_argument("--remove-skill", default="", help="Remove one skill and exit")
    install.add_argument("--list-skills", action="store_true")
    install.add_argument("--targets", default=DEFAULT_TARGETS)
    install.add_argument("--update", action="store_true", help="Reconcile wiring; does not git pull")
    install.add_argument("--uninstall", action="store_true")
    install.add_argument("--with-graphify", action="store_true")
    install.add_argument("--graphify-init", action="store_true")
    install.add_argument("--graphify-hooks", action="store_true")
    install.add_argument("--graphify-uninstall", action="store_true")
    install.add_argument("--purge-graphify", action="store_true")
    install.add_argument("--no-graphify-prompt", action="store_true")
    install.add_argument("--with-mkdocs", action="store_true")
    install.add_argument("--mkdocs-uninstall", action="store_true")
    install.add_argument("--purge-mkdocs", action="store_true")
    install.add_argument("--no-mkdocs-prompt", action="store_true")
    install.add_argument("--global", dest="global_mode", action="store_true", help=argparse.SUPPRESS)
    install.add_argument("--project", dest="project_mode", action="store_true", help=argparse.SUPPRESS)
    install.set_defaults(handler=_cmd_install)

    vendor = sub.add_parser("vendor", help="Copy Spine into the project as real files")
    _add_project_flags(vendor)
    vendor.add_argument("--core", action="store_true")
    vendor.add_argument("--skills", default=None)
    vendor.add_argument("--targets", default=DEFAULT_TARGETS)
    vendor.add_argument("--update", action="store_true")
    vendor.add_argument("--uninstall", action="store_true")
    vendor.set_defaults(handler=_cmd_vendor)

    update = sub.add_parser("update", help="git pull, then reconcile wiring")
    _add_project_flags(update)
    update.add_argument("--no-pull", action="store_true")
    update.add_argument("--replace-opencode", action="store_true")
    update.add_argument("--with-graphify", action="store_true")
    update.add_argument("--graphify-init", action="store_true")
    update.add_argument("--with-mkdocs", action="store_true")
    update.add_argument("--no-graphify-prompt", action="store_true")
    update.add_argument("--no-mkdocs-prompt", action="store_true")
    update.set_defaults(handler=_cmd_update)

    uninstall = sub.add_parser("uninstall", help="Remove Spine artefacts for the detected mode")
    _add_project_flags(uninstall)
    uninstall.set_defaults(handler=_cmd_uninstall)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the installer CLI.

    Args:
        argv: Arguments without the program name. Defaults to ``sys.argv[1:]``.

    Returns:
        Process exit code.
    """
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
