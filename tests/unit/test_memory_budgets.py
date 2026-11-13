"""Tests for memory budgets (spine_cli.memory.check_budgets, spine_validate.py memory)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402

SUMMARY_FRONTMATTER = "---\nsummary: >-\n  Short agent-written summary.\n---\n"
TASK_GOAL_CHARS = 300
FILLER = "x"


def _write(root: Path, relative: str, text: str) -> None:
    path = root / "docs" / "memory" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _progress(state_chars: int, total_chars: int = 0) -> str:
    """Build a progress.md with a Current state of ``state_chars`` and an overall size of ``total_chars``."""
    head = "## Current state\n"
    state = FILLER * state_chars
    log_head = "\n\n## Delivery log (newest first)\n"
    text = head + state + log_head
    return text + FILLER * max(0, total_chars - len(text))


def _check(checks: list[memory.BudgetCheck], scope: str) -> memory.BudgetCheck:
    matches = [check for check in checks if check.scope == scope]
    assert len(matches) == 1, f"expected one check for {scope}, got {[c.scope for c in checks]}"
    return matches[0]


def _many_open_tasks(root: Path, count: int) -> None:
    for index in range(1, count + 1):
        _write(
            root,
            f"active_tasks/{index:03d}-task.md",
            f"---\ntask_id: {index:03d}\ntitle: Task {index}\nstatus: PLANNING\n"
            f"goal: {'g' * TASK_GOAL_CHARS}\n---\n",
        )


def _log_scope(relative: str) -> str:
    return f"{memory.MEMORY_DIR.as_posix()}/{relative}"


# =============================================================================
# Task 1: budget model
# =============================================================================


@pytest.mark.parametrize(
    ("relative", "limit"),
    [
        ("global/decision-log.md", memory.LOG_BUDGET_CHARS["global/decision-log.md"]),
        ("ledger/learnings.md", memory.LOG_BUDGET_CHARS["ledger/learnings.md"]),
    ],
)
def test_check_budgets_flags_log_files_over_limit(tmp_path: Path, relative: str, limit: int) -> None:
    _write(tmp_path, relative, FILLER * limit)
    assert not _check(memory.check_budgets(tmp_path), _log_scope(relative)).over

    _write(tmp_path, relative, FILLER * (limit + 1))
    check = _check(memory.check_budgets(tmp_path), _log_scope(relative))
    assert check.over
    assert (check.chars, check.limit) == (limit + 1, limit)


def test_check_budgets_flags_each_scope_over_limit(tmp_path: Path) -> None:
    progress_limit = memory.LOG_BUDGET_CHARS["ledger/progress.md"]
    _write(tmp_path, "ledger/progress.md", _progress(memory.CURRENT_STATE_BUDGET_CHARS, progress_limit))
    _write(tmp_path, "global/system-patterns.md", SUMMARY_FRONTMATTER + FILLER * memory.NARRATIVE_BODY_BUDGET_CHARS)
    checks = memory.check_budgets(tmp_path)
    assert not any(check.over for check in checks)

    _write(tmp_path, "ledger/progress.md", _progress(memory.CURRENT_STATE_BUDGET_CHARS + 1, progress_limit + 1))
    _write(
        tmp_path, "global/system-patterns.md", SUMMARY_FRONTMATTER + FILLER * (memory.NARRATIVE_BODY_BUDGET_CHARS + 1)
    )
    _many_open_tasks(tmp_path, memory.DIGEST_BUDGET_CHARS // TASK_GOAL_CHARS)
    checks = memory.check_budgets(tmp_path)

    assert _check(checks, memory.CURRENT_STATE_SCOPE).over
    assert _check(checks, _log_scope("ledger/progress.md")).over
    assert _check(checks, _log_scope("global/system-patterns.md")).over
    digest = _check(checks, memory.DIGEST_SCOPE)
    assert digest.over
    assert digest.limit == memory.DIGEST_BUDGET_CHARS
    assert digest.chars == len(memory.build_digest(tmp_path))


def test_current_state_budget_measures_the_block_only(tmp_path: Path) -> None:
    _write(tmp_path, "ledger/progress.md", _progress(memory.CURRENT_STATE_BUDGET_CHARS, 5_000))
    check = _check(memory.check_budgets(tmp_path), memory.CURRENT_STATE_SCOPE)
    assert check.chars == memory.CURRENT_STATE_BUDGET_CHARS
    assert not check.over


def test_narrative_budget_excludes_frontmatter(tmp_path: Path) -> None:
    long_frontmatter = "---\nsummary: >-\n" + "  word\n" * 1_000 + "---\n"
    _write(tmp_path, "global/tech-context.md", long_frontmatter + FILLER * memory.NARRATIVE_BODY_BUDGET_CHARS)
    check = _check(memory.check_budgets(tmp_path), _log_scope("global/tech-context.md"))
    assert check.chars == memory.NARRATIVE_BODY_BUDGET_CHARS
    assert not check.over


def test_unbudgeted_files_are_ignored(tmp_path: Path) -> None:
    huge = FILLER * (memory.DIGEST_BUDGET_CHARS * 2)
    _write(tmp_path, "active_tasks/001-big.md", "---\ntask_id: 001\nstatus: PLANNING\n---\n" + huge)
    _write(tmp_path, "ledger/roadmap.md", huge)
    _write(tmp_path, "completed_tasks/002-done.md", "---\nstatus: DONE\n---\n" + huge)

    checks = memory.check_budgets(tmp_path)

    assert [check.scope for check in checks] == [memory.DIGEST_SCOPE]
    assert not checks[0].over


def test_missing_files_are_skipped(tmp_path: Path) -> None:
    (tmp_path / "docs" / "memory").mkdir(parents=True)
    assert [check.scope for check in memory.check_budgets(tmp_path)] == [memory.DIGEST_SCOPE]

    _write(tmp_path, "global/project-brief.md", SUMMARY_FRONTMATTER + "# Brief\n")
    scopes = [check.scope for check in memory.check_budgets(tmp_path)]
    assert scopes == [memory.DIGEST_SCOPE, _log_scope("global/project-brief.md")]


def test_check_budgets_without_memory_dir_returns_nothing(tmp_path: Path) -> None:
    assert memory.check_budgets(tmp_path) == []


def test_digest_section_sizes_are_largest_first() -> None:
    digest = (
        "# Memory digest\n\nintro\n\n"
        f"## Current state\n{FILLER * 2}\n\n## Open tasks\n{FILLER * 80}\n\n## Logs\n{FILLER * 40}\n"
    )
    sizes = memory.digest_section_sizes(digest)
    assert [label for label, _ in sizes] == ["Open tasks", "Logs", "Current state"]
    assert sizes[0][1] > sizes[1][1] > sizes[2][1]


def test_digest_over_budget_names_largest_sections(tmp_path: Path) -> None:
    _write(tmp_path, "ledger/progress.md", _progress(memory.CURRENT_STATE_BUDGET_CHARS))
    _many_open_tasks(tmp_path, memory.DIGEST_BUDGET_CHARS // TASK_GOAL_CHARS)

    digest = _check(memory.check_budgets(tmp_path), memory.DIGEST_SCOPE)

    assert digest.over
    assert digest.detail.index("Open tasks") < digest.detail.index("Current state")
    assert "Extended tier" in digest.detail


def test_digest_has_no_budget_line_when_over_budget(tmp_path: Path) -> None:
    _write(tmp_path, "ledger/progress.md", _progress(memory.CURRENT_STATE_BUDGET_CHARS * 3))
    _many_open_tasks(tmp_path, memory.DIGEST_BUDGET_CHARS // TASK_GOAL_CHARS)
    assert _check(memory.check_budgets(tmp_path), memory.DIGEST_SCOPE).over

    digest = memory.build_digest(tmp_path)

    assert "budget" not in digest.lower()
    assert "WARNING" not in digest
