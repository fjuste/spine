"""Split legacy memory log files into ledger entries (``spine.py memory migrate``).

Legacy single files — ``global/decision-log.md``, ``ledger/learnings.md`` and
the ``## Delivery log`` section of ``ledger/progress.md`` — become one entry
file each under ``ledger/{decisions,learnings,deliveries}/``. Bodies are copied
verbatim; ``summary:`` is the title. The default run is a dry run; ``--apply``
writes only when the plan has no unparsed text and no ID conflicts.
Standard library only, Python 3.9+.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from spine_cli.log import SpineExit
from spine_cli.memory import (
    ENTRY_SUMMARY_MAX_CHARS,
    LEDGER_DIR,
    MEMORY_DIR,
    _PLACEHOLDER_ENTRY_RE,
    _cap,
    collect_entries,
    read_text,
    write_indexes,
)
from spine_cli.paths import resolve_project_root

DECISION_LOG = "global/decision-log.md"
LEARNINGS_LOG = "ledger/learnings.md"
PROGRESS = "ledger/progress.md"
DECISIONS = "decisions"
LEARNINGS = "learnings"
DELIVERIES = "deliveries"
SLUG_MAX_CHARS = 60
FALLBACK_SLUG = "entry"
REPORT_LINE_MAX_CHARS = 100
MIGRATE_CMD = "python3 .spine/scripts/spine.py memory migrate"

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$")
_SEPARATOR_LINE_RE = re.compile(r"^[ \t]*-{3,}[ \t]*$")
_TITLE_SEP = r"(?:[ \t]+[-—–:][ \t]+|[ \t]*[—–:][ \t]*|[ \t]+|$)"
_DATED_HEADING_RE = re.compile(rf"^\[?(\d{{4}}-\d{{2}}-\d{{2}})\]?(?:-([a-z0-9][a-z0-9-]*[a-z0-9]))?{_TITLE_SEP}(.*)$")
_LEARN_HEADING_RE = re.compile(rf"^(LEARN-\d+){_TITLE_SEP}(.*)$")
_PLACEHOLDER_RE = re.compile(
    _PLACEHOLDER_ENTRY_RE.pattern + r"|\[DATA\]|\[TITULO\]|LEARN-NNN|Example incident slug"
)
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_DELIVERY_LOG_RE = re.compile(r"^##[ \t]+Delivery log", re.IGNORECASE)
_H2_RE = re.compile(r"^##[ \t]")
_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_TASK_RE = re.compile(r"\*\*Task:\*\*[ \t]*`?(\d{3,}-[A-Za-z0-9._-]+)`?")
_TAGS_RE = re.compile(r"^\*\*Tags:\*\*[ \t]*(.+)$", re.MULTILINE)
_FIRST_SEEN_RE = re.compile(r"\*\*First seen:\*\*[ \t]*(\d{4}-\d{2}-\d{2})")
_BOLD_LEAD_RE = re.compile(r"^\*\*(.+?)\*\*")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
_PLAIN_UNSAFE_START = frozenset("-?:,[]{}#&*!|>'\"%@`")
_TABLE_FIELDS = ("Decision", "Why", "Alternatives considered")


# =============================================================================
# Parsed entries
# =============================================================================


@dataclass(frozen=True)
class LegacyEntry:
    """One entry read from a legacy log file.

    Args:
        kind: Target ledger folder (``decisions``, ``learnings``, ``deliveries``).
        line: 1-based line of the entry heading or table row in the legacy file.
        base_id: Entry id before duplicate suffixes.
        date: ISO date (empty when the legacy entry has none).
        title: Heading text after the date or id, capped.
        tags: Items of a ``**Tags:**`` line.
        task: ``NNN-slug`` of a ``**Task:**`` line (empty when none).
        body: Entry body, verbatim (table rows rendered as labelled fields).
    """

    kind: str
    line: int
    base_id: str
    date: str
    title: str
    tags: tuple[str, ...]
    task: str
    body: str

    @property
    def summary(self) -> str:
        """Mechanical one-line summary: the title, capped at the entry limit."""
        return _cap(self.title, ENTRY_SUMMARY_MAX_CHARS)


@dataclass
class ParseResult:
    """Outcome of parsing one legacy file (or the Delivery log section).

    Args:
        entries: Parsed entries in file order.
        placeholders: ``(line, text)`` of skipped template placeholders.
        preamble: ``(line, text)`` of dropped non-blank lines before the first entry.
        unparsed: ``(line, text)`` of non-blank lines that belong to no entry.
    """

    entries: list[LegacyEntry] = field(default_factory=list)
    placeholders: list[tuple[int, str]] = field(default_factory=list)
    preamble: list[tuple[int, str]] = field(default_factory=list)
    unparsed: list[tuple[int, str]] = field(default_factory=list)


def slugify(text: str) -> str:
    """Return an ASCII, lowercase, hyphenated slug of at most ``SLUG_MAX_CHARS``.

    Args:
        text: Free text (accents are folded).

    Returns:
        The slug, cut at a hyphen when too long; ``FALLBACK_SLUG`` when empty.
    """
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    if len(slug) > SLUG_MAX_CHARS:
        head = slug[: SLUG_MAX_CHARS + 1]
        cut = head.rfind("-")
        slug = head[:cut] if cut > 0 else slug[:SLUG_MAX_CHARS]
    return slug.strip("-") or FALLBACK_SLUG


def _outside_fences(lines: list[str]) -> list[bool]:
    """Flag each line that sits outside fenced code blocks (fence lines count as inside)."""
    flags: list[bool] = []
    fence = ""
    for line in lines:
        match = _FENCE_RE.match(line)
        if fence:
            flags.append(False)
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = ""
        elif match:
            fence = match.group(1)
            flags.append(False)
        else:
            flags.append(True)
    return flags


def _trim_body(lines: list[str]) -> str:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and (not lines[-1].strip() or _SEPARATOR_LINE_RE.match(lines[-1])):
        lines = lines[:-1]
    return "\n".join(lines) + "\n" if lines else ""


def _metadata(body: str) -> tuple[tuple[str, ...], str]:
    tags_match = _TAGS_RE.search(body)
    tags: tuple[str, ...] = ()
    if tags_match:
        tags = tuple(item.strip().strip("`") for item in tags_match.group(1).split(",") if item.strip().strip("`"))
    task_match = _TASK_RE.search(body)
    return tags, task_match.group(1) if task_match else ""


def _entry(kind: str, line: int, head: re.Match[str], body_lines: list[str]) -> LegacyEntry:
    body = _trim_body(body_lines)
    tags, task = _metadata(body)
    if kind == LEARNINGS:
        learn_id, raw_title = head.group(1), head.group(2)
        first_seen = _FIRST_SEEN_RE.search(body)
        any_date = _ISO_DATE_RE.search(body)
        date = first_seen.group(1) if first_seen else any_date.group(0) if any_date else ""
        title = _cap(raw_title or learn_id, ENTRY_SUMMARY_MAX_CHARS)
        return LegacyEntry(kind, line, learn_id, date, title, tags, task, body)
    date, heading_slug, raw_title = head.group(1), head.group(2), head.group(3)
    title = _cap(raw_title or heading_slug or date, ENTRY_SUMMARY_MAX_CHARS)
    if heading_slug:
        base_id = f"{date}-{heading_slug}"
    elif kind == DELIVERIES and task:
        base_id = f"{date}-{task}"
    else:
        base_id = f"{date}-{slugify(title)}"
    return LegacyEntry(kind, line, base_id, date, title, tags, task, body)


# =============================================================================
# Heading-based parser (heading decisions, learnings, Delivery log)
# =============================================================================

_PREAMBLE = "preamble"
_ENTRY = "entry"
_PLACEHOLDER = "placeholder"
_ORPHAN = "orphan"
_ENTRY_LEVELS = {DECISIONS: (2, 3), LEARNINGS: (2, 3), DELIVERIES: (3,)}  # Delivery log entries sit under its ##


def _classify_heading(kind: str, level: int, text: str) -> tuple[str, re.Match[str] | None]:
    """Return ``(_ENTRY, match)``, ``(_PLACEHOLDER, None)`` or ``("", None)``."""
    if level not in _ENTRY_LEVELS[kind]:
        return "", None
    if _PLACEHOLDER_RE.search(text):
        return _PLACEHOLDER, None
    pattern = _LEARN_HEADING_RE if kind == LEARNINGS else _DATED_HEADING_RE
    match = pattern.match(text)
    return (_ENTRY, match) if match else ("", None)


def _parse_headed(kind: str, lines: list[str], offset: int) -> ParseResult:
    """Parse entries introduced by headings; ``offset`` maps to file line numbers."""
    result = ParseResult()
    state, zone_level = _PREAMBLE, 0
    head: re.Match[str] | None = None
    head_line = 0
    body: list[str] = []

    def close() -> None:
        if state == _ENTRY and head is not None:
            result.entries.append(_entry(kind, head_line, head, body))

    for index, (line, outside) in enumerate(zip(lines, _outside_fences(lines))):
        number = offset + index + 1
        heading = _HEADING_RE.match(line) if outside else None
        if heading:
            level = len(heading.group(1))
            verdict, match = _classify_heading(kind, level, heading.group(2))
            if verdict:
                close()
                state, zone_level, head, head_line, body = verdict, level, match, number, []
                if verdict == _PLACEHOLDER:
                    result.placeholders.append((number, line))
                continue
            if state in (_ENTRY, _PLACEHOLDER) and level <= zone_level:
                close()
                state, head = _ORPHAN, None
            elif state == _PREAMBLE and level == max(_ENTRY_LEVELS[kind]):  # unrecognized entry heading
                state = _ORPHAN
        if state == _ENTRY:
            body.append(line)
        elif state == _PREAMBLE and line.strip() and not _SEPARATOR_LINE_RE.match(line):
            result.preamble.append((number, line))
        elif state == _ORPHAN and line.strip() and not _SEPARATOR_LINE_RE.match(line):
            result.unparsed.append((number, line))
    close()
    return result


# =============================================================================
# Table parser (decision-log as a 4-column table)
# =============================================================================


def _cells(row: str) -> list[str]:
    stripped = row.strip()[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in _CELL_SPLIT_RE.split(stripped)]


def _table_entry(line: int, cells: list[str]) -> LegacyEntry:
    date, decision = cells[0], cells[1]
    bold = _BOLD_LEAD_RE.match(decision)
    title = _cap(bold.group(1) if bold else decision, ENTRY_SUMMARY_MAX_CHARS)
    fields = [f"**{label}:** {value}" for label, value in zip(_TABLE_FIELDS, cells[1:]) if value]
    body = "\n\n".join(fields) + "\n"
    return LegacyEntry(DECISIONS, line, f"{date}-{slugify(title)}", date, title, (), "", body)


def _parse_table(lines: list[str]) -> ParseResult:
    result = ParseResult()
    start = next(index for index, line in enumerate(lines) if line.lstrip().startswith("|"))
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    result.preamble = [
        (index + 1, line) for index, line in enumerate(lines[:start]) if line.strip() and not _SEPARATOR_LINE_RE.match(line)
    ]
    columns = len(_cells(lines[start]))
    for index in range(start + 1, end):
        number, cells = index + 1, _cells(lines[index])
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if _PLACEHOLDER_RE.search(cells[0]):
            result.placeholders.append((number, lines[index]))
        elif len(cells) != columns or len(cells) < 2 or not _ISO_DATE_RE.fullmatch(cells[0]):
            result.unparsed.append((number, lines[index]))
        else:
            result.entries.append(_table_entry(number, cells))
    result.unparsed += [(index + 1, line) for index, line in enumerate(lines[end:], start=end) if line.strip()]
    return result


# =============================================================================
# Public parsers
# =============================================================================


def parse_decision_log(text: str) -> ParseResult:
    """Parse a legacy ``global/decision-log.md`` (heading or table format).

    Args:
        text: File content (LF newlines).

    Returns:
        Entries, placeholders, dropped preamble and unparsed lines.
    """
    lines = text.split("\n")
    has_dated_heading = any(
        (heading := _HEADING_RE.match(line))
        and _classify_heading(DECISIONS, len(heading.group(1)), heading.group(2))[0]
        for line in lines
    )
    if not has_dated_heading and any(line.lstrip().startswith("|") for line in lines):
        return _parse_table(lines)
    return _parse_headed(DECISIONS, lines, 0)


def parse_learnings(text: str) -> ParseResult:
    """Parse a legacy ``ledger/learnings.md`` (``##`` or ``###`` ``LEARN-NNN`` headings).

    Args:
        text: File content (LF newlines).

    Returns:
        Entries, placeholders, dropped preamble and unparsed lines.
    """
    return _parse_headed(LEARNINGS, text.split("\n"), 0)


def delivery_log_span(text: str) -> tuple[int, int] | None:
    """Return ``(start, end)`` char offsets of the ``## Delivery log`` section.

    Args:
        text: ``progress.md`` content (LF newlines).

    Returns:
        Offsets from the heading line to the next ``## `` heading (or the end),
        or None when the section is absent.
    """
    lines = text.split("\n")
    outside = _outside_fences(lines)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line) + 1)
    heading = next((index for index, line in enumerate(lines) if outside[index] and _DELIVERY_LOG_RE.match(line)), None)
    if heading is None:
        return None
    following = next(
        (index for index in range(heading + 1, len(lines)) if outside[index] and _H2_RE.match(lines[index])), None
    )
    return starts[heading], starts[following] if following is not None else len(text)


def parse_delivery_log(text: str) -> ParseResult | None:
    """Parse the legacy ``## Delivery log`` section of ``ledger/progress.md``.

    Args:
        text: ``progress.md`` content (LF newlines).

    Returns:
        The parse result (line numbers refer to ``progress.md``), or None when
        the file has no Delivery log section.
    """
    span = delivery_log_span(text)
    if span is None:
        return None
    heading_line = text.count("\n", 0, span[0])
    section_lines = text[span[0]: span[1]].split("\n")[1:]
    return _parse_headed(DELIVERIES, section_lines, heading_line + 1)


# =============================================================================
# Rendering
# =============================================================================

_FIELD_ORDER = {
    DECISIONS: ("id", "date", "title", "summary", "tags", "task", "superseded_by"),
    LEARNINGS: ("id", "date", "title", "summary", "tags", "task"),
    DELIVERIES: ("id", "date", "title", "summary", "tags", "task"),
}


def _scalar(value: str) -> str:
    """Render a frontmatter scalar: plain when safe, else a one-line ``>-`` block."""
    if not value:
        return ""
    unsafe = value[0] in _PLAIN_UNSAFE_START or ": " in value or " #" in value or value.endswith(":")
    return f">-\n  {value}" if unsafe else value


def render_entry(entry: LegacyEntry, entry_id: str) -> str:
    """Render one ledger entry file (template field order, then the verbatim body).

    Args:
        entry: Parsed legacy entry.
        entry_id: Final id (``base_id`` plus any duplicate suffix).

    Returns:
        File content with YAML frontmatter.
    """
    values = {
        "id": entry_id,
        "date": entry.date,
        "title": entry.title,
        "summary": entry.summary,
        "task": entry.task,
        "superseded_by": "",
    }
    lines = ["---"]
    for key in _FIELD_ORDER[entry.kind]:
        if key == "tags":
            lines += ["tags:"] + [f"  - {tag}" for tag in entry.tags] if entry.tags else ["tags: []"]
            continue
        rendered = _scalar(values[key])
        lines.append(f"{key}: {rendered}" if rendered else f"{key}:")
    lines.append("---")
    text = "\n".join(lines) + "\n"
    return f"{text}\n{entry.body}" if entry.body else text


# =============================================================================
# Plan, report and apply
# =============================================================================


@dataclass(frozen=True)
class PlannedEntry:
    """One entry file the migration would write.

    Args:
        entry: Parsed legacy entry.
        entry_id: Final id (suffixed when the base id repeats in this run).
        relative: Target path relative to ``docs/memory/``.
        conflict: True when the id or file already exists in the folder.
    """

    entry: LegacyEntry
    entry_id: str
    relative: str
    conflict: bool

    @property
    def suffixed(self) -> bool:
        """True when a duplicate suffix was appended to the base id."""
        return self.entry_id != self.entry.base_id


@dataclass(frozen=True)
class SourcePlan:
    """What the migration does with one legacy source.

    Args:
        relative: Legacy file path relative to ``docs/memory/``.
        result: Parse result of that file (or of the Delivery log section).
    """

    relative: str
    result: ParseResult


@dataclass
class MigrationPlan:
    """The whole migration, computed before anything is written.

    Args:
        sources: One plan per legacy source found, in fixed order.
        planned: Entry files to write, in source then file order.
    """

    sources: list[SourcePlan]
    planned: list[PlannedEntry]

    @property
    def unparsed(self) -> int:
        """Number of unparsed lines across sources."""
        return sum(len(source.result.unparsed) for source in self.sources)

    @property
    def conflicts(self) -> list[PlannedEntry]:
        """Planned entries whose id or file already exists."""
        return [item for item in self.planned if item.conflict]

    @property
    def blocked(self) -> bool:
        """True when ``--apply`` must refuse (unparsed text or conflicts)."""
        return bool(self.unparsed or self.conflicts)


def has_legacy_logs(memory_dir: Path) -> bool:
    """Return True when a legacy log file or a Delivery log section remains.

    Args:
        memory_dir: The ``docs/memory/`` directory.

    Returns:
        Whether ``spine.py memory migrate`` has anything to do.
    """
    if (memory_dir / DECISION_LOG).is_file() or (memory_dir / LEARNINGS_LOG).is_file():
        return True
    progress = memory_dir / PROGRESS
    return progress.is_file() and delivery_log_span(read_text(progress)) is not None


def _sources(memory_dir: Path) -> list[SourcePlan]:
    sources: list[SourcePlan] = []
    if (memory_dir / DECISION_LOG).is_file():
        sources.append(SourcePlan(DECISION_LOG, parse_decision_log(read_text(memory_dir / DECISION_LOG))))
    if (memory_dir / LEARNINGS_LOG).is_file():
        sources.append(SourcePlan(LEARNINGS_LOG, parse_learnings(read_text(memory_dir / LEARNINGS_LOG))))
    if (memory_dir / PROGRESS).is_file():
        delivery = parse_delivery_log(read_text(memory_dir / PROGRESS))
        if delivery is not None:
            sources.append(SourcePlan(PROGRESS, delivery))
    return sources


def _file_name(entry: LegacyEntry, entry_id: str) -> str:
    return f"{entry_id}-{slugify(entry.title)}.md" if entry.kind == LEARNINGS else f"{entry_id}.md"


def build_plan(root: Path) -> MigrationPlan:
    """Parse every legacy source and assign final ids, paths and conflicts.

    Args:
        root: Project root that contains ``docs/memory/``.

    Returns:
        The plan; empty ``sources`` when nothing is left to migrate.
    """
    memory_dir = root / MEMORY_DIR
    sources = _sources(memory_dir)
    planned: list[PlannedEntry] = []
    for source in sources:
        entries = source.result.entries
        if not entries:
            continue
        folder = entries[0].kind
        directory = memory_dir / LEDGER_DIR / folder
        existing = collect_entries(memory_dir, folder)
        taken_ids = {item.entry_id for item in existing}
        taken_files = {item.filename for item in existing}
        seen: dict[str, int] = {}
        for entry in entries:
            seen[entry.base_id] = seen.get(entry.base_id, 0) + 1
            count = seen[entry.base_id]
            entry_id = entry.base_id if count == 1 else f"{entry.base_id}-{count}"
            name = _file_name(entry, entry_id)
            conflict = entry_id in taken_ids or name in taken_files or (directory / name).exists()
            planned.append(PlannedEntry(entry, entry_id, f"{LEDGER_DIR}/{folder}/{name}", conflict))
    return MigrationPlan(sources, planned)


def _quote(text: str) -> str:
    return _cap(text.strip(), REPORT_LINE_MAX_CHARS)


def _removal(relative: str) -> str:
    return f"cut § Delivery log from {relative}" if relative == PROGRESS else f"remove {relative}"


def render_report(plan: MigrationPlan, apply: bool) -> str:
    """Render the migration report shown by dry run and refused applies.

    Args:
        plan: Output of :func:`build_plan`.
        apply: Whether the run was invoked with ``--apply``.

    Returns:
        Human-readable report ending with a one-line total.
    """
    if not plan.sources:
        return "Legacy memory log files: nothing to migrate.\n"
    mode = "apply" if apply else "dry run (nothing written; run with --apply to write)"
    lines = [f"Memory migrate — {mode}", ""]
    for source in plan.sources:
        result = source.result
        items = [item for item in plan.planned if any(item.entry is entry for entry in result.entries)]
        lines.append(f"{source.relative}: {len(items)} entries; then {_removal(source.relative)}")
        for item in items:
            mark = "CONFLICT (already exists)" if item.conflict else "+"
            lines.append(f"  {mark} {item.relative}")
            if item.suffixed:
                lines.append(f"      duplicate id suffix: {item.entry.base_id} → {item.entry_id} (line {item.entry.line})")
        lines += [f"  skipped placeholder (line {number}): {_quote(text)}" for number, text in result.placeholders]
        lines += [f"  dropped preamble (line {number}): {_quote(text)}" for number, text in result.preamble]
        lines += [f"  UNPARSED line {number}: {_quote(text)}" for number, text in result.unparsed]
        lines.append("")
    placeholders = sum(len(source.result.placeholders) for source in plan.sources)
    lines.append(
        f"Total: {len(plan.planned)} entries, {placeholders} placeholders skipped, "
        f"{plan.unparsed} unparsed lines, {len(plan.conflicts)} conflicts."
    )
    if plan.blocked:
        lines.append(
            "Blocked: fix unparsed lines by hand (move them into an entry or delete them) and resolve "
            "conflicts (an entry with that id already exists) before --apply."
        )
    return "\n".join(lines) + "\n"


def _cut_delivery_log(text: str) -> str:
    span = delivery_log_span(text)
    if span is None:
        return text
    before, after = text[: span[0]], text[span[1]:]
    if after:
        return before + after
    return before.rstrip("\n") + "\n"


def apply_plan(root: Path, plan: MigrationPlan) -> list[Path]:
    """Write the planned entries, remove the legacy parts and regenerate indexes.

    Args:
        root: Project root that contains ``docs/memory/``.
        plan: A plan whose ``blocked`` is False.

    Returns:
        Entry files written.
    """
    memory_dir = root / MEMORY_DIR
    written: list[Path] = []
    for item in plan.planned:
        path = memory_dir / item.relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_entry(item.entry, item.entry_id), encoding="utf-8")
        written.append(path)
    for source in plan.sources:
        path = memory_dir / source.relative
        if source.relative == PROGRESS:
            path.write_text(_cut_delivery_log(read_text(path)), encoding="utf-8")
        else:
            path.unlink()
    write_indexes(root)
    return written


def run_migrate(project_root: str | None, apply: bool) -> int:
    """Run ``spine.py memory migrate [--apply]``.

    Args:
        project_root: ``--project-root`` value, or None for the git toplevel.
        apply: Write entries and remove legacy parts; otherwise a dry run.

    Returns:
        Process exit code: 1 when ``--apply`` refuses a blocked plan.
    """
    try:
        root = resolve_project_root(project_root)
    except SpineExit as exc:
        return exc.code
    plan = build_plan(root)
    sys.stdout.write(render_report(plan, apply))
    if not apply or not plan.sources:
        return 0
    if plan.blocked:
        sys.stdout.write("Refusing to apply: nothing was written.\n")
        return 1
    written = apply_plan(root, plan)
    removed = ", ".join(_removal(source.relative) for source in plan.sources)
    sys.stdout.write(f"Applied: wrote {len(written)} entry files; {removed}; regenerated ledger INDEX.md files.\n")
    return 0
