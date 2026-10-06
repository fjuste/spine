"""Behavioral tests for scripts/spine_validate.py (cross-platform validators)."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "spine_validate.py"

VALID_TASK = """---
task_id: 007
title: Example task
goal: Prove the validator works
status: PLANNING
tags:
  - type/feature
  - area/tooling
branch: feature/example
base: develop
created_at: 2026-10-06
updated_at: 2026-10-06
---

# 007-example

## Objective

Do the thing.

## Acceptance Criteria

- [ ] It works

## Implementation Plan

### Task 1: First step
"""


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spine_validate", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sv = _load_module()


def _write(path: Path, text: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _task(tmp_path: Path, text: str) -> Path:
    return _write(tmp_path / "task.md", text)


def _quiet_task_report(tmp_path: Path, text: str) -> sv.Report:
    return sv.validate_task(_task(tmp_path, text), sv.Report(quiet=True))


# =============================================================================
# task
# =============================================================================


def test_task_valid_file_passes(tmp_path: Path) -> None:
    report = _quiet_task_report(tmp_path, VALID_TASK)
    assert report.errors == 0
    assert report.warnings == 0


def test_task_missing_frontmatter_key_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = sv.validate_task(_task(tmp_path, VALID_TASK.replace("goal: Prove the validator works\n", "")))
    assert report.errors == 1
    assert "frontmatter missing key: goal" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("tags_block", "message"),
    [
        ("tags:\n", "tags list empty"),
        ("tags:\n" + "".join(f"  - t{index}\n" for index in range(6)), "too many tags (6; max 5)"),
    ],
)
def test_task_tag_count_bounds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], tags_block: str, message: str
) -> None:
    text = VALID_TASK.replace("tags:\n  - type/feature\n  - area/tooling\n", tags_block)
    report = sv.validate_task(_task(tmp_path, text))
    assert report.errors == 1
    assert message in capsys.readouterr().err


def test_task_legacy_status_pattern_fails(tmp_path: Path) -> None:
    report = _quiet_task_report(tmp_path, VALID_TASK + "\n**Status:** DONE\n")
    assert report.errors == 1


def test_task_promotional_superpowers_fails_but_prohibition_passes(tmp_path: Path) -> None:
    assert _quiet_task_report(tmp_path, VALID_TASK + "\nUse superpowers:executing-plans\n").errors == 1
    assert _quiet_task_report(tmp_path, VALID_TASK + "\nDo not use superpowers: headers\n").errors == 0


def test_task_missing_section_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    report = sv.validate_task(_task(tmp_path, VALID_TASK.replace("## Acceptance Criteria", "## Criteria")))
    assert report.errors == 1
    assert "missing required section: ## Acceptance Criteria" in capsys.readouterr().err


def test_task_blocks_require_implementation_plan(tmp_path: Path) -> None:
    report = _quiet_task_report(tmp_path, VALID_TASK.replace("## Implementation Plan", "## Plan"))
    assert report.errors == 1


def test_task_without_frontmatter_fails(tmp_path: Path) -> None:
    report = _quiet_task_report(tmp_path, VALID_TASK.split("---\n", 2)[2])
    assert report.errors >= 1


def test_task_crlf_and_bom_pass(tmp_path: Path) -> None:
    path = tmp_path / "task.md"
    path.write_bytes(b"\xef\xbb\xbf" + VALID_TASK.replace("\n", "\r\n").encode("utf-8"))
    assert sv.validate_task(path, sv.Report(quiet=True)).errors == 0


def test_task_non_feature_branch_and_base_warn(tmp_path: Path) -> None:
    text = VALID_TASK.replace("branch: feature/example", "branch: main").replace("base: develop", "base: master")
    report = _quiet_task_report(tmp_path, text)
    assert report.errors == 0
    assert report.warnings == 2


def test_task_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    valid = _task(tmp_path, VALID_TASK)
    assert sv.main(["task", str(valid)]) == 0
    assert "matches Memory Bank v2.1 task contract" in capsys.readouterr().out
    assert sv.main(["task"]) == 1
    assert sv.main(["task", str(tmp_path / "missing.md")]) == 1
    assert sv.main(["task", "--dry-run", str(valid)]) == 0


def test_cli_usage_error_exits_1() -> None:
    with pytest.raises(SystemExit) as excinfo:
        sv.main(["unknown-subcommand"])
    assert excinfo.value.code == 1


# =============================================================================
# bootstrap
# =============================================================================


def _seed_project(root: Path) -> None:
    _write(root / ".spine" / "scripts" / "spine_validate.py")
    _write(root / ".cursor" / "commands" / "spine-bootstrap.md")
    _write(root / "opencode.json", "{}")
    for relative in sv.DOCS_SEED_PATHS:
        _write(root / relative)
    for relative in sv.BOOTSTRAP_REQUIRED_DIRS:
        (root / relative).mkdir(parents=True, exist_ok=True)


def test_bootstrap_seeded_project_passes(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    assert sv.validate_bootstrap(tmp_path, sv.Report(quiet=True)).errors == 0


def test_bootstrap_missing_seed_file_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _seed_project(tmp_path)
    (tmp_path / "docs" / "memory" / "ledger" / "roadmap.md").unlink()
    report = sv.validate_bootstrap(tmp_path)
    assert report.errors == 1
    assert "missing seed file: docs/memory/ledger/roadmap.md" in capsys.readouterr().err


def test_bootstrap_missing_validator_fails(tmp_path: Path) -> None:
    _seed_project(tmp_path)
    (tmp_path / ".spine" / "scripts" / "spine_validate.py").unlink()
    assert sv.validate_bootstrap(tmp_path, sv.Report(quiet=True)).errors == 1


def test_bootstrap_cli_reports_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _seed_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert sv.main(["bootstrap"]) == 0
    assert "OK: project is ready for /spine-bootstrap." in capsys.readouterr().out


# =============================================================================
# graphify
# =============================================================================


def _fake_run(stdout: str = "", returncode: int = 0) -> Callable[..., subprocess.CompletedProcess[str]]:
    def run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")

    return run


def _graphify_project(root: Path) -> None:
    _write(root / "graphify-out" / "graph.json", "{}")
    _write(root / "graphify-out" / "GRAPH_REPORT.md")
    _write(root / ".graphifyignore")
    _write(root / ".cursor" / "rules" / "graphify.mdc")
    _write(root / ".cursor" / "rules" / "02-memory-bank.md")
    _write(root / ".opencode" / "plugins" / "graphify.js")
    _write(root / "opencode.json", '{"plugin": ["graphify"], "instructions": ["02-memory-bank.md"]}')
    _write(root / "CLAUDE.md", "## graphify")
    (root / ".claude" / "skills").mkdir(parents=True)


def test_graphify_complete_integration_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _graphify_project(tmp_path)
    monkeypatch.setattr(sv.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(sv.subprocess, "run", _fake_run("graphify 0.7.16\n"))
    report = sv.validate_graphify(tmp_path, "cursor,opencode,claude", sv.Report(quiet=True))
    assert report.errors == 0
    assert report.warnings == 0


def test_graphify_missing_cli_and_artifacts_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sv.shutil, "which", lambda _name: None)
    report = sv.validate_graphify(tmp_path, "cursor", sv.Report(quiet=True))
    # graph.json, CLI, .cursor/rules/graphify.mdc
    assert report.errors == 3


def test_graphify_target_selection_limits_checks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _graphify_project(tmp_path)
    (tmp_path / ".opencode" / "plugins" / "graphify.js").unlink()
    monkeypatch.setattr(sv.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(sv.subprocess, "run", _fake_run("0.8.0"))
    assert sv.validate_graphify(tmp_path, "cursor,claude", sv.Report(quiet=True)).errors == 0
    assert sv.validate_graphify(tmp_path, "opencode", sv.Report(quiet=True)).errors == 1


def test_graphify_old_version_warns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _graphify_project(tmp_path)
    monkeypatch.setattr(sv.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(sv.subprocess, "run", _fake_run("0.7.2"))
    report = sv.validate_graphify(tmp_path, "cursor", sv.Report(quiet=True))
    assert report.errors == 0
    assert report.warnings == 1


@pytest.mark.parametrize(
    ("text", "expected"),
    [("graphify 0.7.16", (0, 7, 16)), ("1.2.3-beta", (1, 2, 3)), ("unknown", None)],
)
def test_parse_semver(text: str, expected: tuple[int, int, int] | None) -> None:
    assert sv.parse_semver(text) == expected


# =============================================================================
# mkdocs
# =============================================================================


def test_mkdocs_missing_config_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sv.shutil, "which", lambda _name: None)
    report = sv.validate_mkdocs(tmp_path, sv.Report(quiet=True))
    # missing config + mkdocs unavailable
    assert report.errors == 2


@pytest.mark.parametrize("venv_relative", [".venv/bin/mkdocs", ".venv/Scripts/mkdocs.exe"])
def test_mkdocs_resolves_project_venv_on_linux_and_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, venv_relative: str
) -> None:
    _write(tmp_path / venv_relative)
    monkeypatch.setattr(sv.shutil, "which", lambda _name: None)
    runner = sv.resolve_mkdocs_runner(tmp_path)
    assert runner is not None
    assert runner[1] == venv_relative


def test_mkdocs_prefers_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sv.shutil, "which", lambda name: "/usr/bin/uv" if name == "uv" else None)
    runner = sv.resolve_mkdocs_runner(tmp_path)
    assert runner is not None
    assert runner[1] == "uv run --extra docs mkdocs"


def test_mkdocs_complete_integration_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / sv.MKDOCS_CONFIG, "site_name: x\n")
    _write(tmp_path / "docs" / "mkdocs" / "index.md", "# x\n")
    (tmp_path / "docs" / "mkdocs" / "site").mkdir()
    _write(tmp_path / ".gitignore", "docs/mkdocs/site/\n")
    monkeypatch.setattr(sv.shutil, "which", lambda name: "/usr/bin/mkdocs" if name == "mkdocs" else None)
    monkeypatch.setattr(sv.subprocess, "run", _fake_run("mkdocs, version 1.6.1"))
    report = sv.validate_mkdocs(tmp_path, sv.Report(quiet=True))
    assert report.errors == 0
    assert report.warnings == 0


def test_mkdocs_failed_build_only_warns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / sv.MKDOCS_CONFIG, "site_name: x\n")
    _write(tmp_path / "docs" / "mkdocs" / "index.md", "# x\n")
    (tmp_path / "docs" / "mkdocs" / "site").mkdir()
    _write(tmp_path / ".gitignore", "docs/mkdocs/site/\n")
    monkeypatch.setattr(sv.shutil, "which", lambda name: "/usr/bin/mkdocs" if name == "mkdocs" else None)
    monkeypatch.setattr(sv.subprocess, "run", _fake_run(returncode=1))
    report = sv.validate_mkdocs(tmp_path, sv.Report(quiet=True))
    assert report.errors == 0
    assert report.warnings == 1


def test_validator_shell_wrappers_are_not_shipped() -> None:
    for name in (
        "validate-task.sh",
        "validate-bootstrap-ready.sh",
        "validate-graphify-integration.sh",
        "validate-mkdocs-integration.sh",
    ):
        assert not (REPO_ROOT / "scripts" / name).exists()
