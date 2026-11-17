"""Tests for ``spine_validate.py staged`` (pre-commit memory check on the staged snapshot)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import spine_validate  # noqa: E402
from spine_cli import memory  # noqa: E402

TEMPLATE_MEMORY = REPO_ROOT / "templates" / "docs" / "memory"
TASK_PATH = "docs/memory/active_tasks/001-sample-task.md"
DELIVERIES = "docs/memory/ledger/deliveries"

VALID_TASK = """---
task_id: 001
title: Sample task
goal: Prove the staged check
status: PLANNING
tags:
  - type/feature
branch: feature/sample-task
base: develop
created_at: 2026-11-17
updated_at: 2026-11-17
---

# 001-sample-task

## Objective

Text.

## Acceptance Criteria

- [ ] AC1
"""

EMPTY_TAGS_TASK = VALID_TASK.replace("tags:\n  - type/feature\n", "tags: []\n")

LEGACY_TASK = """# 002-legacy-task

**Status:** DONE
**Branch:** feature/legacy

Old task without frontmatter.
"""


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return result.stdout


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _entry(day: int, summary: str | None = "Delivered something.") -> str:
    lines = ["---", f"id: 2026-11-{day:02d}-001-sample", f"date: 2026-11-{day:02d}", "title: Sample delivery"]
    if summary is not None:
        lines.append(f"summary: {summary}")
    lines += ["tags:", "  - area/memory", "task: 001-sample-task", "---", "", "# Sample delivery", ""]
    return "\n".join(lines)


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Real git repository with the seeded memory bank committed; cwd is its root."""
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "commit.gpgsign", "false")
    shutil.copytree(TEMPLATE_MEMORY, root / "docs" / "memory")
    memory.write_indexes(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    monkeypatch.chdir(root)
    return root


def _run(capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    code = spine_validate.main(["staged"])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# --- AC1: task contract on the staged snapshot -------------------------------


def test_staged_task_contract_error_blocks(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(git_repo, TASK_PATH, EMPTY_TAGS_TASK)
    _git(git_repo, "add", TASK_PATH)

    code, _, err = _run(capsys)

    assert code == 1
    assert f"ERROR: {TASK_PATH}: tags list empty" in err
    assert "Commit blocked: 1 memory error(s)." in err


def test_unstaged_fix_still_blocks(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(git_repo, TASK_PATH, EMPTY_TAGS_TASK)
    _git(git_repo, "add", TASK_PATH)
    _write(git_repo, TASK_PATH, VALID_TASK)

    code, _, err = _run(capsys)
    assert code == 1
    assert "tags list empty" in err

    _git(git_repo, "add", TASK_PATH)
    code, _, err = _run(capsys)
    assert code == 0
    assert "ERROR:" not in err


def test_pure_rename_of_legacy_task_is_not_checked(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy = "docs/memory/active_tasks/002-legacy-task.md"
    _write(git_repo, legacy, LEGACY_TASK)
    _git(git_repo, "add", legacy)
    _git(git_repo, "commit", "-q", "--no-verify", "-m", "legacy")
    _git(git_repo, "mv", legacy, "docs/memory/completed_tasks/002-legacy-task.md")

    code, _, err = _run(capsys)

    assert code == 0
    assert "ERROR:" not in err


def test_modified_legacy_task_is_checked(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy = "docs/memory/active_tasks/002-legacy-task.md"
    _write(git_repo, legacy, LEGACY_TASK)
    _git(git_repo, "add", legacy)
    _git(git_repo, "commit", "-q", "--no-verify", "-m", "legacy")
    _write(git_repo, legacy, LEGACY_TASK + "\nMore text.\n")
    _git(git_repo, "add", legacy)

    code, _, err = _run(capsys)

    assert code == 1
    assert f"ERROR: {legacy}: missing YAML frontmatter" in err


# --- AC3: warnings, fast path, outside git -----------------------------------


def test_open_task_warning_does_not_block(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    review_task = VALID_TASK.replace("status: PLANNING", "status: REVIEW").replace(
        "updated_at: 2026-11-17", "updated_at: 2020-01-01"
    )
    _write(git_repo, TASK_PATH, review_task)
    _git(git_repo, "add", TASK_PATH)

    code, out, err = _run(capsys)

    assert code == 0
    assert "WARNING:" in err
    assert "REVIEW task not updated" in err
    assert "ERROR:" not in err
    assert "OK:" not in out


def test_no_memory_files_staged_is_silent(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(git_repo, "src/app.py", "print('hi')\n")
    _git(git_repo, "add", "src/app.py")

    code, out, err = _run(capsys)

    assert code == 0
    assert out == ""
    assert err == ""


def test_outside_git_repo_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = tmp_path / "plain"
    outside.mkdir()
    monkeypatch.chdir(outside)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    code, _, err = _run(capsys)

    assert code == 1
    assert "ERROR:" in err


# --- AC2: ledger entries and INDEX.md -----------------------------------------


def _index(root: Path) -> None:
    memory.write_indexes(root)


def test_changed_entry_without_summary_blocks(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    entry = f"{DELIVERIES}/2026-11-17-001-sample.md"
    _write(git_repo, entry, _entry(17, summary=None))
    _index(git_repo)
    _git(git_repo, "add", "docs/memory")

    code, _, err = _run(capsys)

    assert code == 1
    assert f"ERROR: {entry}: missing `summary:`" in err
    assert "INDEX.md" not in err


def test_over_long_summary_blocks(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    entry = f"{DELIVERIES}/2026-11-17-001-sample.md"
    _write(git_repo, entry, _entry(17, summary="x" * (memory.ENTRY_SUMMARY_MAX_CHARS + 1)))
    _index(git_repo)
    _git(git_repo, "add", "docs/memory")

    code, _, err = _run(capsys)

    assert code == 1
    assert f"ERROR: {entry}: `summary:` is 161 chars (max 160)" in err


def test_stale_index_in_touched_folder_blocks(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    entry = f"{DELIVERIES}/2026-11-17-001-sample.md"
    _write(git_repo, entry, _entry(17))
    _git(git_repo, "add", entry)

    code, _, err = _run(capsys)
    assert code == 1
    assert f"ERROR: {DELIVERIES}/INDEX.md is stale — run python3 .spine/scripts/spine.py memory index, then git add it" in err

    _index(git_repo)
    code, _, err = _run(capsys)
    assert code == 1, "regenerated INDEX.md not staged yet"

    _git(git_repo, "add", f"{DELIVERIES}/INDEX.md")
    code, _, err = _run(capsys)
    assert code == 0
    assert "ERROR:" not in err


def test_deleted_entry_requires_fresh_index(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    entry = f"{DELIVERIES}/2026-11-17-001-sample.md"
    _write(git_repo, entry, _entry(17))
    _index(git_repo)
    _git(git_repo, "add", "docs/memory")
    _git(git_repo, "commit", "-q", "--no-verify", "-m", "entry")
    _git(git_repo, "rm", "-q", entry)

    code, _, err = _run(capsys)

    assert code == 1
    assert f"{DELIVERIES}/INDEX.md is stale" in err


def test_untouched_entry_problems_do_not_block(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    legacy = f"{DELIVERIES}/2026-11-10-001-legacy.md"
    _write(git_repo, legacy, _entry(10, summary=None))
    _index(git_repo)
    _git(git_repo, "add", "docs/memory")
    _git(git_repo, "commit", "-q", "--no-verify", "-m", "legacy entry")

    entry = f"{DELIVERIES}/2026-11-17-001-sample.md"
    _write(git_repo, entry, _entry(17))
    _index(git_repo)
    _git(git_repo, "add", "docs/memory")

    code, _, err = _run(capsys)

    assert code == 0
    assert "ERROR:" not in err


def test_project_in_subdirectory_of_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "mono"
    project = repo / "services" / "api"
    project.mkdir(parents=True)
    _git(repo, "init", "-q")
    shutil.copytree(TEMPLATE_MEMORY, project / "docs" / "memory")
    memory.write_indexes(project)
    _write(project, TASK_PATH, EMPTY_TAGS_TASK)
    _git(repo, "add", "-A")
    monkeypatch.chdir(project)

    code, _, err = _run(capsys)

    assert code == 1
    assert f"ERROR: {TASK_PATH}: tags list empty" in err
    assert "INDEX.md" not in err
