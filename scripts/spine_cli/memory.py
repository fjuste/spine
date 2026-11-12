"""Memory bank digest and stats (``spine.py memory stats|digest``).

The digest is a compact, deterministic view of ``docs/memory/`` that replaces
loading every global file, the whole ``progress.md`` and every open task body
at Core SYNC. Standard library only, Python 3.9+.
"""

from __future__ import annotations

import re
from pathlib import Path

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
