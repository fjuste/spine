"""Tests for the memory digest (spine.py memory stats|digest)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402

# =============================================================================
# Task 1: frontmatter reader and classification
# =============================================================================


def test_frontmatter_plain_value_is_parsed() -> None:
    text = "---\ntask_id: 007\ntitle: Social login\n---\n# Body\n"
    assert memory.read_frontmatter(text) == {"task_id": "007", "title": "Social login"}


def test_frontmatter_quoted_value_is_unquoted() -> None:
    text = "---\nsummary: \"Scope: hub. Goals: ingest.\"\nother: 'x'\n---\n"
    fields = memory.read_frontmatter(text)
    assert fields["summary"] == "Scope: hub. Goals: ingest."
    assert fields["other"] == "x"


def test_folded_block_summary_is_parsed() -> None:
    text = (
        "---\n"
        "summary: >-\n"
        "  First line of the summary\n"
        "  continues here.\n"
        "status: DONE\n"
        "---\n"
    )
    fields = memory.read_frontmatter(text)
    assert fields["summary"] == "First line of the summary continues here."
    assert fields["status"] == "DONE"


def test_literal_block_keeps_newlines() -> None:
    text = "---\nsummary: |\n  line one\n  line two\n---\n"
    assert memory.read_frontmatter(text)["summary"] == "line one\nline two"


def test_frontmatter_list_values_do_not_leak_into_keys() -> None:
    text = "---\ntags:\n  - area/memory\n  - type/feature\ngoal: Ship it\n---\n"
    fields = memory.read_frontmatter(text)
    assert fields["goal"] == "Ship it"
    assert "- area/memory" not in fields


def test_text_without_frontmatter_returns_empty() -> None:
    assert memory.read_frontmatter("# Title\n\nsummary: not frontmatter\n") == {}


def test_unclosed_frontmatter_returns_empty() -> None:
    assert memory.read_frontmatter("---\ntitle: never closed\n# Body\n") == {}


def test_strip_frontmatter_returns_body() -> None:
    assert memory.strip_frontmatter("---\na: b\n---\n# Body\n") == "# Body\n"
    assert memory.strip_frontmatter("# Only body\n") == "# Only body\n"


@pytest.mark.parametrize(
    ("relative", "kind"),
    [
        ("global/project-brief.md", memory.NARRATIVE),
        ("global/design-system.md", memory.NARRATIVE),
        ("global/decision-log.md", memory.LOG),
        ("ledger/progress.md", memory.LOG),
        ("ledger/learnings.md", memory.LOG),
        ("ledger/roadmap.md", memory.EXTENDED),
        ("ledger/risks.md", memory.NARRATIVE),
        ("active_tasks/018-memory-digest.md", memory.TASK),
        ("active_tasks/_task-template.md", memory.IGNORED),
        ("active_tasks/notes.md", memory.IGNORED),
        ("completed_tasks/001-done.md", memory.IGNORED),
        ("global/image.png", memory.IGNORED),
    ],
)
def test_classify_memory_files(relative: str, kind: str) -> None:
    assert memory.classify(relative) == kind


def test_read_text_tolerates_bom_and_crlf(tmp_path: Path) -> None:
    path = tmp_path / "f.md"
    path.write_bytes("﻿---\r\nsummary: ok\r\n---\r\n# T\r\n".encode("utf-8"))
    text = memory.read_text(path)
    assert text == "---\nsummary: ok\n---\n# T\n"
    assert memory.read_frontmatter(text) == {"summary": "ok"}
