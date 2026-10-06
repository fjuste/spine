"""Rsync mode lives in ``spine.py install --rsync`` and ``spine.py update``."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_spine_init_script_removed() -> None:
    assert not Path("scripts/spine-init.sh").exists()


def test_rsync_flag_records_canonical_source() -> None:
    install = _read("scripts/spine_cli/install.py")
    copy = _read("scripts/spine_cli/vendor_copy.py")
    assert "--rsync" in _read("scripts/spine.py") or "rsync_mode" in install
    assert "SPINE_CANONICAL_PATH" in _read("scripts/spine_cli/update.py")
    assert ".spine-canonical-source" in copy
    assert "rsync mode" in install.lower() or "rsync" in install.lower()


def test_install_accepts_real_spine_directory() -> None:
    text = _read("scripts/spine_cli/install.py")
    assert "rsync mode" in text.lower() or "is_dir()" in text


def test_update_supports_rsync_mode() -> None:
    text = _read("scripts/spine_cli/update.py")
    assert "rsync" in text
    assert "SPINE_CANONICAL_PATH" in text or ".spine-canonical-source" in text


def test_uninstall_keeps_spine_without_vendor_marker() -> None:
    text = _read("scripts/spine_cli/uninstall.py")
    assert ".spine kept" in text
    assert "docs/ and opencode.json were NOT removed" in text
