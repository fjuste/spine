"""Seed contract for the Python installer."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_docs_module_seeds_without_overwrite() -> None:
    text = _read("scripts/spine_cli/docs.py")
    assert "def seed_docs" in text
    assert "already exists, not overwriting" in text
    assert "DOCS_SEED_PATHS" in text


def test_install_seed_allowlist_covers_v21_paths() -> None:
    text = _read("scripts/spine_cli/constants.py")
    required = [
        "docs/memory/ledger/learnings.md",
        "docs/governance/memory-tags-policy.md",
        "docs/memory/active_tasks/_task-template.md",
        "docs/memory/completed_tasks/.gitkeep",
        "docs/documentation",
    ]
    for path in required:
        assert path in text, f"missing seed reference: {path}"


def test_installer_does_not_seed_sample_task() -> None:
    text = _read("scripts/spine_cli/docs.py") + _read("scripts/spine_cli/constants.py")
    assert "003-fix-quote-item" not in text


def test_installer_merges_opencode_in_process() -> None:
    text = _read("scripts/spine_cli/opencode_merge.py")
    assert "def merge_project_opencode" in text
    assert "merge-opencode.py" in text


def test_merge_opencode_helper_exists() -> None:
    text = _read("scripts/merge-opencode.py")
    assert "def merge_opencode" in text


def test_spine_install_command_removed() -> None:
    assert not Path("commands/spine-install.md").exists()


def test_shell_install_script_removed() -> None:
    assert not Path("install.sh").exists()
