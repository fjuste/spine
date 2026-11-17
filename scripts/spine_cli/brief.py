"""Pilot brief (``spine.py brief``): where the project is and what to do next.

A terminal view for the human pilot, computed from ``docs/memory/`` and git:
header, WHERE WE ARE, RECENT STORY, WAITING ON YOU and NEXT STEP. Nothing is
written. Standard library only, Python 3.9+.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from spine_cli.log import SpineExit
from spine_cli.memory import (
    COMPLETED_DIR,
    LEDGER_DIR,
    MEMORY_DIR,
    REVIEW_STATUS,
    TASK,
    LedgerEntry,
    MemoryFile,
    _cap,
    _section,
    check_open_tasks,
    collect_entries,
    collect_files,
    read_frontmatter,
    read_text,
)
from spine_cli.paths import resolve_project_root

STORY_DELIVERIES = 5
WHY_MAX_CHARS = 120
INDENT = "  "
WHY_INDENT = INDENT + " " * len("MM-DD  ")
EMPTY_SECTION = f"{INDENT}nothing"
IN_PROGRESS_STATUS = "IN_PROGRESS"
HARVEST_COMMAND = "/spine-harvest"
INSTALL_HINT = "python3 .spine/scripts/spine.py install"
ROADMAP = "ledger/roadmap.md"
PROGRESS = "ledger/progress.md"
OSC8_START = "\x1b]8;;"
OSC8_END = "\x1b\\"

_GOAL_HEADING_RE = re.compile(r"^###[ \t]+(G\d+):[ \t]*(.+?)[ \t]*$", re.MULTILINE)
_GOAL_ID_RE = re.compile(r"^G\d+$")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?$")
_UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")
_NEXT_BULLET_RE = re.compile(r"^-[ \t]+Next:[ \t]*(.+?)[ \t]*$", re.MULTILINE)


@dataclass(frozen=True)
class GitState:
    """Working-tree state shown in the brief header.

    Args:
        branch: Current branch name (empty when HEAD is detached).
        changes: Number of ``git status --porcelain`` lines.
    """

    branch: str
    changes: int


@dataclass(frozen=True)
class TaskRef:
    """One task file with the frontmatter fields the brief uses."""

    task_id: str
    title: str
    status: str
    roadmap_idea: str
    path: Path

    def number(self) -> int:
        """Task id as an int (0 when not numeric), for newest-first ordering."""
        return int(self.task_id) if self.task_id.isdigit() else 0


def read_git_state(root: Path) -> GitState | None:
    """Read branch and uncommitted change count of ``root``.

    Args:
        root: Project root.

    Returns:
        The state, or ``None`` when ``root`` is not inside a git work tree or git is missing.
    """
    try:
        inside = _git(root, "rev-parse", "--is-inside-work-tree")
        if inside is None or inside.strip() != "true":
            return None
        branch = _git(root, "branch", "--show-current") or ""
        status = _git(root, "status", "--porcelain") or ""
    except FileNotFoundError:
        return None
    return GitState(branch=branch.strip(), changes=len([line for line in status.split("\n") if line.strip()]))


def _git(root: Path, *args: str) -> str | None:
    result = subprocess.run(["git", "-C", str(root), *args], check=False, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def _link(text: str, path: Path, root: Path, is_tty: bool) -> str:
    """Return ``text`` linked to ``path``: OSC 8 on a terminal, else a trailing relative path."""
    if is_tty:
        return f"{OSC8_START}{path.resolve().as_uri()}{OSC8_END}{text}{OSC8_START}{OSC8_END}"
    return f"{text}  → {path.relative_to(root).as_posix()}"


def _header(root: Path, today: date, git: GitState | None) -> str:
    parts = [root.name]
    if git is None:
        parts.append("no git")
    else:
        parts.append(git.branch or "detached HEAD")
        if git.changes == 0:
            parts.append("clean tree")
        else:
            parts.append(f"{git.changes} uncommitted change{'' if git.changes == 1 else 's'}")
    parts.append(today.isoformat())
    return " · ".join(parts)


def _task_refs(memory_dir: Path, files: list[MemoryFile]) -> list[TaskRef]:
    refs: list[TaskRef] = []
    for item in files:
        if item.kind != TASK:
            continue
        fields = read_frontmatter(item.text)
        stem = item.relative.rsplit("/", 1)[1][: -len(".md")]
        refs.append(
            TaskRef(
                task_id=fields.get("task_id", "").strip() or stem[:3],
                title=fields.get("title", "").strip() or stem,
                status=fields.get("status", "").strip().upper(),
                roadmap_idea=fields.get("roadmap_idea", "").strip(),
                path=memory_dir / item.relative,
            )
        )
    return sorted(refs, key=TaskRef.number)


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in _UNESCAPED_PIPE_RE.split(line.strip().strip("|"))]


def idea_goals(roadmap: str) -> dict[str, str]:
    """Map each Idea Bank ID to its ``Goal`` column value.

    Args:
        roadmap: ``roadmap.md`` content.

    Returns:
        Idea ID to goal cell; empty when the section or the columns are missing.
    """
    section = _section(roadmap, r"Idea Bank")
    if section is None:
        return {}
    rows = [line for line in section.split("\n") if line.strip().startswith("|")]
    if not rows:
        return {}
    header = [cell.lower() for cell in _table_cells(rows[0])]
    if "id" not in header or "goal" not in header:
        return {}
    id_col, goal_col = header.index("id"), header.index("goal")
    goals: dict[str, str] = {}
    for row in rows[1:]:
        if _TABLE_SEPARATOR_RE.match(row.strip()):
            continue
        cells = _table_cells(row)
        if len(cells) > max(id_col, goal_col):
            goals[cells[id_col]] = cells[goal_col]
    return goals


def _arc_idea(memory_dir: Path, tasks: list[TaskRef], deliveries: list[LedgerEntry]) -> str:
    """``roadmap_idea`` of the newest IN_PROGRESS task, else of the newest delivered task."""
    in_progress = [task for task in tasks if task.status == IN_PROGRESS_STATUS]
    if in_progress:
        return in_progress[-1].roadmap_idea
    if not deliveries or not deliveries[0].task:
        return ""
    task_file = memory_dir / COMPLETED_DIR / f"{deliveries[0].task}.md"
    if not task_file.is_file():
        return ""
    return read_frontmatter(read_text(task_file)).get("roadmap_idea", "").strip()


def _arc_line(root: Path, idea: str, is_tty: bool) -> str | None:
    """``Arc: G1 — Lean context`` when idea → goal → goal heading all resolve, else None."""
    roadmap_path = root / MEMORY_DIR / ROADMAP
    if not idea or not roadmap_path.is_file():
        return None
    roadmap = read_text(roadmap_path)
    goal_id = idea_goals(roadmap).get(idea, "")
    if not _GOAL_ID_RE.match(goal_id):
        return None
    headings = dict(_GOAL_HEADING_RE.findall(roadmap))
    if goal_id not in headings:
        return None
    return f"{INDENT}Arc: " + _link(f"{goal_id} — {headings[goal_id]}", roadmap_path, root, is_tty)


def _task_line(task: TaskRef, root: Path, is_tty: bool, suffix: str = "") -> str:
    return INDENT + _link(f"{task.task_id} {task.title}{suffix}", task.path, root, is_tty)


def _where_we_are(root: Path, tasks: list[TaskRef], deliveries: list[LedgerEntry], is_tty: bool) -> list[str]:
    lines: list[str] = []
    arc = _arc_line(root, _arc_idea(root / MEMORY_DIR, tasks, deliveries), is_tty)
    if arc:
        lines.append(arc)
    for task in tasks:
        if task.status == IN_PROGRESS_STATUS:
            lines.append(_task_line(task, root, is_tty, suffix=" (in progress)"))
    return lines


def _story(root: Path, deliveries: list[LedgerEntry], is_tty: bool) -> list[str]:
    folder = root / MEMORY_DIR / LEDGER_DIR / "deliveries"
    lines: list[str] = []
    for entry in deliveries[:STORY_DELIVERIES]:
        month_day = entry.date[5:] if len(entry.date) >= len("YYYY-MM-DD") else "--   "
        lines.append(f"{INDENT}{month_day}  " + _link(entry.title, folder / entry.filename, root, is_tty))
        if entry.why:
            lines.append(f"{WHY_INDENT}why: {_cap(' '.join(entry.why.split()), WHY_MAX_CHARS)}")
    return lines


def _waiting(root: Path, today: date, tasks: list[TaskRef], is_tty: bool) -> list[str]:
    lines = [
        _task_line(task, root, is_tty, suffix=f" — in REVIEW: run {HARVEST_COMMAND}")
        for task in tasks
        if task.status == REVIEW_STATUS
    ]
    check = check_open_tasks(root, today)
    if check is not None:
        lines += [f"{INDENT}{problem}" for problem in check.problems]
    return lines


def _next_step(memory_dir: Path) -> list[str]:
    progress = memory_dir / PROGRESS
    lines: list[str] = []
    if progress.is_file():
        state = _section(read_text(progress), r"Current state") or ""
        bullet = _NEXT_BULLET_RE.search(state)
        if bullet:
            lines.append(f"{INDENT}Next: {bullet.group(1)}")
    lines.append(f"{INDENT}Hint: ask the agent to run {HARVEST_COMMAND} to record a next step")
    return lines


def build_brief(root: Path, today: date, git: GitState | None, is_tty: bool) -> str:
    """Render the pilot brief.

    Args:
        root: Project root that contains ``docs/memory/``.
        today: Date shown in the header and used for open-task age checks.
        git: Working-tree state, or ``None`` outside git.
        is_tty: True when stdout is a terminal (OSC 8 links instead of plain paths).

    Returns:
        The brief text (ends with a newline).
    """
    memory_dir = root / MEMORY_DIR
    tasks = _task_refs(memory_dir, collect_files(memory_dir))
    deliveries = collect_entries(memory_dir, "deliveries")
    sections = (
        ("WHERE WE ARE", _where_we_are(root, tasks, deliveries, is_tty)),
        ("RECENT STORY", _story(root, deliveries, is_tty)),
        ("WAITING ON YOU", _waiting(root, today, tasks, is_tty)),
        ("NEXT STEP", _next_step(memory_dir)),
    )
    lines = [_header(root, today, git)]
    for heading, body in sections:
        lines += ["", heading] + (body or [EMPTY_SECTION])
    return "\n".join(lines) + "\n"


def run_brief(project_root: str | None) -> int:
    """Run ``spine.py brief``.

    Args:
        project_root: ``--project-root`` value, or None for the git toplevel.

    Returns:
        Process exit code: 0, or 1 when the root or ``docs/memory/`` is missing.
    """
    try:
        root = resolve_project_root(project_root)
    except SpineExit as exc:
        return exc.code
    if not (root / MEMORY_DIR).is_dir():
        sys.stderr.write(
            f"ERROR: no memory bank at {MEMORY_DIR.as_posix()}/ — run `{INSTALL_HINT}` to set up Spine.\n"
        )
        return 1
    sys.stdout.write(build_brief(root, date.today(), read_git_state(root), sys.stdout.isatty()))
    return 0
