#!/usr/bin/env python3
"""Spine validators (cross-platform, standard library only).

Usage (from consumer project root; on Windows use ``py -3`` or ``python``):
    python3 .spine/scripts/spine_validate.py task docs/memory/active_tasks/007-foo.md
    python3 .spine/scripts/spine_validate.py bootstrap
    python3 .spine/scripts/spine_validate.py graphify --targets=cursor,opencode,claude
    python3 .spine/scripts/spine_validate.py mkdocs

Every subcommand accepts ``--dry-run``. Exit code 0 means OK (warnings allowed),
1 means at least one error. ``ERROR:``/``WARNING:``/``NOTE:`` go to stderr and
``OK:`` lines go to stdout; agents and slash commands rely on these prefixes.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

VALIDATE_CMD = "python3 .spine/scripts/spine_validate.py"

TASK_REQUIRED_KEYS = (
    "task_id",
    "title",
    "goal",
    "status",
    "tags",
    "branch",
    "base",
    "created_at",
    "updated_at",
)
TASK_MIN_TAGS = 1
TASK_MAX_TAGS = 5
TASK_LEGACY_PATTERNS = (r"^\*\*Status:\*\*", r"^\*\*Branch:\*\*")
TASK_REQUIRED_SECTIONS = ("## Objective", "## Acceptance Criteria")

# Must match install.sh / install-vendor.sh / install.ps1 docs seed lists.
DOCS_SEED_PATHS = (
    "docs/memory/global/project-brief.md",
    "docs/memory/global/product-context.md",
    "docs/memory/global/domain-glossary.md",
    "docs/memory/global/system-patterns.md",
    "docs/memory/global/tech-context.md",
    "docs/memory/global/decision-log.md",
    "docs/memory/ledger/roadmap.md",
    "docs/memory/ledger/progress.md",
    "docs/memory/ledger/learnings.md",
    "docs/memory/active_tasks/_task-template.md",
    "docs/governance/skills-policy.md",
    "docs/governance/memory-tags-policy.md",
    "docs/governance/ice-scoring-guide.md",
    "docs/quality/guardrails.md",
    "docs/workflow/gitflow-operacional.md",
    "docs/workflow/ciclo-de-entrega.md",
)
BOOTSTRAP_REQUIRED_DIRS = ("docs/memory/active_tasks", "docs/memory/completed_tasks")

GRAPHIFY_DEFAULT_TARGETS = "cursor,opencode,claude"
GRAPHIFY_KNOWN_TARGETS = ("cursor", "opencode", "claude")
MIN_GRAPHIFY_VERSION = (0, 7, 16)

MKDOCS_CONFIG = "docs/mkdocs/mkdocs.yml"
MKDOCS_BUILD_ARGS = ("build", "-f", MKDOCS_CONFIG, "--strict")
MKDOCS_SITE_DIRS = ("docs/mkdocs-site", "docs/mkdocs/site")
SUBPROCESS_TIMEOUT_SECONDS = 600

SEMVER_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


class Report:
    """Collects validation errors and warnings and prints them as they occur.

    Args:
        quiet: When True, nothing is printed (used for nested soft checks).
    """

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet
        self.errors = 0
        self.warnings = 0

    def fail(self, message: str) -> None:
        """Record an error."""
        self.errors += 1
        self._err(f"ERROR: {message}")

    def warn(self, message: str) -> None:
        """Record a warning."""
        self.warnings += 1
        self._err(f"WARNING: {message}")

    def ok(self, label: str, detail: str) -> None:
        """Print a passing check line."""
        self.out(f"  {label}: OK ({detail})")

    def out(self, message: str) -> None:
        """Print to stdout unless quiet."""
        if not self.quiet:
            print(message)

    def _err(self, message: str) -> None:
        if not self.quiet:
            print(message, file=sys.stderr)

    @property
    def passed(self) -> bool:
        """True when no errors were recorded."""
        return self.errors == 0


def read_text(path: Path) -> str:
    """Read a UTF-8 text file (BOM tolerated) with newlines normalized to LF.

    Args:
        path: File to read.

    Returns:
        File content using ``\\n`` line endings.
    """
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n")


# =============================================================================
# task
# =============================================================================


def _first_line(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(0) if match else ""


def validate_task(task_file: Path, report: Report | None = None) -> Report:
    """Validate a Memory Bank active task file against the v2.1 contract.

    Args:
        task_file: Path to the task markdown file (must exist).
        report: Optional report to append to.

    Returns:
        The report with recorded errors and warnings.
    """
    report = report or Report()
    content = read_text(task_file)

    if not content.startswith("---"):
        report.fail("missing YAML frontmatter (file must start with ---)")
    else:
        frontmatter = content[3:].split("---", 1)[0]
        for key in TASK_REQUIRED_KEYS:
            if not re.search(rf"^{key}:", frontmatter, flags=re.MULTILINE):
                report.fail(f"frontmatter missing key: {key}")

        branch_line = _first_line(r"^branch:.*$", frontmatter)
        if branch_line and "feature/" not in branch_line:
            report.warn(f"branch does not start with feature/ (non-standard GitFlow): {branch_line}")

        base_line = _first_line(r"^base:.*$", frontmatter)
        if base_line and "develop" not in base_line:
            report.warn(f"base is not develop: {base_line}")

        tag_count = len(re.findall(r"^[ \t]+- ", frontmatter, flags=re.MULTILINE))
        if tag_count < TASK_MIN_TAGS:
            report.fail(f"tags list empty (need {TASK_MIN_TAGS}-{TASK_MAX_TAGS} tags)")
        elif tag_count > TASK_MAX_TAGS:
            report.fail(f"too many tags ({tag_count}; max {TASK_MAX_TAGS})")

    for pattern in TASK_LEGACY_PATTERNS:
        if re.search(pattern, content, flags=re.MULTILINE):
            report.fail(f"legacy pattern found: {pattern}")

    for line in content.split("\n"):
        lowered = line.lower()
        if "superpowers:" in lowered and not re.search(r"do not|never use|`superpowers", lowered):
            report.fail("promotional superpowers: reference found (use execution_skill in frontmatter)")
            break

    for section in TASK_REQUIRED_SECTIONS:
        if section not in content:
            report.fail(f"missing required section: {section}")

    if re.search(r"^### Task [0-9]+:", content, flags=re.MULTILINE) and "## Implementation Plan" not in content:
        report.fail("Task N blocks found outside ## Implementation Plan section")

    return report


def run_task(args: argparse.Namespace) -> int:
    """CLI handler for ``task``."""
    if not args.task_file:
        print("ERROR: task file path required.", file=sys.stderr)
        return 1
    task_file = Path(args.task_file)
    if not task_file.is_file():
        print(f"ERROR: file not found: {args.task_file}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[DRY-RUN] Would validate: {args.task_file}")
        return 0

    report = validate_task(task_file)
    if not report.passed:
        print(f"Validation failed with {report.errors} error(s).", file=sys.stderr)
        return 1
    print(f"OK: {args.task_file} matches Memory Bank v2.1 task contract.")
    return 0


# =============================================================================
# bootstrap
# =============================================================================


def validate_bootstrap(root: Path, report: Report | None = None) -> Report:
    """Check install artifacts required before /spine-bootstrap.

    Args:
        root: Consumer project root.
        report: Optional report to append to.

    Returns:
        The report with recorded errors.
    """
    report = report or Report()

    spine = root / ".spine"
    if not (spine.exists() or spine.is_symlink()):
        report.fail("missing .spine (run link-spine.sh then bash .spine/install.sh)")

    if not (spine / "scripts" / "spine_validate.py").is_file():
        report.fail("missing .spine/scripts/spine_validate.py (run bash .spine/scripts/update.sh)")

    command_paths = (
        root / ".cursor" / "commands" / "spine-bootstrap.md",
        root / ".opencode" / "commands" / "spine-bootstrap.md",
    )
    if not any(path.is_file() for path in command_paths):
        report.fail("spine-bootstrap slash command not found (.cursor/commands/ or .opencode/commands/)")

    if not (root / "opencode.json").is_file():
        report.fail("missing opencode.json (run bash .spine/install.sh)")

    for relative in DOCS_SEED_PATHS:
        if not (root / relative).is_file():
            report.fail(f"missing seed file: {relative} (run bash .spine/install.sh)")

    for relative in BOOTSTRAP_REQUIRED_DIRS:
        if not (root / relative).is_dir():
            report.fail(f"missing directory: {relative} (run bash .spine/install.sh)")

    return report


def _bootstrap_soft_notes(root: Path) -> None:
    if (root / "graphify-out" / "graph.json").is_file():
        if not validate_graphify(root, GRAPHIFY_DEFAULT_TARGETS, Report(quiet=True)).passed:
            print("NOTE: graphify-out/graph.json exists but tri-platform integration may be incomplete.", file=sys.stderr)
            print(f"      Run: {VALIDATE_CMD} graphify", file=sys.stderr)
            print("      Or:  bash .spine/install.sh and answer yes at the Graphify prompt", file=sys.stderr)
            print("      (non-interactive: bash .spine/install.sh --with-graphify)", file=sys.stderr)

    if (root / MKDOCS_CONFIG).is_file():
        if not validate_mkdocs(root, Report(quiet=True)).passed:
            print(f"NOTE: {MKDOCS_CONFIG} exists but integration may be incomplete.", file=sys.stderr)
            print(f"      Run: {VALIDATE_CMD} mkdocs", file=sys.stderr)
            print("      Or:  bash .spine/install.sh and answer yes at the MkDocs prompt", file=sys.stderr)
            print("      (non-interactive: bash .spine/install.sh --with-mkdocs)", file=sys.stderr)


def run_bootstrap(args: argparse.Namespace) -> int:
    """CLI handler for ``bootstrap``."""
    root = Path.cwd()
    if args.dry_run:
        print(f"[DRY-RUN] Would validate bootstrap readiness from: {root}")

    report = validate_bootstrap(root)
    if not report.passed:
        print(f"Bootstrap readiness check failed with {report.errors} error(s).", file=sys.stderr)
        return 1
    print("OK: project is ready for /spine-bootstrap.")
    _bootstrap_soft_notes(root)
    return 0


# =============================================================================
# graphify
# =============================================================================


def parse_semver(text: str) -> tuple[int, int, int] | None:
    """Extract the first ``X.Y.Z`` version from text.

    Args:
        text: Arbitrary version output (e.g. ``graphify 0.7.16``).

    Returns:
        Version tuple, or None when no version is found.
    """
    match = SEMVER_RE.search(text)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _command_output(command: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False, ""
    output = (result.stdout or "").strip().splitlines()
    return result.returncode == 0, (output[0] if output else "")


def _file_contains(path: Path, needle: str, ignore_case: bool = False) -> bool:
    if not path.is_file():
        return False
    try:
        text = read_text(path)
    except (OSError, UnicodeDecodeError):
        return False
    if ignore_case:
        return needle.lower() in text.lower()
    return needle in text


def _exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def validate_graphify(root: Path, targets: str, report: Report | None = None) -> Report:
    """Check Graphify artifacts, CLI, and per-IDE integration.

    Args:
        root: Consumer project root.
        targets: Comma-separated targets (cursor, opencode, claude).
        report: Optional report to append to.

    Returns:
        The report with recorded errors and warnings.
    """
    report = report or Report()
    selected: set[str] = set()
    for target in (part.strip() for part in targets.split(",")):
        if not target:
            continue
        if target in GRAPHIFY_KNOWN_TARGETS:
            selected.add(target)
        else:
            report.warn(f"unknown target '{target}', skipping")

    report.out("Graphify integration report")
    report.out(f"  Targets: {targets}")

    graph = root / "graphify-out" / "graph.json"
    if graph.is_file():
        report.ok("Graph", "graphify-out/graph.json")
    else:
        report.fail(
            "missing graphify-out/graph.json (run bash .spine/install.sh and answer yes at Graphify prompt; "
            "non-interactive: --with-graphify)"
        )

    if (root / "graphify-out" / "GRAPH_REPORT.md").is_file():
        report.ok("Report", "graphify-out/GRAPH_REPORT.md")
    elif graph.is_file():
        report.warn("missing graphify-out/GRAPH_REPORT.md (stale or partial build?)")

    if (root / ".graphifyignore").is_file():
        report.ok("Ignore", ".graphifyignore")
    else:
        report.warn("missing .graphifyignore")

    graphify_bin = shutil.which("graphify")
    if graphify_bin:
        _, version = _command_output([graphify_bin, "--version"], root)
        if not version:
            report.ok("CLI", "graphify on PATH - (unknown version)")
        else:
            report.ok("CLI", f"graphify {version}")
            parsed = parse_semver(version)
            if parsed and parsed < MIN_GRAPHIFY_VERSION:
                minimum = ".".join(str(part) for part in MIN_GRAPHIFY_VERSION)
                report.warn(f"graphifyy {version} < recommended {minimum}")
    else:
        report.fail("graphify CLI not on PATH (uv tool install graphifyy)")

    if "cursor" in selected:
        if (root / ".cursor" / "rules" / "graphify.mdc").is_file():
            report.ok("Cursor", ".cursor/rules/graphify.mdc")
        else:
            report.fail("missing .cursor/rules/graphify.mdc (run graphify cursor install)")
        if _exists(root / ".cursor" / "rules" / "02-memory-bank.md"):
            report.ok("Cursor", "Spine memory-bank rule present")
        else:
            report.warn("Spine .cursor/rules/02-memory-bank.md not found (run bash .spine/install.sh)")
        if (root / ".agents" / "rules").is_dir():
            if (root / ".agents" / "rules" / "graphify.mdc").is_file():
                report.ok("Antigravity", ".agents/rules/graphify.mdc")
            else:
                report.warn("missing .agents/rules/graphify.mdc (re-run install-graphify or mirror from .cursor/rules/)")

    if "opencode" in selected:
        opencode_json = root / "opencode.json"
        if (root / ".opencode" / "plugins" / "graphify.js").is_file():
            report.ok("OpenCode", ".opencode/plugins/graphify.js")
        else:
            report.fail("missing .opencode/plugins/graphify.js (run graphify opencode install)")
        if _file_contains(opencode_json, "graphify"):
            report.ok("OpenCode", "graphify plugin registered in opencode.json")
        else:
            report.fail("graphify plugin not registered in project opencode.json (run merge-graphify-opencode.py)")
        if _file_contains(opencode_json, "02-memory-bank.md"):
            report.ok("OpenCode", "Spine instructions present in opencode.json")
        else:
            report.warn("Spine instructions missing from opencode.json")

    if "claude" in selected:
        claude_ok = False
        if _file_contains(root / "CLAUDE.md", "graphify", ignore_case=True):
            report.ok("Claude", "CLAUDE.md graphify section")
            claude_ok = True
        if _file_contains(root / ".claude" / "settings.json", "graphify", ignore_case=True):
            report.ok("Claude", "PreToolUse hook in .claude/settings.json")
            claude_ok = True
        if not claude_ok:
            report.fail("missing Claude graphify integration (run graphify claude install)")
        if _exists(root / ".claude" / "skills"):
            report.ok("Claude", ".claude/skills present")
        else:
            report.warn(".claude/skills not found (run bash .spine/install.sh --targets=claude)")

    return report


def run_graphify(args: argparse.Namespace) -> int:
    """CLI handler for ``graphify``."""
    root = Path.cwd()
    if args.dry_run:
        print(f"[DRY-RUN] Would validate Graphify integration from: {root}")

    report = validate_graphify(root, args.targets)
    if not report.passed:
        print(
            f"Graphify integration check failed with {report.errors} error(s), {report.warnings} warning(s).",
            file=sys.stderr,
        )
        return 1
    if report.warnings:
        print(f"OK: Graphify integration passed with {report.warnings} warning(s).")
    else:
        print(f"OK: Graphify integration complete for targets: {args.targets}")
    return 0


# =============================================================================
# mkdocs
# =============================================================================


def resolve_mkdocs_runner(root: Path) -> tuple[list[str], str] | None:
    """Find how to invoke mkdocs: uv, project virtualenv, then PATH.

    Args:
        root: Consumer project root.

    Returns:
        ``(command_prefix, label)`` or None when mkdocs is unavailable.
    """
    uv_bin = shutil.which("uv")
    if uv_bin:
        return [uv_bin, "run", "--extra", "docs", "mkdocs"], "uv run --extra docs mkdocs"
    for venv_mkdocs in (root / ".venv" / "bin" / "mkdocs", root / ".venv" / "Scripts" / "mkdocs.exe"):
        if venv_mkdocs.is_file():
            relative = venv_mkdocs.relative_to(root).as_posix()
            return [str(venv_mkdocs)], relative
    mkdocs_bin = shutil.which("mkdocs")
    if mkdocs_bin:
        return [mkdocs_bin], "mkdocs"
    return None


def validate_mkdocs(root: Path, report: Report | None = None) -> Report:
    """Check MkDocs config, CLI, strict build, site output, and gitignore.

    Args:
        root: Consumer project root.
        report: Optional report to append to.

    Returns:
        The report with recorded errors and warnings.
    """
    report = report or Report()
    report.out("MkDocs integration report")

    config = root / MKDOCS_CONFIG
    if config.is_file():
        report.ok("Config", MKDOCS_CONFIG)
    else:
        report.fail(
            f"missing {MKDOCS_CONFIG} (run bash .spine/install.sh and answer yes at MkDocs prompt; "
            "non-interactive: --with-mkdocs)"
        )

    if (root / "docs" / "mkdocs" / "index.md").is_file():
        report.ok("Index", "docs/mkdocs/index.md")
    elif config.is_file():
        report.warn("missing docs/mkdocs/index.md (run bash .spine/install.sh --update)")

    runner = resolve_mkdocs_runner(root)
    if runner:
        prefix, label = runner
        succeeded, version = _command_output(prefix + ["--version"], root)
        report.ok("CLI", f"{label} - {version if succeeded and version else 'unknown version'}")
    else:
        report.fail(
            "mkdocs not available via uv, .venv/bin/mkdocs, .venv/Scripts/mkdocs.exe, or PATH "
            "(uv sync --extra docs / uv pip install -r requirements-docs.txt)"
        )

    if config.is_file() and runner:
        prefix, label = runner
        built, _ = _command_output(prefix + list(MKDOCS_BUILD_ARGS), root)
        if built:
            report.ok("Build", f"{label} {' '.join(MKDOCS_BUILD_ARGS)} passes")
        else:
            report.warn("mkdocs build --strict failed (check docs/mkdocs/*.md for broken links or invalid YAML)")

        site_dir = next((relative for relative in MKDOCS_SITE_DIRS if (root / relative).is_dir()), "")
        if site_dir:
            report.ok("Output", f"{site_dir}/ present")
        else:
            report.warn("site output not found (expected docs/mkdocs-site/ or docs/mkdocs/site/)")

    gitignore = root / ".gitignore"
    gitignore_text = read_text(gitignore) if gitignore.is_file() else ""
    if re.search(r"docs/mkdocs(-site|/site)/", gitignore_text):
        report.ok("Gitignore", "MkDocs site output is gitignored")
    else:
        report.warn("docs/mkdocs/site/ or docs/mkdocs-site/ not in .gitignore (output may be accidentally committed)")

    return report


def run_mkdocs(args: argparse.Namespace) -> int:
    """CLI handler for ``mkdocs``."""
    root = Path.cwd()
    if args.dry_run:
        print(f"[DRY-RUN] Would validate MkDocs integration from: {root}")

    report = validate_mkdocs(root)
    if not report.passed:
        print(
            f"MkDocs integration check failed with {report.errors} error(s), {report.warnings} warning(s).",
            file=sys.stderr,
        )
        return 1
    if report.warnings:
        print(f"OK: MkDocs integration passed with {report.warnings} warning(s).")
    else:
        print("OK: MkDocs integration complete.")
    return 0


# =============================================================================
# CLI
# =============================================================================


USAGE_ERROR_EXIT_CODE = 1


class _Parser(argparse.ArgumentParser):
    """ArgumentParser that exits with 1 on usage errors (same as the Bash validators)."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(USAGE_ERROR_EXIT_CODE, f"ERROR: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with one subcommand per validator."""
    parser = _Parser(
        prog="spine_validate.py",
        description="Spine validators (run from the consumer project root).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    task = subparsers.add_parser("task", help="Validate an active task file (Memory Bank v2.1 contract).")
    task.add_argument("task_file", nargs="?", help="Path to docs/memory/active_tasks/NNN-name.md")
    task.add_argument("--dry-run", action="store_true")
    task.set_defaults(handler=run_task)

    bootstrap = subparsers.add_parser("bootstrap", help="Check install artifacts before /spine-bootstrap.")
    bootstrap.add_argument("--dry-run", action="store_true")
    bootstrap.set_defaults(handler=run_bootstrap)

    graphify = subparsers.add_parser("graphify", help="Check Graphify tri-platform integration.")
    graphify.add_argument("--targets", default=GRAPHIFY_DEFAULT_TARGETS, help="Comma-separated: cursor,opencode,claude")
    graphify.add_argument("--dry-run", action="store_true")
    graphify.set_defaults(handler=run_graphify)

    mkdocs = subparsers.add_parser("mkdocs", help="Check MkDocs configuration, CLI, and build.")
    mkdocs.add_argument("--dry-run", action="store_true")
    mkdocs.set_defaults(handler=run_mkdocs)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Arguments without the program name (defaults to ``sys.argv[1:]``).

    Returns:
        Process exit code.
    """
    # Keep stdout/stderr interleaving in order when output is piped (agents, CI).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
