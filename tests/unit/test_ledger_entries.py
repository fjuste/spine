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


# =============================================================================
# Task 2: INDEX.md generation
# =============================================================================


def _rows(index: str) -> list[str]:
    lines = [line for line in index.split("\n") if line.startswith("| ")]
    return lines[1:]  # drop the header row (the separator starts with "|-")


def test_index_lists_entries_newest_first(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-old.md", _entry("2026-01-01-old", "2026-01-01", "Old decision"))
    _write_entry(tmp_path, "decisions", "2026-05-01-new.md", _entry("2026-05-01-new", "2026-05-01", "New decision"))

    index = memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions"))

    rows = _rows(index)
    assert len(rows) == 2
    assert rows[0].startswith("| 2026-05-01 | [New decision](2026-05-01-new.md) | active |")
    assert rows[1].startswith("| 2026-01-01 | [Old decision](2026-01-01-old.md) | active |")
    assert "area/memory, type/feature" in rows[0]
    assert rows[0].endswith("| One-line summary. |")
    assert "spine.py memory index" in index


def test_index_marks_superseded_decisions(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "decisions",
        "2026-01-01-old.md",
        _entry("2026-01-01-old", "2026-01-01", "Old", superseded_by="2026-05-01-new"),
    )

    index = memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions"))

    assert "| superseded by [2026-05-01-new](2026-05-01-new.md) |" in _rows(index)[0]


def test_index_counts_learning_recurrences(tmp_path: Path) -> None:
    body = "**Recurrences:**\n- 2026-03-01 — task 012-foo\n- 2026-04-01 — task 015-bar\n"
    _write_entry(tmp_path, "learnings", "LEARN-002-x.md", _entry("LEARN-002", "2026-02-01", "Flaky test", body=body))

    [row] = _rows(memory.render_index("learnings", memory.collect_entries(_memory_dir(tmp_path), "learnings")))

    assert row.startswith("| LEARN-002 | [Flaky test](LEARN-002-x.md) | area/memory, type/feature | 2 |")


def test_index_shows_delivery_task(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "deliveries",
        "2026-11-12-019-self-install.md",
        _entry("2026-11-12-019-self-install", "2026-11-12", "Self-install", task="019-self-install"),
    )

    [row] = _rows(memory.render_index("deliveries", memory.collect_entries(_memory_dir(tmp_path), "deliveries")))

    assert row.startswith("| 2026-11-12 | [Self-install](2026-11-12-019-self-install.md) | 019-self-install |")


def test_index_escapes_pipes(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A | B", summary="x | y"))

    [row] = _rows(memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions")))

    assert "[A \\| B]" in row and "x \\| y" in row


def test_empty_index_has_header_only() -> None:
    index = memory.render_index("learnings", [])
    assert index.startswith("# Learnings\n")
    assert _rows(index) == []
    assert "| ID | Title | Tags | Recurrences | Summary |" in index


def test_index_ignores_template_and_index(tmp_path: Path) -> None:
    _write_entry(tmp_path, "learnings", "_template.md", _entry("LEARN-000", "2026-01-01", "Template entry"))
    _write_entry(tmp_path, "learnings", "LEARN-001-a.md", _entry("LEARN-001", "2026-02-01", "Real entry"))

    memory.write_indexes(tmp_path)

    index = (_memory_dir(tmp_path) / "ledger" / "learnings" / "INDEX.md").read_text(encoding="utf-8")
    assert "Real entry" in index
    assert "Template entry" not in index


def test_index_is_idempotent(tmp_path: Path) -> None:
    _write_entry(tmp_path, "deliveries", "2026-02-01-a.md", _entry("2026-02-01-a", "2026-02-01", "A"))
    _write_entry(tmp_path, "decisions", "2026-02-01-b.md", _entry("2026-02-01-b", "2026-02-01", "B"))

    written = memory.write_indexes(tmp_path)
    index_path = _memory_dir(tmp_path) / "ledger" / "deliveries" / "INDEX.md"
    first = index_path.read_text(encoding="utf-8")

    assert sorted(path.parent.name for path in written) == ["decisions", "deliveries"]
    assert memory.write_indexes(tmp_path) == []
    assert index_path.read_text(encoding="utf-8") == first


def test_write_indexes_skips_missing_folders(tmp_path: Path) -> None:
    (_memory_dir(tmp_path) / "ledger").mkdir(parents=True)

    assert memory.write_indexes(tmp_path) == []
    assert not (_memory_dir(tmp_path) / "ledger" / "decisions").exists()


def test_cli_memory_index_writes_indexes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import spine

    _write_entry(tmp_path, "decisions", "2026-02-01-b.md", _entry("2026-02-01-b", "2026-02-01", "B"))

    assert spine.main(["memory", "index", "--project-root", str(tmp_path)]) == 0
    assert "docs/memory/ledger/decisions/INDEX.md" in capsys.readouterr().out

    assert spine.main(["memory", "index", "--project-root", str(tmp_path)]) == 0
    assert "up to date" in capsys.readouterr().out
