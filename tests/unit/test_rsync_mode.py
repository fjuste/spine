"""Contract checks for rsync-mode install (symlink alternative with real .spine directory)."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_spine_init_script_exists():
    path = Path("scripts/spine-init.sh")
    assert path.is_file()
    text = _read("scripts/spine-init.sh")
    assert "rsync" in text
    assert "SPINE_CANONICAL_PATH" in text
    assert "--spine-dir=" in text


def test_spine_init_resolves_canonical_path():
    text = _read("scripts/spine-init.sh")
    assert "resolve_canonical_spine" in text
    assert "is_spine_root" in text
    assert "$HOME/Workspace/ide/spine" in text
    assert "SPINE_CANONICAL_PATH" in text
    assert "--spine-dir" in text


def test_spine_init_calls_install_sh():
    text = _read("scripts/spine-init.sh")
    assert "install.sh" in text


def test_install_sh_accepts_real_spine_directory():
    text = _read("install.sh")
    assert "require_spine_path" in text
    # Must contain a branch for real directory (not just symlink)
    assert 'elif [[ -d "$spine_path" ]]' in text


def test_install_sh_health_check_supports_rsync_mode():
    text = _read("install.sh")
    assert "rsync mode" in text


def test_update_sh_supports_rsync_mode():
    text = _read("scripts/update.sh")
    assert "SPINE_MODE" in text
    assert "rsync" in text
    assert "SPINE_CANONICAL_PATH" in text or ".spine-canonical-source" in text


def test_install_sh_uninstall_handles_real_spine_dir():
    text = _read("install.sh")
    assert "rm -rf" in text
    assert "rsync mode" in text
