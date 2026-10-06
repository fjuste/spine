"""Smoke checks for the Windows PowerShell vendor-mode installer."""

from pathlib import Path

SCRIPT = "install.ps1"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_install_ps1_exists_and_is_vendor_mode() -> None:
    assert Path(SCRIPT).is_file()
    text = _read(SCRIPT)
    assert "vendor-mode installer" in text
    assert ".spine-vendor" in text


def test_install_ps1_is_ascii_for_windows_powershell() -> None:
    Path(SCRIPT).read_bytes().decode("ascii")


def test_install_ps1_requires_project_root() -> None:
    text = _read(SCRIPT)
    assert "[Parameter(Mandatory = $true" in text
    assert "[string]$ProjectRoot" in text


def test_install_ps1_supports_vendor_flags() -> None:
    text = _read(SCRIPT)
    for flag in ("$Update", "$Uninstall", "$Force", "$DryRun", "$Core", "$Skills", "$Targets"):
        assert flag in text


def test_install_ps1_update_requires_spine_dir() -> None:
    text = _read(SCRIPT)
    assert "-Update requires -SpineDir" in text
    assert "points at the project's vendored .spine" in text


def test_install_ps1_excludes_nested_git() -> None:
    text = _read(SCRIPT)
    assert "'.git'" in text
    assert "removed nested .git" in text
    assert "/MIR" in text


def test_install_ps1_keeps_templates_docs_in_vendored_copy() -> None:
    text = _read(SCRIPT)
    assert "Excluded only at the Spine root" in text


def test_install_ps1_preserves_docs_memory_on_seed() -> None:
    text = _read(SCRIPT)
    assert "already exists, not overwriting" in text
    assert "memory/ledger/learnings.md" in text


def test_install_ps1_writes_utf8_without_bom() -> None:
    text = _read(SCRIPT)
    assert "UTF8Encoding($false)" in text


def test_install_ps1_refuses_symlink_mode_without_force() -> None:
    text = _read(SCRIPT)
    assert "Symlink-mode Spine detected" in text
    assert "exit 3" in text


def test_readme_documents_windows_powershell_install() -> None:
    text = _read("README.md")
    assert "Windows (PowerShell)" in text
    assert "install.ps1" in text
