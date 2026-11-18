"""Tests for the open-task health check (spine_cli.memory.check_open_tasks, spine_validate.py memory)."""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402

TODAY = date(2026, 11, 16)


def _task(root: Path, name: str, frontmatter: str | None) -> None:
    """Write ``active_tasks/<name>`` with ``frontmatter`` (``None`` writes a file without frontmatter)."""
    path = root / "docs" / "memory" / "active_tasks" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    head = f"---\n{frontmatter}\n---\n" if frontmatter is not None else ""
    path.write_text(f"{head}# {name}\n", encoding="utf-8")


def _days_ago(days: int, today: date = TODAY) -> str:
    return (today - timedelta(days=days)).isoformat()


def _check(root: Path, today: date = TODAY) -> memory.OpenTasksCheck:
    check = memory.check_open_tasks(root, today)
    assert check is not None
    return check


def _problem(check: memory.OpenTasksCheck, marker: str) -> str:
    matches = [problem for problem in check.problems if marker in problem]
    assert len(matches) == 1, f"expected one problem with {marker!r}, got {check.problems}"
    return matches[0]


# =============================================================================
# Task 1: check function
# =============================================================================


def test_open_tasks_without_valid_status_are_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-no-frontmatter.md", None)
    _task(tmp_path, "002-no-status.md", "task_id: 002\ntitle: No status")
    _task(tmp_path, "003-blocked.md", "task_id: 003\nstatus: BLOCKED")

    check = _check(tmp_path)

    assert len(check.problems) == 1
    problem = _problem(check, "without a valid `status:`")
    assert problem.startswith("3 tasks without a valid `status:`")
    for name in ("001-no-frontmatter.md", "002-no-status.md", "003-blocked.md"):
        assert name in problem
    assert "completed_tasks/" in problem


def test_standard_statuses_are_not_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-planning.md", f"status: planning\nupdated_at: {_days_ago(400)}")
    _task(tmp_path, "002-in-progress.md", f"status: IN_PROGRESS\nupdated_at: {_days_ago(365)}")
    _task(tmp_path, "003-review.md", f"status: Review\nupdated_at: {_days_ago(1)}")

    check = _check(tmp_path)

    assert check.problems == ()
    assert check.tasks == 3


def test_review_older_than_threshold_is_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-old-review.md", f"status: REVIEW\nupdated_at: {_days_ago(memory.STALE_REVIEW_DAYS + 1)}")

    problem = _problem(_check(tmp_path), "REVIEW")

    assert problem.startswith(f"1 REVIEW task not updated in over {memory.STALE_REVIEW_DAYS} days")
    assert "001-old-review.md" in problem
    assert "/spine-harvest" in problem
    assert "IN_PROGRESS" in problem


def test_review_at_threshold_is_not_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-review.md", f"status: REVIEW\nupdated_at: {_days_ago(memory.STALE_REVIEW_DAYS)}")

    assert _check(tmp_path).problems == ()


def test_review_without_updated_at_is_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-no-date.md", "status: REVIEW")
    _task(tmp_path, "002-bad-date.md", "status: REVIEW\nupdated_at: soon")

    problem = _problem(_check(tmp_path), "REVIEW")

    assert problem.startswith("2 REVIEW tasks")
    assert "001-no-date.md" in problem and "002-bad-date.md" in problem


def test_done_tasks_left_in_active_tasks_are_flagged(tmp_path: Path) -> None:
    _task(tmp_path, "001-done.md", "status: DONE")
    _task(tmp_path, "002-open.md", "status: IN_PROGRESS")

    check = _check(tmp_path)

    problem = _problem(check, "DONE")
    assert problem.startswith("1 DONE task still in active_tasks/")
    assert "001-done.md" in problem
    assert "git mv" in problem and "completed_tasks/" in problem
    assert check.tasks == 1


# =============================================================================
# Task 2: spine_validate.py memory
# =============================================================================


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spine_validate", REPO_ROOT / "scripts" / "spine_validate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sv = _load_validator()


def _run_validator(
    root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str, str]:
    monkeypatch.chdir(root)
    code = sv.main(["memory"])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_validate_memory_warns_on_stale_open_tasks_exit_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _task(tmp_path, "001-legacy.md", None)
    _task(tmp_path, "002-review.md", f"status: REVIEW\nupdated_at: {_days_ago(30, date.today())}")
    _task(tmp_path, "003-done.md", "status: DONE")

    code, out, err = _run_validator(tmp_path, monkeypatch, capsys)

    assert code == 0
    scope = memory.OPEN_TASKS_SCOPE
    assert f"WARNING: {scope}: 1 task without a valid `status:` — 001-legacy.md" in err
    assert f"WARNING: {scope}: 1 REVIEW task not updated in over {memory.STALE_REVIEW_DAYS} days — 002-review.md" in err
    assert f"WARNING: {scope}: 1 DONE task still in active_tasks/ — 003-done.md" in err
    assert f"{scope}: OK" not in out


def test_open_task_warning_caps_file_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    total = memory.PROBLEM_FILES_SHOWN + 2
    for index in range(1, total + 1):
        _task(tmp_path, f"{index:03d}-legacy.md", None)

    _, _, err = _run_validator(tmp_path, monkeypatch, capsys)

    shown = ", ".join(f"{index:03d}-legacy.md" for index in range(1, memory.PROBLEM_FILES_SHOWN + 1))
    assert f"{total} tasks without a valid `status:` — {shown} (+2 more)" in err
    assert f"{total:03d}-legacy.md" not in err


def test_validate_memory_open_tasks_ok_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _task(tmp_path, "001-planning.md", "status: PLANNING")
    _task(tmp_path, "002-review.md", f"status: REVIEW\nupdated_at: {date.today().isoformat()}")

    code, out, err = _run_validator(tmp_path, monkeypatch, capsys)

    assert code == 0
    assert f"{memory.OPEN_TASKS_SCOPE}: OK" in out
    assert "2 open task(s), no stale tasks" in out
    assert memory.OPEN_TASKS_SCOPE not in err


def test_task_template_is_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _task(tmp_path, "_task-template.md", "status: [PLANNING | IN_PROGRESS]")

    _, out, err = _run_validator(tmp_path, monkeypatch, capsys)

    assert "_task-template.md" not in err
    assert "0 open task(s), no stale tasks" in out


def test_no_active_tasks_dir_skips_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "docs" / "memory" / "ledger").mkdir(parents=True)

    code, out, err = _run_validator(tmp_path, monkeypatch, capsys)

    assert code == 0
    assert memory.OPEN_TASKS_SCOPE not in out + err


# =============================================================================
# Task 3: harvest step, rule and docs
# =============================================================================


def _read(relative: str) -> str:
    return memory.read_text(REPO_ROOT / relative)


def test_harvest_explains_own_task_review_warning() -> None:
    text = _read("commands/spine-harvest.md")
    step = text.split("**4c.1 Ledger index and memory budgets", 1)[1].split("**4d.", 1)[0]

    assert "REVIEW" in step
    assert f"{memory.STALE_REVIEW_DAYS} days" in step
    assert "being harvested" in step and "step 5" in step
    assert "completed_tasks/" in step


@pytest.mark.parametrize("relative", ["rules/02-memory-bank.md", "README.md", "AGENTS.md"])
def test_docs_list_open_task_warnings(relative: str) -> None:
    text = _read(relative)
    if relative.startswith("rules/"):
        text = text.split("## Memory budgets", 1)[1].split("\n## ", 1)[0]
    else:
        text = text.split("**Memory budgets:**", 1)[1].split("\n\n", 1)[0]

    assert f"{memory.STALE_REVIEW_DAYS} days" in text
    assert "completed_tasks/" in text
    assert "status" in text
