"""Tests for the Spine git pre-commit hook block (spine_cli.precommit and installer wiring)."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import precommit  # noqa: E402
from spine_cli.log import Log  # noqa: E402

EXISTING_SH_HOOK = "#!/usr/bin/env bash\necho existing\nexit 0\n"


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


@pytest.fixture(autouse=True)
def _isolated_git_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ignore the user's global/system git config (e.g. a global core.hooksPath)."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Empty git repository."""
    root = tmp_path / "project"
    root.mkdir()
    _git(root, "init", "-q")
    return root


def _hook(root: Path) -> Path:
    return root / ".git" / "hooks" / "pre-commit"


# --- AC4: install ------------------------------------------------------------


def test_install_creates_executable_hook(repo: Path) -> None:
    assert precommit.install_hook(repo, Log()) is True

    hook = _hook(repo)
    text = hook.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh\n# >>> spine pre-commit >>>\n")
    assert ".spine/scripts/spine_validate.py staged || exit 1" in text
    assert text.rstrip().endswith("# <<< spine pre-commit <<<")
    assert hook.stat().st_mode & stat.S_IXUSR
    assert precommit.hook_installed(repo)


def test_install_is_idempotent(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    precommit.install_hook(repo, Log())
    first = _hook(repo).read_text(encoding="utf-8")
    capsys.readouterr()

    log = Log()
    precommit.install_hook(repo, log)

    assert _hook(repo).read_text(encoding="utf-8") == first
    assert log.skipped == 1
    assert log.linked == 0


def test_install_refreshes_an_outdated_block(repo: Path) -> None:
    hook = _hook(repo)
    hook.write_text(
        f"#!/bin/sh\necho before\n{precommit.BLOCK_START}\nold body\n{precommit.BLOCK_END}\necho after\n",
        encoding="utf-8",
    )

    precommit.install_hook(repo, Log())

    text = hook.read_text(encoding="utf-8")
    assert "old body" not in text
    assert text == f"#!/bin/sh\necho before\n{precommit.BLOCK}echo after\n"


def test_install_respects_core_hooks_path(repo: Path) -> None:
    _git(repo, "config", "core.hooksPath", "githooks")

    precommit.install_hook(repo, Log())

    assert (repo / "githooks" / "pre-commit").is_file()
    assert not _hook(repo).exists()


def test_install_inserts_after_shebang_of_existing_hook(repo: Path) -> None:
    hook = _hook(repo)
    hook.write_text(EXISTING_SH_HOOK, encoding="utf-8")
    hook.chmod(0o755)

    precommit.install_hook(repo, Log())

    text = hook.read_text(encoding="utf-8")
    assert text == f"#!/usr/bin/env bash\n{precommit.BLOCK}echo existing\nexit 0\n"
    assert hook.stat().st_mode & stat.S_IXUSR


@pytest.mark.parametrize(
    "content",
    [
        "#!/usr/bin/env python3\nprint('hook')\n",
        "echo no shebang\n",
        '#!/usr/bin/env sh\n. "$(dirname "$0")/husky.sh"\nnpx lint-staged\n',
    ],
    ids=["python", "no-shebang", "husky"],
)
def test_non_shell_hook_is_left_untouched(repo: Path, content: str, capsys: pytest.CaptureFixture[str]) -> None:
    hook = _hook(repo)
    hook.write_text(content, encoding="utf-8")

    assert precommit.install_hook(repo, Log()) is False

    assert hook.read_text(encoding="utf-8") == content
    out = capsys.readouterr().out
    assert "NOTE:" in out
    assert precommit.MANUAL_LINE in out


def test_install_outside_git_warns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    log = Log()

    assert precommit.install_hook(tmp_path, log) is False
    assert log.warnings == 1


# --- AC5: uninstall and dry run ------------------------------------------------


def test_uninstall_removes_only_the_block(repo: Path) -> None:
    hook = _hook(repo)
    hook.write_text(EXISTING_SH_HOOK, encoding="utf-8")
    precommit.install_hook(repo, Log())

    precommit.uninstall_hook(repo, Log())

    assert hook.read_text(encoding="utf-8") == EXISTING_SH_HOOK
    assert not precommit.hook_installed(repo)


def test_uninstall_deletes_file_left_empty(repo: Path) -> None:
    precommit.install_hook(repo, Log())

    precommit.uninstall_hook(repo, Log())

    assert not _hook(repo).exists()


def test_uninstall_without_block_is_a_no_op(repo: Path) -> None:
    hook = _hook(repo)
    hook.write_text(EXISTING_SH_HOOK, encoding="utf-8")
    log = Log()

    precommit.uninstall_hook(repo, log)

    assert hook.read_text(encoding="utf-8") == EXISTING_SH_HOOK
    assert log.skipped == 1


def test_dry_run_writes_nothing(repo: Path) -> None:
    precommit.install_hook(repo, Log(dry_run=True))
    assert not _hook(repo).exists()

    hook = _hook(repo)
    hook.write_text(EXISTING_SH_HOOK, encoding="utf-8")
    precommit.install_hook(repo, Log(dry_run=True))
    assert hook.read_text(encoding="utf-8") == EXISTING_SH_HOOK

    precommit.install_hook(repo, Log())
    installed = hook.read_text(encoding="utf-8")
    precommit.uninstall_hook(repo, Log(dry_run=True))
    assert hook.read_text(encoding="utf-8") == installed


# --- AC5: installer flags, prompt, spine.py uninstall ------------------------


def _spine(*args: str) -> int:
    import spine

    return spine.main(list(args))


def _install(project: Path, *extra: str) -> int:
    return _spine(
        "install",
        "--project-root",
        str(project),
        "--spine-dir",
        str(REPO_ROOT),
        "--skills=writing-plans",
        "--targets=cursor",
        "--no-graphify-prompt",
        "--no-mkdocs-prompt",
        *extra,
    )


def test_install_flag_installs_and_side_command_uninstalls(repo: Path) -> None:
    assert _install(repo, "--with-pre-commit") == 0
    assert precommit.hook_installed(repo)

    assert _spine("install", "--project-root", str(repo), "--pre-commit-uninstall") == 0
    assert not _hook(repo).exists()
    assert (repo / ".spine").is_symlink(), "side command leaves the rest of the install in place"


def test_install_without_flag_does_not_touch_hook(repo: Path) -> None:
    assert _install(repo) == 0
    assert not _hook(repo).exists()


def test_spine_uninstall_removes_the_block(repo: Path) -> None:
    hook = _hook(repo)
    hook.write_text(EXISTING_SH_HOOK, encoding="utf-8")
    assert _install(repo, "--with-pre-commit") == 0
    assert precommit.hook_installed(repo)

    assert _spine("uninstall", "--project-root", str(repo)) == 0

    assert hook.read_text(encoding="utf-8") == EXISTING_SH_HOOK


class _Stdin:
    def __init__(self, tty: bool) -> None:
        self.tty = tty

    def isatty(self) -> bool:
        return self.tty


def test_prompt_skipped_when_installed_or_not_tty(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from spine_cli import install
    from spine_cli.options import Options

    asked: list[str] = []
    monkeypatch.setattr("builtins.input", lambda question: asked.append(question) or "y")

    monkeypatch.setattr(sys, "stdin", _Stdin(tty=False))
    options = Options(project_root=repo)
    install._maybe_prompt_pre_commit(repo, options)
    assert asked == [] and not options.with_pre_commit

    monkeypatch.setattr(sys, "stdin", _Stdin(tty=True))
    options = Options(project_root=repo, with_pre_commit=True)
    install._maybe_prompt_pre_commit(repo, options)
    assert asked == []

    options = Options(project_root=repo)
    install._maybe_prompt_pre_commit(repo, options)
    assert len(asked) == 1
    assert "Enable the git pre-commit memory check for this project? [Y/n]" in asked[0]
    assert options.with_pre_commit

    precommit.install_hook(repo, Log())
    options = Options(project_root=repo)
    install._maybe_prompt_pre_commit(repo, options)
    assert len(asked) == 1, "no prompt once the block is installed"


def test_install_dry_run_flag_writes_nothing(repo: Path) -> None:
    assert _install(repo, "--with-pre-commit", "--dry-run") == 0
    assert not _hook(repo).exists()



# --- AC6: end to end through git commit ---------------------------------------

BROKEN_TASK = """---
task_id: 001
title: Sample task
goal: Prove the hook
status: PLANNING
tags: []
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
FIXED_TASK = BROKEN_TASK.replace("tags: []\n", "tags:\n  - type/feature\n")
E2E_TASK = "docs/memory/active_tasks/001-sample-task.md"


@pytest.fixture
def wired_repo(repo: Path) -> Path:
    """Repository with ``.spine`` → this clone, the seeded memory bank and the hook block."""
    from spine_cli import memory

    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / ".spine").symlink_to(REPO_ROOT)
    (repo / ".gitignore").write_text(".spine\n", encoding="utf-8")
    shutil.copytree(REPO_ROOT / "templates" / "docs" / "memory", repo / "docs" / "memory")
    memory.write_indexes(repo)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-verify", "-m", "seed")
    precommit.install_hook(repo, Log())
    return repo


def _commit(root: Path, message: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, capture_output=True, text=True, check=False)


def test_git_commit_blocked_then_allowed(wired_repo: Path) -> None:
    task = wired_repo / E2E_TASK
    task.write_text(BROKEN_TASK, encoding="utf-8")
    _git(wired_repo, "add", E2E_TASK)

    blocked = _commit(wired_repo, "broken task")
    assert blocked.returncode != 0
    assert f"ERROR: {E2E_TASK}: tags list empty" in blocked.stderr
    assert "Commit blocked: 1 memory error(s)." in blocked.stderr

    task.write_text(FIXED_TASK, encoding="utf-8")
    _git(wired_repo, "add", E2E_TASK)
    allowed = _commit(wired_repo, "fixed task")
    assert allowed.returncode == 0, allowed.stderr
    assert _git(wired_repo, "log", "--format=%s", "-1").stdout.strip() == "fixed task"


def test_missing_spine_skips_with_note(wired_repo: Path) -> None:
    (wired_repo / ".spine").unlink()
    (wired_repo / E2E_TASK).write_text(BROKEN_TASK, encoding="utf-8")
    _git(wired_repo, "add", E2E_TASK)

    result = _commit(wired_repo, "no spine")

    assert result.returncode == 0, result.stderr
    assert "spine pre-commit: .spine not found; memory validation skipped" in result.stderr


def test_missing_python_skips_with_note(wired_repo: Path) -> None:
    (wired_repo / E2E_TASK).write_text(BROKEN_TASK, encoding="utf-8")
    _git(wired_repo, "add", E2E_TASK)
    bin_dir = wired_repo.parent / "bin-no-python"
    bin_dir.mkdir()
    for tool in ("git", "sh", "echo", "cat"):
        found = shutil.which(tool)
        if found:
            (bin_dir / tool).symlink_to(found)
    env = {**os.environ, "PATH": str(bin_dir)}

    result = subprocess.run(
        ["git", "commit", "-q", "-m", "no python"], cwd=wired_repo, capture_output=True, text=True, env=env, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "spine pre-commit: python not found; memory validation skipped" in result.stderr
