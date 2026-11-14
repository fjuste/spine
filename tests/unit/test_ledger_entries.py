"""Tests for the per-entry ledger (ledger/{decisions,learnings,deliveries}/ + INDEX.md)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402


def _entry(
    entry_id: str,
    date: str,
    title: str,
    summary: str = "One-line summary.",
    tags: str = "  - area/memory\n  - type/feature\n",
    task: str = "",
    superseded_by: str = "",
    body: str = "Body.\n",
) -> str:
    return (
        "---\n"
        f"id: {entry_id}\n"
        f"date: {date}\n"
        f"title: {title}\n"
        f"summary: {summary}\n"
        f"tags:\n{tags}"
        f"task: {task}\n"
        f"superseded_by: {superseded_by}\n"
        "---\n\n"
        f"{body}"
    )


def _write_entry(root: Path, folder: str, name: str, text: str) -> Path:
    path = root / "docs" / "memory" / "ledger" / folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _memory_dir(root: Path) -> Path:
    return root / "docs" / "memory"


# =============================================================================
# Task 1: ledger entry model
# =============================================================================


def test_frontmatter_list_tags_are_parsed() -> None:
    block = "---\ntags:\n  - area/memory\n  - type/feature\ngoal: x\n---\n"
    inline = "---\ntags: [area/api, 'type/bug']\n---\n"
    single = "---\ntags: area/infra\n---\n"
    assert memory.read_frontmatter_list(block, "tags") == ["area/memory", "type/feature"]
    assert memory.read_frontmatter_list(inline, "tags") == ["area/api", "type/bug"]
    assert memory.read_frontmatter_list(single, "tags") == ["area/infra"]
    assert memory.read_frontmatter_list("---\ngoal: x\n---\n", "tags") == []
    assert memory.read_frontmatter_list("# no frontmatter\n", "tags") == []


def test_collect_entries_reads_frontmatter(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "decisions",
        "2026-11-12-memory-digest.md",
        _entry("2026-11-12-memory-digest", "2026-11-12", "Core SYNC reads the digest", task="018-memory-digest"),
    )

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "decisions")

    assert entry.entry_id == "2026-11-12-memory-digest"
    assert entry.date == "2026-11-12"
    assert entry.title == "Core SYNC reads the digest"
    assert entry.summary == "One-line summary."
    assert entry.tags == ("area/memory", "type/feature")
    assert entry.task == "018-memory-digest"
    assert entry.superseded_by == ""
    assert entry.filename == "2026-11-12-memory-digest.md"


def test_collect_entries_ignores_template_and_index(tmp_path: Path) -> None:
    _write_entry(tmp_path, "learnings", "_template.md", _entry("LEARN-000", "2026-01-01", "Template"))
    _write_entry(tmp_path, "learnings", "INDEX.md", "# Learnings\n")
    _write_entry(tmp_path, "learnings", "notes.txt", "not markdown")
    _write_entry(tmp_path, "learnings", "LEARN-001-flaky.md", _entry("LEARN-001", "2026-02-01", "Flaky"))

    entries = memory.collect_entries(_memory_dir(tmp_path), "learnings")

    assert [entry.entry_id for entry in entries] == ["LEARN-001"]


def test_collect_entries_newest_first(tmp_path: Path) -> None:
    for name, date in (("2026-01-05-a.md", "2026-01-05"), ("2026-03-01-b.md", "2026-03-01"), ("2026-02-01-c.md", "2026-02-01")):
        _write_entry(tmp_path, "deliveries", name, _entry(name[:-3], date, name))

    entries = memory.collect_entries(_memory_dir(tmp_path), "deliveries")

    assert [entry.date for entry in entries] == ["2026-03-01", "2026-02-01", "2026-01-05"]


def test_collect_entries_falls_back_to_filename(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-04-01-no-frontmatter.md", "# Just a body\n")

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "decisions")

    assert entry.entry_id == "2026-04-01-no-frontmatter"
    assert entry.title == "2026-04-01-no-frontmatter"
    assert entry.summary == ""


def test_collect_entries_missing_folder_returns_empty(tmp_path: Path) -> None:
    assert memory.collect_entries(_memory_dir(tmp_path), "decisions") == []


def test_learning_recurrences_are_counted(tmp_path: Path) -> None:
    body = (
        "**Symptoms:** x\n\n"
        "**Recurrences:**\n"
        "- (append-only — one line per recurrence with date and task ref)\n"
        "- 2026-03-01 — task 012-foo (again)\n"
        "- 2026-04-01 — task 015-bar (again)\n"
        "\n"
        "Trailing paragraph.\n"
        "- not a recurrence\n"
    )
    _write_entry(tmp_path, "learnings", "LEARN-002-x.md", _entry("LEARN-002", "2026-02-01", "X", body=body))

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "learnings")

    assert entry.recurrences == 2
