"""Graphify co-install and uninstall. The ``graphify`` CLI stays an external process."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from spine_cli.constants import MIN_GRAPHIFY_VERSION
from spine_cli.log import Log
from spine_cli.opencode_merge import merge_graphify_plugin, strip_graphify_plugin


def _run(project: Path, args: list[str], log: Log) -> bool:
    if log.dry_run:
        print(f"    [DRY-RUN] Would run: {' '.join(args)}")
        return True
    if shutil.which(args[0]) is None:
        print(f"      skipped: {args[0]} CLI not available")
        return False
    completed = subprocess.run(args, cwd=project, check=False)
    if completed.returncode != 0:
        print(f"      WARNING: {' '.join(args)} failed", file=sys.stderr)
        return False
    return True


def _version_warning() -> None:
    completed = subprocess.run(
        ["graphify", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )
    text = (completed.stdout or completed.stderr or "").strip()
    tokens = text.split()
    version = ""
    for token in tokens:
        if token[:1].isdigit():
            version = token
            break
    parts = version.split(".")
    if len(parts) < 2:
        return
    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError:
        return
    if (major, minor) < MIN_GRAPHIFY_VERSION[:2]:
        print(
            f"    WARNING: graphifyy {version} < recommended "
            f"{'.'.join(str(part) for part in MIN_GRAPHIFY_VERSION)}",
            file=sys.stderr,
        )


def _selected(targets: str) -> set[str]:
    return {part.strip() for part in targets.split(",") if part.strip()}


def setup_graphify(
    project: Path,
    spine: Path,
    log: Log,
    *,
    targets: str,
    init_graph: bool,
    hooks: bool,
) -> None:
    """Seed ``.graphifyignore``, optionally build the graph, and co-install platforms.

    Args:
        project: Consumer project root.
        spine: Spine repository root.
        log: Progress logger.
        targets: Comma-separated ``cursor,opencode,claude``.
        init_graph: Run ``graphify update .`` and platform install.
        hooks: Run ``graphify hook install``.
    """
    selected = _selected(targets)
    print("  - Graphify CLI check")
    if shutil.which("graphify"):
        print(f"    graphify detected: {shutil.which('graphify')}")
        if not log.dry_run:
            _version_warning()
    else:
        print("    WARNING: graphify CLI not found.")
        print("    Install globally (recommended):")
        print("      uv tool install graphifyy")

    template = spine / "templates" / "dot.graphifyignore"
    target = project / ".graphifyignore"
    print("  - .graphifyignore")
    if not template.is_file():
        print(f"    WARNING: template not found: {template}")
    elif target.is_file():
        print(f"    exists, preserving: {target}")
    elif log.dry_run:
        print(f"    [DRY-RUN] Would copy {template} -> {target}")
    else:
        shutil.copy2(template, target)
        print(f"    copied: {target}")

    if not init_graph:
        return

    print("  - initial graph build")
    if shutil.which("graphify") is None and not log.dry_run:
        print("    skipped: graphify CLI not available")
    else:
        _run(project, ["graphify", "update", "."], log)

    print(f"  - Graphify platform co-install (targets: {targets})")
    if "cursor" in selected:
        print("    Cursor (graphify.mdc):")
        _run(project, ["graphify", "cursor", "install"], log)
        rule = project / ".cursor" / "rules" / "graphify.mdc"
        if rule.is_file():
            mirror = project / ".agents" / "rules" / "graphify.mdc"
            if log.dry_run:
                print("    [DRY-RUN] Would mirror graphify.mdc -> .agents/rules/")
            else:
                mirror.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(rule, mirror)
                print("    mirrored graphify.mdc -> .agents/rules/ (Antigravity)")
    if "opencode" in selected:
        print("    OpenCode (skill + plugin):")
        _run(project, ["graphify", "install", "--platform", "opencode"], log)
        _run(project, ["graphify", "opencode", "install"], log)
        merge_graphify_plugin(project, log)
    if "claude" in selected:
        print("    Claude Code (CLAUDE.md + PreToolUse hook):")
        _run(project, ["graphify", "claude", "install"], log)
    if hooks:
        print("  - Git hooks (graphify hook install)")
        _run(project, ["graphify", "hook", "install"], log)

    if log.dry_run:
        return
    print("  - integration verify")
    import spine_validate

    report = spine_validate.validate_graphify(project, targets)
    if not report.passed:
        print("    WARNING: graphify validation reported issues", file=sys.stderr)


def uninstall_graphify(
    project: Path,
    log: Log,
    *,
    targets: str,
    purge: bool,
) -> None:
    """Remove Graphify platform artifacts.

    Args:
        project: Consumer project root.
        log: Progress logger.
        targets: Comma-separated platforms.
        purge: Also remove ``graphify-out/`` and ``.graphifyignore``.
    """
    selected = _selected(targets)
    print(f"  - Graphify platform uninstall (targets: {targets})")
    if "cursor" in selected:
        print("    Cursor:")
        _run(project, ["graphify", "cursor", "uninstall"], log)
    if "opencode" in selected:
        print("    OpenCode:")
        _run(project, ["graphify", "opencode", "uninstall"], log)
        strip_graphify_plugin(project, log)
    if "claude" in selected:
        print("    Claude Code:")
        _run(project, ["graphify", "claude", "uninstall"], log)
    if purge:
        print("  - Purge graph artifacts")
        if log.dry_run:
            print("    [DRY-RUN] Would remove graphify-out/ and .graphifyignore")
            return
        graph_out = project / "graphify-out"
        if graph_out.exists():
            shutil.rmtree(graph_out)
        ignore = project / ".graphifyignore"
        if ignore.is_file() or ignore.is_symlink():
            ignore.unlink()
        print("    removed graphify-out/ and .graphifyignore")
    else:
        print("  - Preserved graphify-out/ and .graphifyignore (use --purge-graphify to remove)")
