"""Memory bank digest and stats (``spine.py memory stats|digest``).

The digest is a compact, deterministic view of ``docs/memory/`` that replaces
loading every global file, the whole ``progress.md`` and every open task body
at Core SYNC. Standard library only, Python 3.9+.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from spine_cli.log import SpineExit
from spine_cli.paths import resolve_project_root

# File kinds -------------------------------------------------------------------
NARRATIVE = "narrative"
LOG = "log"
TASK = "task"
EXTENDED = "extended"
IGNORED = "ignored"

MEMORY_DIR = Path("docs") / "memory"
LOG_FILES = frozenset({"global/decision-log.md", "ledger/progress.md", "ledger/learnings.md"})
EXTENDED_FILES = frozenset({"ledger/roadmap.md"})
NARRATIVE_DIRS = ("global", "ledger")
TASK_FILE_RE = re.compile(r"^\d{3}-.+\.md$")
SCANNED_DIRS = ("global", "ledger", "active_tasks")
COMPLETED_DIR = "completed_tasks"
CORE_NARRATIVE_ORDER = (
    "global/project-brief.md",
    "global/product-context.md",
    "global/domain-glossary.md",
    "global/system-patterns.md",
    "global/tech-context.md",
)

# Digest limits ------------------------------------------------------------------
NEWEST_LOG_TITLES = 5
OUTLINE_MAX_CHARS = 600
SUMMARY_MAX_CHARS = 800
LOG_TITLE_MAX_CHARS = 160
TASK_LINE_MAX_CHARS = 320
DEFAULT_SETUP_BUDGET_CHARS = 60_000
SUMMARY_MAX_LINES = 5
ELLIPSIS = "…"
OPEN_STATUS_RANK = {"IN_PROGRESS": 0, "REVIEW": 1}
OTHER_STATUS_RANK = 2
CLOSED_STATUS = "DONE"
UNKNOWN_STATUS = "UNKNOWN"

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---[ \t]*(?:\n|\Z)", re.DOTALL)
_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*(.*?)[ \t]*$")
_BLOCK_INDICATOR_RE = re.compile(r"^[>|][+-]?$")


def read_text(path: Path) -> str:
    """Read a UTF-8 text file (BOM tolerated) with newlines normalized to LF.

    Args:
        path: File to read.

    Returns:
        File content using ``\\n`` line endings.
    """
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def _block_value(indicator: str, lines: list[str]) -> str:
    stripped = [line.strip() for line in lines]
    while stripped and not stripped[-1]:
        stripped.pop()
    if indicator.startswith("|"):
        return "\n".join(stripped)
    return " ".join(line for line in stripped if line)


def read_frontmatter(text: str) -> dict[str, str]:
    """Parse top-level scalar fields of a YAML frontmatter block.

    Supports plain and quoted scalars and ``>``/``|`` block scalars. List items
    and nested mappings are skipped: their key maps to an empty string.

    Args:
        text: Full file content (LF newlines).

    Returns:
        Field name to string value. Empty when there is no closed frontmatter.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    lines = match.group(1).split("\n")
    index = 0
    while index < len(lines):
        key_match = _KEY_RE.match(lines[index])
        index += 1
        if not key_match:
            continue
        key, value = key_match.group(1), key_match.group(2)
        if _BLOCK_INDICATOR_RE.match(value):
            block: list[str] = []
            while index < len(lines) and (not lines[index].strip() or lines[index][0] in " \t"):
                block.append(lines[index])
                index += 1
            fields[key] = _block_value(value, block)
        else:
            fields[key] = _unquote(value)
    return fields


def strip_frontmatter(text: str) -> str:
    """Return ``text`` without its leading frontmatter block, if any.

    Args:
        text: Full file content (LF newlines).

    Returns:
        The body after the closing ``---`` line, or ``text`` unchanged.
    """
    match = _FRONTMATTER_RE.match(text)
    return text[match.end():] if match else text


def classify(relative: str) -> str:
    """Classify a memory bank file by its path relative to ``docs/memory/``.

    Args:
        relative: POSIX path such as ``global/project-brief.md``.

    Returns:
        One of ``NARRATIVE``, ``LOG``, ``TASK``, ``EXTENDED`` or ``IGNORED``.
    """
    if not relative.endswith(".md"):
        return IGNORED
    if relative in LOG_FILES:
        return LOG
    if relative in EXTENDED_FILES:
        return EXTENDED
    parts = relative.split("/")
    if len(parts) != 2:
        return IGNORED
    folder, name = parts
    if folder == "active_tasks":
        return TASK if TASK_FILE_RE.match(name) else IGNORED
    if folder in NARRATIVE_DIRS:
        return NARRATIVE
    return IGNORED


# =============================================================================
# Memory bank scan
# =============================================================================


@dataclass(frozen=True)
class MemoryFile:
    """One Markdown file of the memory bank.

    Args:
        relative: POSIX path relative to ``docs/memory/``.
        kind: Result of :func:`classify`.
        text: File content (LF newlines, BOM stripped).
    """

    relative: str
    kind: str
    text: str

    @property
    def chars(self) -> int:
        """Character count of the file content."""
        return len(self.text)


def collect_files(memory_dir: Path) -> list[MemoryFile]:
    """Read every classified Markdown file under the scanned memory folders.

    Args:
        memory_dir: The ``docs/memory/`` directory.

    Returns:
        Files sorted by relative path; ignored files are left out.
    """
    files: list[MemoryFile] = []
    for folder in SCANNED_DIRS:
        directory = memory_dir / folder
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            relative = f"{folder}/{path.name}"
            kind = classify(relative)
            if kind == IGNORED or not path.is_file():
                continue
            files.append(MemoryFile(relative, kind, read_text(path)))
    return files


def _cap(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - len(ELLIPSIS)].rstrip() + ELLIPSIS


def _section(text: str, heading_re: str) -> str | None:
    """Return the body of the first ``## `` section whose heading matches."""
    match = re.search(rf"^##[ \t]+{heading_re}[^\n]*$", text, flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    rest = text[match.end():]
    end = re.search(r"^##[ \t]", rest, flags=re.MULTILINE)
    return rest[: end.start()] if end else rest


# =============================================================================
# Open tasks
# =============================================================================


@dataclass(frozen=True)
class TaskLine:
    """Digest view of one open task (frontmatter only)."""

    task_id: str
    status: str
    title: str
    goal: str

    def render(self) -> str:
        """Return ``NNN | STATUS | title — goal`` capped to one line."""
        head = f"{self.task_id} | {self.status} | {self.title}"
        line = f"{head} — {self.goal}" if self.goal else head
        return _cap(" ".join(line.split()), TASK_LINE_MAX_CHARS)

    def sort_key(self) -> tuple[int, int, str]:
        """IN_PROGRESS, then REVIEW, then the rest; each group by task id."""
        rank = OPEN_STATUS_RANK.get(self.status, OTHER_STATUS_RANK)
        number = int(self.task_id) if self.task_id.isdigit() else 0
        return (rank, number, self.task_id)


def open_tasks(files: list[MemoryFile]) -> list[TaskLine]:
    """Build task lines for open tasks, ordered for the digest.

    Args:
        files: Scanned memory files.

    Returns:
        Task lines without ``DONE`` tasks, IN_PROGRESS/REVIEW first, then by id.
    """
    tasks: list[TaskLine] = []
    for item in files:
        if item.kind != TASK:
            continue
        fields = read_frontmatter(item.text)
        status = fields.get("status", "").strip().upper() or UNKNOWN_STATUS
        if status == CLOSED_STATUS:
            continue
        stem = item.relative.rsplit("/", 1)[1][: -len(".md")]
        tasks.append(
            TaskLine(
                task_id=fields.get("task_id", "").strip() or stem[:3],
                status=status,
                title=fields.get("title", "").strip() or stem,
                goal=fields.get("goal", "").strip(),
            )
        )
    return sorted(tasks, key=TaskLine.sort_key)


# =============================================================================
# Narrative files
# =============================================================================

_PLACEHOLDER_SUMMARY_RE = re.compile(r"^\[fill in", re.IGNORECASE)
_H2_RE = re.compile(r"^##[ \t]+(.+?)[ \t#]*$", re.MULTILINE)


def narrative_summary(text: str) -> str | None:
    """Return the agent-written ``summary:`` or None when missing or a placeholder.

    Args:
        text: Narrative file content.

    Returns:
        The summary text, or None.
    """
    summary = read_frontmatter(text).get("summary", "").strip()
    if not summary or _PLACEHOLDER_SUMMARY_RE.match(summary):
        return None
    return summary


def outline(text: str) -> str:
    """Return the file's ``##`` headings joined and capped at ``OUTLINE_MAX_CHARS``.

    Args:
        text: Narrative file content.

    Returns:
        ``A; B; C`` or ``(no ## headings)``.
    """
    headings = _H2_RE.findall(strip_frontmatter(text))
    if not headings:
        return "(no ## headings)"
    return _cap("; ".join(headings), OUTLINE_MAX_CHARS)


def _narrative_order(item: MemoryFile) -> tuple[int, str]:
    if item.relative in CORE_NARRATIVE_ORDER:
        return (CORE_NARRATIVE_ORDER.index(item.relative), item.relative)
    return (len(CORE_NARRATIVE_ORDER), item.relative)


def _render_narrative(item: MemoryFile) -> list[str]:
    summary = narrative_summary(item.text)
    if summary is None:
        return [
            f"### {item.relative} ({item.chars:,} chars) — summary missing",
            f"Outline: {outline(item.text)}",
        ]
    return [f"### {item.relative} ({item.chars:,} chars)", _cap(summary, SUMMARY_MAX_CHARS)]


# =============================================================================
# Log files
# =============================================================================

_PLACEHOLDER_ENTRY_RE = re.compile(r"\[DATE\]|\[TITLE\]|YYYY-MM-DD")
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_LEARN_ID_RE = re.compile(r"LEARN-(\d+)")
_H3_RE = re.compile(r"^###[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_LEARN_HEADING_RE = re.compile(r"^#{2,3}[ \t]+(LEARN-\d+.*?)[ \t]*$", re.MULTILINE)
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?$")


def _table_rows(text: str) -> list[str]:
    """Return ``cell1 — cell2`` for each data row of the first Markdown table."""
    rows: list[str] = []
    in_table = False
    header_seen = False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue
        in_table = True
        if not header_seen:
            header_seen = True
            continue
        if _TABLE_SEPARATOR_RE.match(stripped):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|") if cell.strip()]
        rows.append(" — ".join(cells[:2]))
    return rows


def _order_key(title: str) -> str:
    date = _ISO_DATE_RE.search(title)
    if date:
        return date.group(0)
    learn = _LEARN_ID_RE.search(title)
    return f"{int(learn.group(1)):09d}" if learn else ""


def newest_first(titles: list[str]) -> list[str]:
    """Order log entry titles newest first.

    When every title carries a date (or a ``LEARN-NNN`` id), entries are sorted
    by it; ties keep the file's own direction. Otherwise the file is assumed to
    be newest first already.

    Args:
        titles: Entry titles in file order.

    Returns:
        Titles, newest first.
    """
    keys = [_order_key(title) for title in titles]
    if len(titles) < 2 or not all(keys):
        return list(titles)
    chronological = keys[0] < keys[-1]
    order = sorted(
        range(len(titles)),
        key=lambda index: (keys[index], index if chronological else -index),
        reverse=True,
    )
    return [titles[index] for index in order]


def log_entries(relative: str, text: str) -> list[str]:
    """Extract log entry titles from a log file, newest first.

    Args:
        relative: Path relative to ``docs/memory/`` (selects the format).
        text: File content.

    Returns:
        Entry titles, placeholders removed, newest first.
    """
    if relative == "ledger/progress.md":
        titles = _H3_RE.findall(_section(text, r"Delivery log") or "")
    elif relative == "ledger/learnings.md":
        titles = _LEARN_HEADING_RE.findall(text)
    else:
        titles = _H3_RE.findall(text) or _table_rows(text)
    titles = [title for title in titles if not _PLACEHOLDER_ENTRY_RE.search(title)]
    return newest_first(titles)


LEGACY_LABEL = "(legacy file, frozen until migrate)"


def _noun(count: int) -> str:
    return "entry" if count == 1 else "entries"


def _render_log(item: MemoryFile) -> list[str]:
    """Render a legacy single log file; ``progress.md`` only when it still has a delivery log."""
    is_progress = item.relative == "ledger/progress.md"
    if is_progress and _section(item.text, r"Delivery log") is None:
        return []
    entries = log_entries(item.relative, item.text)
    label = f"{item.relative} delivery log" if is_progress else item.relative
    if not entries:
        return [f"- {label}: 0 entries {LEGACY_LABEL}"]
    lines = [f"- {label}: {len(entries)} {_noun(len(entries))} {LEGACY_LABEL}; newest:"]
    lines.extend(f"  - {_cap(title, LOG_TITLE_MAX_CHARS)}" for title in entries[:NEWEST_LOG_TITLES])
    return lines


# =============================================================================
# Ledger entries (ledger/<folder>/<entry>.md + generated INDEX.md)
# =============================================================================

LEDGER_DIR = "ledger"
LEDGER_FOLDERS = ("decisions", "learnings", "deliveries")
INDEX_NAME = "INDEX.md"
TEMPLATE_PREFIX = "_"
ENTRY_SUMMARY_MAX_CHARS = 160

_RECURRENCES_RE = re.compile(r"^\*\*Recurrences:\*\*[ \t]*$", re.MULTILINE)
_RECURRENCE_PLACEHOLDER_RE = re.compile(r"^-[ \t]+\(")


def read_frontmatter_list(text: str, key: str) -> list[str]:
    """Return a frontmatter list field (block ``- item`` list, ``[a, b]`` or a scalar).

    Args:
        text: Full file content (LF newlines).
        key: Top-level frontmatter key, e.g. ``tags``.

    Returns:
        The items in order; empty when the key or the frontmatter is missing.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return []
    lines = match.group(1).split("\n")
    for index, line in enumerate(lines):
        key_match = _KEY_RE.match(line)
        if not key_match or key_match.group(1) != key:
            continue
        value = key_match.group(2)
        if value.startswith("[") and value.endswith("]"):
            return [_unquote(item.strip()) for item in value[1:-1].split(",") if item.strip()]
        if value:
            return [_unquote(value)]
        items: list[str] = []
        for following in lines[index + 1:]:
            stripped = following.strip()
            if stripped.startswith("- "):
                items.append(_unquote(stripped[2:].strip()))
            elif stripped:
                break
        return items
    return []


def _count_recurrences(text: str) -> int:
    match = _RECURRENCES_RE.search(text)
    if not match:
        return 0
    count = 0
    for line in text[match.end():].split("\n"):
        stripped = line.strip()
        if not stripped:
            if count:
                break
            continue
        if not stripped.startswith("- "):
            break
        if not _RECURRENCE_PLACEHOLDER_RE.match(stripped):
            count += 1
    return count


@dataclass(frozen=True)
class LedgerEntry:
    """One entry file of a ledger folder (frontmatter view).

    Args:
        filename: File name inside the folder.
        entry_id: ``id:`` (falls back to the file stem).
        date: ``date:`` (ISO ``YYYY-MM-DD``; empty when missing).
        title: ``title:`` (falls back to the file stem).
        summary: ``summary:`` one-liner (empty when missing).
        tags: ``tags:`` items.
        task: ``task:`` (``NNN-slug``; empty when none).
        superseded_by: ``superseded_by:`` id of the replacing decision.
        recurrences: Items under ``**Recurrences:**`` (learnings).
    """

    filename: str
    entry_id: str
    date: str
    title: str
    summary: str
    tags: tuple[str, ...]
    task: str
    superseded_by: str
    recurrences: int


def _is_entry_file(path: Path) -> bool:
    return path.is_file() and path.suffix == ".md" and path.name != INDEX_NAME and not path.name.startswith(TEMPLATE_PREFIX)


def read_entry(path: Path) -> LedgerEntry:
    """Read one ledger entry file.

    Args:
        path: Entry Markdown file.

    Returns:
        The entry's frontmatter view.
    """
    text = read_text(path)
    fields = read_frontmatter(text)
    stem = path.stem
    return LedgerEntry(
        filename=path.name,
        entry_id=fields.get("id", "").strip() or stem,
        date=fields.get("date", "").strip(),
        title=fields.get("title", "").strip() or stem,
        summary=fields.get("summary", "").strip(),
        tags=tuple(read_frontmatter_list(text, "tags")),
        task=fields.get("task", "").strip(),
        superseded_by=fields.get("superseded_by", "").strip(),
        recurrences=_count_recurrences(strip_frontmatter(text)),
    )


def collect_entries(memory_dir: Path, folder: str) -> list[LedgerEntry]:
    """Read every entry of ``ledger/<folder>/``, newest first.

    ``INDEX.md``, ``_``-prefixed templates and non-Markdown files are skipped.

    Args:
        memory_dir: The ``docs/memory/`` directory.
        folder: One of ``LEDGER_FOLDERS``.

    Returns:
        Entries sorted by date, then id, newest first; empty when the folder is missing.
    """
    directory = memory_dir / LEDGER_DIR / folder
    if not directory.is_dir():
        return []
    entries = [read_entry(path) for path in directory.iterdir() if _is_entry_file(path)]
    return sorted(entries, key=lambda entry: (entry.date, entry.entry_id), reverse=True)


def _render_ledger_folders(memory_dir: Path) -> list[str]:
    """Render one digest block per existing ledger folder (count + newest titles)."""
    lines: list[str] = []
    for folder in LEDGER_FOLDERS:
        if not (memory_dir / LEDGER_DIR / folder).is_dir():
            continue
        entries = collect_entries(memory_dir, folder)
        label = f"- {LEDGER_DIR}/{folder}/: {len(entries)} {_noun(len(entries))}"
        if not entries:
            lines.append(label)
            continue
        superseded = sum(1 for entry in entries if entry.superseded_by)
        if superseded:
            label += f" ({superseded} superseded)"
        lines.append(f"{label}, see {INDEX_NAME}; newest:")
        for entry in entries[:NEWEST_LOG_TITLES]:
            head = entry.entry_id if folder == "learnings" else entry.date
            lines.append(f"  - {_cap(f'{head} — {entry.title}', LOG_TITLE_MAX_CHARS)}")
    return lines


INDEX_NOTE = "Generated by `spine.py memory index` from entry frontmatter, newest first. Do not edit by hand."
INDEX_HEADINGS = {"decisions": "Decisions", "learnings": "Learnings", "deliveries": "Deliveries"}
INDEX_COLUMNS = {
    "decisions": ("Date", "Decision", "Status", "Tags", "Summary"),
    "learnings": ("ID", "Title", "Tags", "Recurrences", "Summary"),
    "deliveries": ("Date", "Delivery", "Task", "Tags", "Summary"),
}
ACTIVE_STATUS = "active"


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")


def _index_row(folder: str, entry: LedgerEntry) -> tuple[str, ...]:
    link = f"[{_cell(entry.title)}]({entry.filename})"
    tags = _cell(", ".join(entry.tags))
    summary = _cell(entry.summary)
    if folder == "decisions":
        target = entry.superseded_by
        status = f"superseded by [{_cell(target)}]({target}.md)" if target else ACTIVE_STATUS
        return (entry.date, link, status, tags, summary)
    if folder == "learnings":
        return (_cell(entry.entry_id), link, tags, str(entry.recurrences), summary)
    return (entry.date, link, _cell(entry.task), tags, summary)


def render_index(folder: str, entries: list[LedgerEntry]) -> str:
    """Render ``INDEX.md`` for one ledger folder.

    Args:
        folder: One of ``LEDGER_FOLDERS``.
        entries: Entries as returned by :func:`collect_entries` (newest first).

    Returns:
        Markdown with a heading, a do-not-edit note and one table row per entry.
    """
    columns = INDEX_COLUMNS[folder]
    lines = [
        f"# {INDEX_HEADINGS[folder]}",
        "",
        INDEX_NOTE,
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "---|" * len(columns),
    ]
    lines += ["| " + " | ".join(_index_row(folder, entry)) + " |" for entry in entries]
    return "\n".join(lines) + "\n"


def index_path(memory_dir: Path, folder: str) -> Path:
    """Return ``docs/memory/ledger/<folder>/INDEX.md``."""
    return memory_dir / LEDGER_DIR / folder / INDEX_NAME


def write_indexes(root: Path) -> list[Path]:
    """Regenerate ``INDEX.md`` in every existing ledger folder.

    Args:
        root: Project root that contains ``docs/memory/``.

    Returns:
        Index files whose content changed (missing folders are skipped, never created).
    """
    memory_dir = root / MEMORY_DIR
    written: list[Path] = []
    for folder in LEDGER_FOLDERS:
        path = index_path(memory_dir, folder)
        if not path.parent.is_dir():
            continue
        content = render_index(folder, collect_entries(memory_dir, folder))
        if path.is_file() and read_text(path) == content:
            continue
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


# =============================================================================
# SETUP selection
# =============================================================================


@dataclass(frozen=True)
class SetupCandidate:
    """A narrative file that still needs an agent-written ``summary:``."""

    relative: str
    chars: int


def select_setup(candidates: list[SetupCandidate], budget: int) -> tuple[list[SetupCandidate], int]:
    """Pick files to summarize this session, largest first, within ``budget``.

    Files that would push the cumulative size over ``budget`` are skipped and
    smaller ones are still tried. When none fits, the largest file is selected
    alone so the setup always makes progress.

    Args:
        candidates: Narrative files without a summary.
        budget: Maximum cumulative source chars to summarize this session.

    Returns:
        Selected files (largest first) and the number of deferred files.
    """
    ordered = sorted(candidates, key=lambda item: (-item.chars, item.relative))
    selected: list[SetupCandidate] = []
    total = 0
    for item in ordered:
        if total + item.chars <= budget:
            selected.append(item)
            total += item.chars
    if not selected and ordered:
        selected = [ordered[0]]
    return selected, len(ordered) - len(selected)


def _render_setup(selected: list[SetupCandidate], deferred: int, budget: int) -> list[str]:
    missing = len(selected) + deferred
    lines = [
        f"SETUP: {missing} narrative file(s) have no `summary:` frontmatter field.",
        f"Before the task, write `summary:` (at most {SUMMARY_MAX_LINES} lines: what the file holds and "
        "when to open it) in the YAML frontmatter of these files only:",
    ]
    lines.extend(f"- {MEMORY_DIR.as_posix()}/{item.relative} ({item.chars:,} chars)" for item in selected)
    if deferred:
        lines.append(
            f"Deferred to later sessions: {deferred} file(s) (session budget {budget:,} chars). "
            "Do not summarize them now."
        )
    return lines


# =============================================================================
# Digest
# =============================================================================


def build_digest(root: Path, budget: int = DEFAULT_SETUP_BUDGET_CHARS) -> str:
    """Render the memory digest for a project.

    Args:
        root: Project root that contains ``docs/memory/``.
        budget: SETUP source budget in chars.

    Returns:
        The digest text (ends with a newline).
    """
    memory_dir = root / MEMORY_DIR
    if not memory_dir.is_dir():
        return f"No memory bank at {MEMORY_DIR.as_posix()}/ — nothing to sync.\n"
    files = collect_files(memory_dir)
    by_relative = {item.relative: item for item in files}

    lines = [
        "# Memory digest",
        "",
        "Generated by `spine.py memory digest`. Open a full file only when the task needs it.",
        "",
        "## Current state",
    ]
    progress = by_relative.get("ledger/progress.md")
    state = _section(progress.text, r"Current state") if progress else None
    lines.append(state.strip() if state and state.strip() else "(progress.md has no `## Current state` section)")

    lines += ["", "## Open tasks"]
    tasks = open_tasks(files)
    lines += [task.render() for task in tasks] or ["(none)"]

    lines += ["", "## Narrative files"]
    narratives = sorted((item for item in files if item.kind == NARRATIVE), key=_narrative_order)
    for item in narratives:
        lines += _render_narrative(item) + [""]
    if not narratives:
        lines += ["(none)", ""]

    lines.append("## Logs")
    log_lines = _render_ledger_folders(memory_dir)
    for item in files:
        if item.kind == LOG:
            log_lines += _render_log(item)
    lines += log_lines or ["(none)"]

    lines += ["", "## Extended tier (read when planning, harvesting or when scope is ambiguous)"]
    for item in files:
        if item.kind == EXTENDED:
            lines.append(f"- {item.relative} ({item.chars:,} chars)")
    completed = memory_dir / COMPLETED_DIR
    if completed.is_dir():
        count = sum(1 for path in completed.glob("*.md") if TASK_FILE_RE.match(path.name))
        lines.append(f"- {COMPLETED_DIR}/: {count} task file(s), on demand")

    candidates = [
        SetupCandidate(item.relative, item.chars) for item in narratives if narrative_summary(item.text) is None
    ]
    if candidates:
        selected, deferred = select_setup(candidates, budget)
        lines += [""] + _render_setup(selected, deferred, budget)
    return "\n".join(lines) + "\n"


# =============================================================================
# Stats
# =============================================================================

CHARS_PER_TOKEN = 4
PERCENT = 100


@dataclass(frozen=True)
class MemoryStats:
    """Char counts that make the digest gain measurable.

    Args:
        files: ``(relative, kind, chars)`` for each scanned memory file.
        legacy_core_chars: Global files + whole ``progress.md`` + open task files.
        digest_chars: Size of :func:`build_digest` output.
        completed_files: Number of ``completed_tasks/`` task files.
        completed_chars: Total chars of ``completed_tasks/`` task files.
    """

    files: list[tuple[str, str, int]]
    legacy_core_chars: int
    digest_chars: int
    completed_files: int
    completed_chars: int


def _in_legacy_core(item: MemoryFile) -> bool:
    if item.relative.startswith("global/") or item.relative == "ledger/progress.md":
        return True
    if item.kind != TASK:
        return False
    return read_frontmatter(item.text).get("status", "").strip().upper() != CLOSED_STATUS


def collect_stats(root: Path, budget: int = DEFAULT_SETUP_BUDGET_CHARS) -> MemoryStats:
    """Measure the legacy Core SYNC load and the digest size for a project.

    Args:
        root: Project root that contains ``docs/memory/``.
        budget: SETUP source budget passed to the digest.

    Returns:
        The measured stats (all zero when there is no memory bank).
    """
    memory_dir = root / MEMORY_DIR
    files = collect_files(memory_dir) if memory_dir.is_dir() else []
    completed = memory_dir / COMPLETED_DIR
    completed_paths = (
        [path for path in completed.glob("*.md") if TASK_FILE_RE.match(path.name)] if completed.is_dir() else []
    )
    return MemoryStats(
        files=[(item.relative, item.kind, item.chars) for item in files],
        legacy_core_chars=sum(item.chars for item in files if _in_legacy_core(item)),
        digest_chars=len(build_digest(root, budget)),
        completed_files=len(completed_paths),
        completed_chars=sum(len(read_text(path)) for path in completed_paths),
    )


def _tokens(chars: int) -> str:
    return f"≈ {chars // CHARS_PER_TOKEN:,} tokens"


def render_stats(stats: MemoryStats) -> str:
    """Format stats as a plain-text report.

    Args:
        stats: Result of :func:`collect_stats`.

    Returns:
        Report text ending with a newline.
    """
    width = max([len(f"{chars:,}") for _, _, chars in stats.files] + [len(f"{stats.legacy_core_chars:,}")])
    lines = [f"Memory bank: {MEMORY_DIR.as_posix()}/", ""]
    lines += [f"  {chars:>{width},}  {kind:<9}  {relative}" for relative, kind, chars in stats.files]
    if stats.completed_files:
        lines.append(
            f"  {stats.completed_chars:>{width},}  {'on-demand':<9}  "
            f"{COMPLETED_DIR}/ ({stats.completed_files} files)"
        )
    lines += [
        "",
        f"Legacy Core SYNC: {stats.legacy_core_chars:,} chars ({_tokens(stats.legacy_core_chars)})"
        " — global/ + whole progress.md + open task files",
        f"Digest:           {stats.digest_chars:,} chars ({_tokens(stats.digest_chars)})",
    ]
    if stats.legacy_core_chars:
        saved = PERCENT - stats.digest_chars * PERCENT // stats.legacy_core_chars
        lines.append(f"Reduction:        {saved}%")
    return "\n".join(lines) + "\n"


def run_memory(action: str, project_root: str | None, budget: int) -> int:
    """Run ``spine.py memory <action>``.

    Args:
        action: ``stats``, ``digest`` or ``index``.
        project_root: ``--project-root`` value, or None for the git toplevel.
        budget: SETUP source budget in chars.

    Returns:
        Process exit code.
    """
    try:
        root = resolve_project_root(project_root)
    except SpineExit as exc:
        return exc.code
    if action == "stats":
        sys.stdout.write(render_stats(collect_stats(root, budget)))
    elif action == "index":
        written = write_indexes(root)
        for path in written:
            sys.stdout.write(f"Updated: {path.relative_to(root).as_posix()}\n")
        if not written:
            sys.stdout.write("Ledger INDEX.md files are up to date.\n")
    else:
        sys.stdout.write(build_digest(root, budget))
    return 0


# =============================================================================
# Budgets (read by ``spine_validate.py memory``; never shown in the digest)
# =============================================================================

DIGEST_BUDGET_CHARS = 8_000
CURRENT_STATE_BUDGET_CHARS = 1_500
NARRATIVE_BODY_BUDGET_CHARS = 3_000
LOG_BUDGET_CHARS = {
    "global/decision-log.md": 5_000,
    "ledger/progress.md": 6_000,
    "ledger/learnings.md": 6_000,
}
DIGEST_SCOPE = "memory digest (Core SYNC)"
CURRENT_STATE_SCOPE = f"{MEMORY_DIR.as_posix()}/ledger/progress.md § Current state"
CURRENT_STATE_HINT = "compact Current state at /spine-harvest"
LOG_HINT = "legacy file, frozen — split it into ledger entries with spine.py memory migrate (roadmap I25)"
NARRATIVE_HINT = "split or trim with human approval"
SETUP_LABEL = "SETUP"

_DIGEST_SECTION_RE = re.compile(r"^(?:##[ \t]+(.+?)|(SETUP):.*)$", re.MULTILINE)


@dataclass(frozen=True)
class BudgetCheck:
    """One memory scope measured against its budget.

    Args:
        scope: What was measured (a path under ``docs/memory/`` or the digest).
        chars: Measured size in chars.
        limit: Budget in chars.
        detail: Remedy hint; for the digest, its section sizes largest first.
    """

    scope: str
    chars: int
    limit: int
    detail: str

    @property
    def over(self) -> bool:
        """True when ``chars`` exceeds ``limit``."""
        return self.chars > self.limit


def digest_section_sizes(digest: str) -> list[tuple[str, int]]:
    """Measure each ``##`` section (and the ``SETUP:`` block) of a digest.

    Args:
        digest: Output of :func:`build_digest`.

    Returns:
        ``(label, chars)`` pairs, largest first. Labels drop trailing
        parentheticals (``Extended tier (read when…)`` → ``Extended tier``).
    """
    matches = list(_DIGEST_SECTION_RE.finditer(digest))
    sizes: list[tuple[str, int]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(digest)
        label = (match.group(1) or match.group(2)).split(" (", 1)[0].strip()
        sizes.append((label, len(digest[match.start():end].rstrip("\n"))))
    return sorted(sizes, key=lambda item: -item[1])


def _digest_detail(digest: str) -> str:
    sizes = digest_section_sizes(digest)
    return "largest sections: " + "; ".join(f"{label} {chars:,}" for label, chars in sizes)


def check_budgets(root: Path) -> list[BudgetCheck]:
    """Measure the memory bank against the digest-first budgets.

    Budgeted scopes: the digest total, the ``progress.md`` Current state block,
    each narrative file body (frontmatter excluded) and the three log files.
    Task files, ``roadmap.md`` and ``completed_tasks/`` are not budgeted;
    missing files are skipped.

    Args:
        root: Project root that contains ``docs/memory/``.

    Returns:
        One check per measured scope (digest first, then files by path), or an
        empty list when ``docs/memory/`` does not exist.
    """
    memory_dir = root / MEMORY_DIR
    if not memory_dir.is_dir():
        return []
    digest = build_digest(root)
    checks = [BudgetCheck(DIGEST_SCOPE, len(digest), DIGEST_BUDGET_CHARS, _digest_detail(digest))]
    for item in collect_files(memory_dir):
        scope = f"{MEMORY_DIR.as_posix()}/{item.relative}"
        if item.relative == "ledger/progress.md":
            state = (_section(item.text, r"Current state") or "").strip()
            checks.append(BudgetCheck(CURRENT_STATE_SCOPE, len(state), CURRENT_STATE_BUDGET_CHARS, CURRENT_STATE_HINT))
        if item.relative in LOG_BUDGET_CHARS:
            checks.append(BudgetCheck(scope, item.chars, LOG_BUDGET_CHARS[item.relative], LOG_HINT))
        elif item.kind == NARRATIVE:
            body = len(strip_frontmatter(item.text))
            checks.append(BudgetCheck(scope, body, NARRATIVE_BODY_BUDGET_CHARS, NARRATIVE_HINT))
    return checks


# =============================================================================
# Ledger checks (read by ``spine_validate.py memory``)
# =============================================================================

INDEX_CMD = "python3 .spine/scripts/spine.py memory index"
PROBLEM_FILES_SHOWN = 5


@dataclass(frozen=True)
class LedgerCheck:
    """Health of one ledger folder.

    Args:
        scope: Folder path such as ``docs/memory/ledger/decisions/``.
        entries: Number of entry files.
        problems: One message per problem kind (empty when healthy).
    """

    scope: str
    entries: int
    problems: tuple[str, ...]


def _file_list(entries: list[LedgerEntry]) -> str:
    names = [entry.filename for entry in entries[:PROBLEM_FILES_SHOWN]]
    more = len(entries) - len(names)
    return ", ".join(names) + (f" (+{more} more)" if more else "")


def check_ledger(root: Path) -> list[LedgerCheck]:
    """Check entry summaries and INDEX.md freshness in every existing ledger folder.

    Args:
        root: Project root that contains ``docs/memory/``.

    Returns:
        One check per existing ledger folder, in ``LEDGER_FOLDERS`` order.
    """
    memory_dir = root / MEMORY_DIR
    checks: list[LedgerCheck] = []
    for folder in LEDGER_FOLDERS:
        path = index_path(memory_dir, folder)
        if not path.parent.is_dir():
            continue
        entries = collect_entries(memory_dir, folder)
        problems: list[str] = []
        missing = [entry for entry in entries if not entry.summary]
        if missing:
            problems.append(f"{len(missing)} {_noun(len(missing))} without `summary:` — {_file_list(missing)}")
        long = [entry for entry in entries if len(entry.summary) > ENTRY_SUMMARY_MAX_CHARS]
        if long:
            problems.append(f"{len(long)} `summary:` over {ENTRY_SUMMARY_MAX_CHARS} chars — {_file_list(long)}")
        if not path.is_file():
            problems.append(f"{INDEX_NAME} missing — run {INDEX_CMD}")
        elif read_text(path) != render_index(folder, entries):
            problems.append(f"{INDEX_NAME} is stale — run {INDEX_CMD}")
        scope = f"{MEMORY_DIR.as_posix()}/{LEDGER_DIR}/{folder}/"
        checks.append(LedgerCheck(scope, len(entries), tuple(problems)))
    return checks
