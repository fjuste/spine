#!/usr/bin/env python3
"""Spine validators (cross-platform, standard library only).

Usage (from consumer project root; on Windows use ``py -3`` or ``python``):
    python3 .spine/scripts/spine_validate.py task docs/memory/active_tasks/007-foo.md
    python3 .spine/scripts/spine_validate.py bootstrap
    python3 .spine/scripts/spine_validate.py graphify --targets=cursor,opencode,claude
    python3 .spine/scripts/spine_validate.py mkdocs
    python3 .spine/scripts/spine_validate.py memory [--project-root=PATH]
    python3 .spine/scripts/spine_validate.py staged   # git pre-commit hook

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
import tempfile
from datetime import date
from pathlib import Path
from typing import NamedTuple, NoReturn

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from spine_cli.constants import DOCS_SEED_PATHS
from spine_cli.memory import (
    ENTRY_SUMMARY_MAX_CHARS,
    INDEX_NAME,
    LEDGER_DIR,
    LEDGER_FOLDERS,
    MEMORY_DIR,
    TASK_FILE_RE,
    check_budgets,
    check_ledger,
    check_open_tasks,
    collect_entries,
    index_path,
    render_index,
)

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
        report.fail("missing .spine (run python3 /path/to/spine/scripts/spine.py install)")

    if not (spine / "scripts" / "spine_validate.py").is_file():
        report.fail("missing .spine/scripts/spine_validate.py (run python3 .spine/scripts/spine.py update)")

    command_paths = (
        root / ".cursor" / "commands" / "spine-bootstrap.md",
        root / ".opencode" / "commands" / "spine-bootstrap.md",
    )
    if not any(path.is_file() for path in command_paths):
        report.fail("spine-bootstrap slash command not found (.cursor/commands/ or .opencode/commands/)")

    if not (root / "opencode.json").is_file():
        report.fail("missing opencode.json (run python3 .spine/scripts/spine.py install)")

    for relative in DOCS_SEED_PATHS:
        if not (root / relative).is_file():
            report.fail(f"missing seed file: {relative} (run python3 .spine/scripts/spine.py install)")

    for relative in BOOTSTRAP_REQUIRED_DIRS:
        if not (root / relative).is_dir():
            report.fail(f"missing directory: {relative} (run python3 .spine/scripts/spine.py install)")

    return report


def _bootstrap_soft_notes(root: Path) -> None:
    if (root / "graphify-out" / "graph.json").is_file():
        if not validate_graphify(root, GRAPHIFY_DEFAULT_TARGETS, Report(quiet=True)).passed:
            print("NOTE: graphify-out/graph.json exists but tri-platform integration may be incomplete.", file=sys.stderr)
            print(f"      Run: {VALIDATE_CMD} graphify", file=sys.stderr)
            print("      Or:  python3 .spine/scripts/spine.py install and answer yes at the Graphify prompt", file=sys.stderr)
            print("      (non-interactive: python3 .spine/scripts/spine.py install --with-graphify)", file=sys.stderr)

    if (root / MKDOCS_CONFIG).is_file():
        if not validate_mkdocs(root, Report(quiet=True)).passed:
            print(f"NOTE: {MKDOCS_CONFIG} exists but integration may be incomplete.", file=sys.stderr)
            print(f"      Run: {VALIDATE_CMD} mkdocs", file=sys.stderr)
            print("      Or:  python3 .spine/scripts/spine.py install and answer yes at the MkDocs prompt", file=sys.stderr)
            print("      (non-interactive: python3 .spine/scripts/spine.py install --with-mkdocs)", file=sys.stderr)


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
            "missing graphify-out/graph.json (run python3 .spine/scripts/spine.py install and answer yes at Graphify prompt; "
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
            report.warn("Spine .cursor/rules/02-memory-bank.md not found (run python3 .spine/scripts/spine.py install)")
        if (root / ".agents" / "rules").is_dir():
            if (root / ".agents" / "rules" / "graphify.mdc").is_file():
                report.ok("Antigravity", ".agents/rules/graphify.mdc")
            else:
                report.warn("missing .agents/rules/graphify.mdc (re-run spine.py install --with-graphify or mirror from .cursor/rules/)")

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
            report.warn(".claude/skills not found (run python3 .spine/scripts/spine.py install --targets=claude)")

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
            f"missing {MKDOCS_CONFIG} (run python3 .spine/scripts/spine.py install and answer yes at MkDocs prompt; "
            "non-interactive: --with-mkdocs)"
        )

    if (root / "docs" / "mkdocs" / "index.md").is_file():
        report.ok("Index", "docs/mkdocs/index.md")
    elif config.is_file():
        report.warn("missing docs/mkdocs/index.md (run python3 .spine/scripts/spine.py install --update)")

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
# memory
# =============================================================================


def validate_memory(root: Path, report: Report | None = None) -> Report:
    """Measure ``docs/memory/`` against its budgets and check ledger folders and open tasks.

    Over-budget scopes, entries without a valid ``summary:``, stale
    ``INDEX.md`` files and open tasks that need a human to close them (no valid
    status, stale REVIEW, DONE left in ``active_tasks/``) are warnings; only a
    missing memory bank is an error.

    Args:
        root: Consumer project root.
        report: Optional report to append to.

    Returns:
        The report with recorded errors and warnings.
    """
    report = report or Report()
    if not (root / MEMORY_DIR).is_dir():
        report.fail(f"missing {MEMORY_DIR.as_posix()}/ (run python3 .spine/scripts/spine.py install)")
        return report
    report.out("Memory budget report")
    for check in check_budgets(root):
        if check.over:
            report.warn(f"{check.scope}: {check.chars:,} chars > {check.limit:,} — {check.detail}")
        else:
            report.ok(check.scope, f"{check.chars:,} / {check.limit:,} chars")
    for ledger in check_ledger(root):
        for problem in ledger.problems:
            report.warn(f"{ledger.scope}: {problem}")
        if not ledger.problems:
            noun = "entry" if ledger.entries == 1 else "entries"
            report.ok(ledger.scope, f"{ledger.entries} {noun}, {INDEX_NAME} up to date")
    tasks = check_open_tasks(root, date.today())
    if tasks is not None:
        for problem in tasks.problems:
            report.warn(f"{tasks.scope}: {problem}")
        if not tasks.problems:
            report.ok(tasks.scope, f"{tasks.tasks} open task(s), no stale tasks")
    return report


def run_memory(args: argparse.Namespace) -> int:
    """CLI handler for ``memory``."""
    root = Path(args.project_root).resolve() if args.project_root else Path.cwd()
    if args.dry_run:
        print(f"[DRY-RUN] Would check memory budgets in: {root}")

    report = validate_memory(root)
    if not report.passed:
        print(f"Memory budget check failed with {report.errors} error(s).", file=sys.stderr)
        return 1
    if report.warnings:
        print(f"OK: memory budgets checked with {report.warnings} warning(s).")
    else:
        print("OK: memory bank within budget.")
    return 0


# =============================================================================
# staged (git pre-commit)
# =============================================================================


MEMORY_PATHSPEC = f"{MEMORY_DIR.as_posix()}/"
TASK_DIRS = ("active_tasks", "completed_tasks")
CONTENT_STATUSES = frozenset({"A", "M", "C", "T"})
RENAME_STATUS = "R"
PURE_RENAME_SCORE = 100
STAGED_FIX_HINT = "run python3 .spine/scripts/spine.py memory index, then git add it"


class GitError(Exception):
    """A git command failed or git is unavailable."""


class StagedChange(NamedTuple):
    """One staged change under ``docs/memory/`` (``git diff --cached --name-status``).

    Args:
        status: Status letter (``A``, ``M``, ``D``, ``R``, ``C``, ``T``, ...).
        score: Similarity score for renames and copies (0 otherwise).
        path: Path after the change, relative to the project root.
        old_path: Source path of a rename or copy (equal to ``path`` otherwise).
    """

    status: str
    score: int
    path: str
    old_path: str

    @property
    def content_changed(self) -> bool:
        """True unless the change is a deletion or a pure (100%) rename."""
        if self.status == RENAME_STATUS:
            return self.score < PURE_RENAME_SCORE
        return self.status in CONTENT_STATUSES


class _ScopedReport(Report):
    """Report that prefixes every message with a file path and forwards it to a parent report."""

    def __init__(self, parent: Report, scope: str) -> None:
        super().__init__(quiet=parent.quiet)
        self.parent = parent
        self.scope = scope

    def fail(self, message: str) -> None:
        """Record an error on the parent report."""
        self.parent.fail(f"{self.scope}: {message}")

    def warn(self, message: str) -> None:
        """Record a warning on the parent report."""
        self.parent.warn(f"{self.scope}: {message}")


def _git(root: Path, args: list[str], stdin: bytes | None = None) -> bytes:
    """Run git in ``root`` and return its stdout.

    Raises:
        GitError: When git is missing or exits non-zero.
    """
    try:
        result = subprocess.run(["git", *args], cwd=root, input=stdin, capture_output=True, check=False)
    except OSError as exc:
        raise GitError(f"git not available: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(f"git {args[0]} failed: {detail}")
    return result.stdout


def parse_name_status(output: bytes) -> list[StagedChange]:
    """Parse ``git diff --name-status -z`` output.

    Args:
        output: Raw NUL-separated output (renames and copies carry two paths).

    Returns:
        One change per staged file.
    """
    fields = output.decode("utf-8", errors="surrogateescape").split("\0")
    changes: list[StagedChange] = []
    index = 0
    while index < len(fields) and fields[index]:
        code = fields[index]
        status, score = code[0], int(code[1:] or 0)
        if status in (RENAME_STATUS, "C"):
            old_path, path = fields[index + 1], fields[index + 2]
            index += 3
        else:
            old_path = path = fields[index + 1]
            index += 2
        changes.append(StagedChange(status, score, path, old_path))
    return changes


def staged_changes(root: Path) -> list[StagedChange]:
    """List staged changes under ``docs/memory/``, paths relative to ``root``."""
    args = ["diff", "--cached", "--name-status", "-z", "-M", "--relative", "--", MEMORY_PATHSPEC]
    return parse_name_status(_git(root, args))


def snapshot_memory(root: Path, target: Path) -> Path:
    """Write the index (staged) copy of ``docs/memory/`` under ``target``.

    Args:
        root: Project root (current directory of the commit).
        target: Empty temporary directory.

    Returns:
        The snapshot project root: ``<target>/<prefix>`` holds ``docs/memory/``.
    """
    prefix = _git(root, ["rev-parse", "--show-prefix"]).decode("utf-8").strip()
    files = _git(root, ["ls-files", "-z", "--", MEMORY_PATHSPEC])
    _git(root, ["checkout-index", "-z", "--stdin", f"--prefix={target.as_posix()}/"], stdin=files)
    return target / prefix


def _is_task_path(path: str) -> bool:
    parts = Path(path).parts
    memory_parts = MEMORY_DIR.parts
    return (
        len(parts) == len(memory_parts) + 2
        and parts[: len(memory_parts)] == memory_parts
        and parts[len(memory_parts)] in TASK_DIRS
        and bool(TASK_FILE_RE.match(parts[-1]))
    )


def _ledger_folder(path: str) -> str | None:
    """Return the ledger folder name when ``path`` sits directly in one, else None."""
    parts = Path(path).parts
    prefix = (*MEMORY_DIR.parts, LEDGER_DIR)
    if len(parts) == len(prefix) + 2 and parts[: len(prefix)] == prefix and parts[len(prefix)] in LEDGER_FOLDERS:
        return parts[len(prefix)]
    return None


def _check_staged_tasks(snapshot: Path, changes: list[StagedChange], report: Report) -> None:
    for change in changes:
        if change.content_changed and _is_task_path(change.path):
            validate_task(snapshot / change.path, _ScopedReport(report, change.path))


def _check_staged_ledger(snapshot: Path, changes: list[StagedChange], report: Report) -> None:
    memory_dir = snapshot / MEMORY_DIR
    for folder in LEDGER_FOLDERS:
        touched = [c for c in changes if folder in (_ledger_folder(c.path), _ledger_folder(c.old_path))]
        if not touched or not (memory_dir / LEDGER_DIR / folder).is_dir():
            continue
        entries = collect_entries(memory_dir, folder)
        by_name = {entry.filename: entry for entry in entries}
        for change in touched:
            entry = by_name.get(Path(change.path).name)
            if not change.content_changed or _ledger_folder(change.path) != folder or entry is None:
                continue
            if not entry.summary:
                report.fail(f"{change.path}: missing `summary:` (one line, at most {ENTRY_SUMMARY_MAX_CHARS} chars)")
            elif len(entry.summary) > ENTRY_SUMMARY_MAX_CHARS:
                report.fail(f"{change.path}: `summary:` is {len(entry.summary)} chars (max {ENTRY_SUMMARY_MAX_CHARS})")
        index = index_path(memory_dir, folder)
        shown = index.relative_to(snapshot).as_posix()
        if not index.is_file():
            report.fail(f"{shown} missing — {STAGED_FIX_HINT}")
        elif read_text(index) != render_index(folder, entries):
            report.fail(f"{shown} is stale — {STAGED_FIX_HINT}")


def _warn_staged(snapshot: Path, report: Report) -> None:
    for check in check_budgets(snapshot):
        if check.over:
            report.warn(f"{check.scope}: {check.chars:,} chars > {check.limit:,} — {check.detail}")
    tasks = check_open_tasks(snapshot, date.today())
    if tasks is not None:
        for problem in tasks.problems:
            report.warn(f"{tasks.scope}: {problem}")


def validate_staged(root: Path, report: Report | None = None) -> Report:
    """Check the staged snapshot of ``docs/memory/`` before a commit.

    Errors (block the commit): staged task files that break the task contract,
    changed ledger entries with a missing or over-long ``summary:``, and a
    missing or stale ``INDEX.md`` in a ledger folder the commit touches. Pure
    renames and untouched files are not checked. Budget and open-task problems
    are warnings. No staged ``docs/memory/`` change → nothing is printed.

    Args:
        root: Project root (the git work tree directory holding ``docs/memory/``).
        report: Optional report to append to.

    Returns:
        The report with recorded errors and warnings.
    """
    report = report or Report()
    try:
        changes = staged_changes(root)
        if not changes:
            return report
        with tempfile.TemporaryDirectory(prefix="spine-staged-") as tmp:
            snapshot = snapshot_memory(root, Path(tmp))
            _check_staged_tasks(snapshot, changes, report)
            _check_staged_ledger(snapshot, changes, report)
            _warn_staged(snapshot, report)
    except GitError as exc:
        report.fail(f"{exc} (run from the project root inside a git work tree)")
    return report


def run_staged(args: argparse.Namespace) -> int:
    """CLI handler for ``staged`` (called by the git pre-commit hook)."""
    root = Path.cwd()
    if args.dry_run:
        print(f"[DRY-RUN] Would check staged memory files in: {root}")
        return 0
    report = validate_staged(root)
    if not report.passed:
        print(
            f"Commit blocked: {report.errors} memory error(s). Fix them, git add the files, and commit again.",
            file=sys.stderr,
        )
        return 1
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

    memory = subparsers.add_parser("memory", help="Check docs/memory/ against digest-first budgets.")
    memory.add_argument("--project-root", help="Project root (default: current directory)")
    memory.add_argument("--dry-run", action="store_true")
    memory.set_defaults(handler=run_memory)

    staged = subparsers.add_parser("staged", help="Check staged docs/memory/ files (git pre-commit hook).")
    staged.add_argument("--dry-run", action="store_true")
    staged.set_defaults(handler=run_staged)

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
