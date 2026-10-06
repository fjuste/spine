"""Vendor install is a spine.py subcommand, not a shell script."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_install_vendor_script_removed() -> None:
    assert not Path("scripts/install-vendor.sh").exists()


def test_vendor_refuses_symlink_without_force() -> None:
    text = _read("scripts/spine_cli/install.py")
    assert "Symlink-mode Spine detected" in text
    assert "code=3" in text or "code: int = 3" in text or ", code=3" in text
    assert ".spine-vendor" in text


def test_vendor_update_requires_spine_dir() -> None:
    text = _read("scripts/spine_cli/install.py")
    assert "--update requires --spine-dir=PATH" in text


def test_vendor_copy_drops_nested_git() -> None:
    text = _read("scripts/spine_cli/vendor_copy.py")
    assert "removed nested .git" in text
    assert ".git" in text


def test_vendor_preserves_docs_memory_on_seed() -> None:
    text = _read("scripts/spine_cli/docs.py")
    assert "already exists, not overwriting" in text
    assert "DOCS_SEED_PATHS" in text


def test_readme_documents_vendor_install() -> None:
    text = _read("README.md")
    assert "Optional: Vendor install" in text
    assert "spine.py vendor" in text
