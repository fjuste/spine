"""Windows install is ``py -3 scripts/spine.py install``, which vendors automatically."""

from pathlib import Path


def test_install_ps1_removed() -> None:
    assert not Path("install.ps1").exists()


def test_readme_documents_windows_python_install() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "Windows" in text
    assert "spine.py vendor" in text
    assert "uses vendor mode automatically" in text
    assert "py -3" in text
    assert "install.ps1" not in text
