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


# =============================================================================
# Fixtures for digest tests
# =============================================================================

PROGRESS = """# Progress

## Current state
- In flight: task 018
- Next: harvest

## Delivery log (newest first)

### 2026-11-10 — Seventh delivery
body
### 2026-11-09 — Sixth delivery
### 2026-11-08 — Fifth delivery
### 2026-11-07 — Fourth delivery
### 2026-11-06 — Third delivery
### 2026-11-05 — Second delivery
### 2026-11-04 — First delivery
"""

DECISION_TABLE = """# Decision Log

| Data | Decisao | Porque |
|---|---|---|
| 2026-03-01 | Decision one | why |
| 2026-03-02 | Decision two | why |
| 2026-03-03 | Decision three | why |
| 2026-03-04 | Decision four | why |
| 2026-03-05 | Decision five | why |
| 2026-03-06 | Decision six | why |
"""

DECISION_HEADINGS = """# Decision Log

## Architectural Decisions

### 2026-11-11 - Newest decision
**Context:** a
### 2026-11-10 - Second decision
### 2026-11-09 - Third decision
"""

LEARNINGS = """# Learnings Registry

## LEARN-001 — First learning
**Symptoms:** x
## LEARN-002 — Second learning
## LEARN-003 — Third learning
"""


def _task(task_id: str, status: str, title: str, goal: str | None, body: str = "") -> str:
    goal_line = f"goal: {goal}\n" if goal is not None else ""
    return (
        f"---\ntask_id: {task_id}\ntitle: {title}\n{goal_line}status: {status}\n"
        f"tags:\n  - type/feature\n---\n\n# {task_id}\n\n{body}\n"
    )


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / "docs" / "memory" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture()
def bank(tmp_path: Path) -> Path:
    """A memory bank with narrative, log, task and extended files."""
    _write(
        tmp_path,
        "global/project-brief.md",
        "---\nsummary: >-\n  Hub for onboarding.\n  Scope is ingestion.\n---\n# Project Brief\n\n## Scope\nx\n",
    )
    _write(tmp_path, "global/tech-context.md", "# Tech\n\n## Development Setup\nx\n## Known Risks\ny\n")
    _write(tmp_path, "global/decision-log.md", DECISION_HEADINGS)
    _write(tmp_path, "ledger/progress.md", PROGRESS)
    _write(tmp_path, "ledger/learnings.md", LEARNINGS)
    _write(tmp_path, "ledger/roadmap.md", "# Roadmap\n" + "r" * 500)
    _write(tmp_path, "active_tasks/003-third.md", _task("003", "PLANNING", "Third", "Do three", "SECRET-BODY-3"))
    _write(tmp_path, "active_tasks/001-first.md", _task("001", "PLANNING", "First", "Do one", "SECRET-BODY-1"))
    _write(tmp_path, "active_tasks/007-seventh.md", _task("007", "REVIEW", "Seventh", "Do seven"))
    _write(tmp_path, "active_tasks/009-ninth.md", _task("009", "IN_PROGRESS", "Ninth", "Do nine"))
    _write(tmp_path, "active_tasks/_task-template.md", _task("NNN", "PLANNING", "TEMPLATE-TITLE", "x"))
    return tmp_path


# =============================================================================
# Task 2: digest sections
# =============================================================================


def test_digest_sections_order_and_one_line_per_task(bank: Path) -> None:
    digest = memory.build_digest(bank)
    headings = ["## Current state", "## Open tasks", "## Narrative files", "## Logs"]
    positions = [digest.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "- In flight: task 018" in digest

    task_lines = [line for line in digest.splitlines() if " | " in line and line[:3].isdigit()]
    assert task_lines == [
        "009 | IN_PROGRESS | Ninth — Do nine",
        "007 | REVIEW | Seventh — Do seven",
        "001 | PLANNING | First — Do one",
        "003 | PLANNING | Third — Do three",
    ]


def test_digest_never_includes_task_body(bank: Path) -> None:
    digest = memory.build_digest(bank)
    assert "SECRET-BODY" not in digest


def test_task_template_is_ignored(bank: Path) -> None:
    assert "TEMPLATE-TITLE" not in memory.build_digest(bank)


def test_done_task_left_in_active_tasks_is_not_listed(bank: Path) -> None:
    _write(bank, "active_tasks/002-stale.md", _task("002", "DONE", "Stale", "Old"))
    assert "Stale" not in memory.build_digest(bank)


def test_task_without_goal_shows_title_only(bank: Path) -> None:
    _write(bank, "active_tasks/004-nogoal.md", _task("004", "PLANNING", "No goal", None))
    assert "004 | PLANNING | No goal\n" in memory.build_digest(bank)


def test_log_files_show_count_and_newest_five_titles(bank: Path) -> None:
    digest = memory.build_digest(bank)
    assert "ledger/progress.md delivery log: 7 entries" in digest
    progress_block = digest.split("ledger/progress.md delivery log")[1]
    for title in ("Seventh", "Sixth", "Fifth", "Fourth", "Third"):
        assert f"{title} delivery" in progress_block
    assert "Second delivery" not in digest
    assert "First delivery" not in digest

    assert "global/decision-log.md: 3 entries" in digest
    assert "2026-11-11 - Newest decision" in digest
    assert "ledger/learnings.md: 3 entries" in digest
    learn_block = digest.split("ledger/learnings.md")[1]
    assert learn_block.index("LEARN-003") < learn_block.index("LEARN-001")


def test_table_decision_log_lists_newest_rows_first(bank: Path) -> None:
    _write(bank, "global/decision-log.md", DECISION_TABLE)
    digest = memory.build_digest(bank)
    assert "global/decision-log.md: 6 entries" in digest
    block = digest.split("global/decision-log.md")[1]
    assert block.index("2026-03-06 — Decision six") < block.index("2026-03-02 — Decision two")
    assert "Decision one" not in digest
    assert "Decisao" not in digest


def test_template_placeholder_log_entries_are_not_counted(bank: Path) -> None:
    _write(bank, "global/decision-log.md", "# Decision Log\n\n### [DATE] - [TITLE]\n**Context:** [Fill in]\n")
    assert "global/decision-log.md: 0 entries" in memory.build_digest(bank)


def test_folded_summary_is_shown_for_narrative_file(bank: Path) -> None:
    digest = memory.build_digest(bank)
    assert "Hub for onboarding. Scope is ingestion." in digest


def test_missing_summary_falls_back_to_capped_outline(bank: Path) -> None:
    digest = memory.build_digest(bank)
    assert "global/tech-context.md" in digest
    tech_block = digest.split("global/tech-context.md")[1].split("###")[0]
    assert "summary missing" in tech_block
    assert "Development Setup" in tech_block and "Known Risks" in tech_block

    headings = "".join(f"## Heading number {index:03d}\nbody\n" for index in range(200))
    _write(bank, "global/system-patterns.md", "# Patterns\n" + headings)
    digest = memory.build_digest(bank)
    block = digest.split("global/system-patterns.md")[1].split("\n### ")[0]
    outline = block.split("\n", 1)[1]
    assert len(outline) <= memory.OUTLINE_MAX_CHARS + len("Outline: ") + 1
    assert outline.rstrip().endswith("…")


def test_placeholder_summary_counts_as_missing(bank: Path) -> None:
    _write(
        bank,
        "global/product-context.md",
        '---\nsummary: "[Fill in: up to 5 lines]"\n---\n# Product\n\n## Why\nx\n',
    )
    block = memory.build_digest(bank).split("global/product-context.md")[1].split("\n### ")[0]
    assert "summary missing" in block


def test_roadmap_is_one_extended_line(bank: Path) -> None:
    digest = memory.build_digest(bank)
    assert "ledger/roadmap.md" in digest
    assert "r" * 50 not in digest


def test_digest_tolerates_missing_and_legacy_files(tmp_path: Path) -> None:
    assert "No memory bank" in memory.build_digest(tmp_path)

    (tmp_path / "docs" / "memory" / "active_tasks").mkdir(parents=True)
    digest = memory.build_digest(tmp_path)
    assert "## Open tasks" in digest and "(none)" in digest

    _write(tmp_path, "ledger/progress.md", "﻿# Progress\r\n\r\n## O que funciona\r\n- x\r\n")
    _write(tmp_path, "global/project-brief.md", "---\ntitle: never closed\n# Brief\n## Scope\n")
    _write(tmp_path, "active_tasks/005-legacy.md", "# 005 legacy task without frontmatter\n")
    digest = memory.build_digest(tmp_path)
    assert "no `## Current state` section" in digest
    assert "005 | UNKNOWN | 005-legacy" in digest
    assert "global/project-brief.md" in digest


# =============================================================================
# Task 3: paced SETUP block
# =============================================================================


def _narrative(size: int) -> str:
    return "# N\n\n## Section\n" + "x" * size


def test_setup_block_respects_budget_largest_first(tmp_path: Path) -> None:
    _write(tmp_path, "global/project-brief.md", _narrative(30_000))
    _write(tmp_path, "global/product-context.md", _narrative(25_000))
    _write(tmp_path, "global/tech-context.md", _narrative(20_000))
    _write(tmp_path, "global/domain-glossary.md", _narrative(4_000))
    digest = memory.build_digest(tmp_path, budget=60_000)
    setup = digest[digest.index("SETUP:"):]
    listed = [line for line in setup.splitlines() if line.startswith("- docs/memory/")]
    assert [line.split()[1] for line in listed] == [
        "docs/memory/global/project-brief.md",
        "docs/memory/global/product-context.md",
        "docs/memory/global/domain-glossary.md",
    ]
    assert "Deferred to later sessions: 1 file" in setup
    assert "summary:" in setup and "5 lines" in setup
    assert digest.rstrip().endswith(setup.rstrip())


def test_setup_lists_largest_file_alone_when_it_exceeds_budget(tmp_path: Path) -> None:
    _write(tmp_path, "global/system-patterns.md", _narrative(90_000))
    selected, deferred = memory.select_setup(
        [memory.SetupCandidate("global/system-patterns.md", 90_000)], budget=60_000
    )
    assert [c.relative for c in selected] == ["global/system-patterns.md"]
    assert deferred == 0


def test_no_setup_block_when_all_summaries_present(bank: Path) -> None:
    _write(bank, "global/tech-context.md", "---\nsummary: Dev setup and risks.\n---\n# Tech\n")
    assert "SETUP:" not in memory.build_digest(bank)


# =============================================================================
# Task 4: stats and CLI wiring
# =============================================================================


def test_stats_reports_legacy_core_total_and_digest_size(tmp_path: Path) -> None:
    brief = _write(tmp_path, "global/project-brief.md", "b" * 1_000)
    log = _write(tmp_path, "global/decision-log.md", "d" * 2_000)
    progress = _write(tmp_path, "ledger/progress.md", "## Current state\n- x\n" + "p" * 3_000)
    _write(tmp_path, "ledger/learnings.md", "l" * 7_000)
    _write(tmp_path, "ledger/roadmap.md", "r" * 9_000)
    open_task = _write(tmp_path, "active_tasks/001-open.md", _task("001", "PLANNING", "Open", "g", "t" * 4_000))
    _write(tmp_path, "active_tasks/002-done.md", _task("002", "DONE", "Done", "g", "t" * 5_000))
    _write(tmp_path, "active_tasks/_task-template.md", "x" * 6_000)

    stats = memory.collect_stats(tmp_path)
    expected = sum(len(path.read_text(encoding="utf-8")) for path in (brief, log, progress, open_task))
    assert stats.legacy_core_chars == expected
    assert stats.digest_chars == len(memory.build_digest(tmp_path))

    report = memory.render_stats(stats)
    assert "global/decision-log.md" in report and "ledger/roadmap.md" in report
    assert f"{expected:,}" in report
    assert f"{stats.digest_chars:,}" in report
    assert "_task-template.md" not in report


def test_cli_memory_digest_prints_digest_and_exits_zero(
    bank: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import spine

    assert spine.main(["memory", "digest", "--project-root", str(bank)]) == 0
    out = capsys.readouterr().out
    assert out.startswith("# Memory digest")
    assert "009 | IN_PROGRESS | Ninth — Do nine" in out


def test_cli_memory_stats_exits_zero(bank: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import spine

    assert spine.main(["memory", "stats", f"--project-root={bank}", "--budget", "1000"]) == 0
    assert "Legacy Core SYNC" in capsys.readouterr().out


def test_cli_memory_budget_changes_setup_selection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import spine

    _write(tmp_path, "global/project-brief.md", _narrative(3_000))
    _write(tmp_path, "global/tech-context.md", _narrative(2_000))
    assert spine.main(["memory", "digest", "--project-root", str(tmp_path), "--budget", "3500"]) == 0
    assert "Deferred to later sessions: 1 file" in capsys.readouterr().out


def test_cli_memory_missing_project_root_exits_one(tmp_path: Path) -> None:
    import spine

    assert spine.main(["memory", "digest", "--project-root", str(tmp_path / "nope")]) == 1
