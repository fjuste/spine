"""Install the real Spine tree into a scratch project and read the wired procedures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import spine  # noqa: E402

SECTIONS = ("## Execution notes", "## Execution evidence")
PROCEDURES = ("spine-execute", "spine-harvest")


def _install(project: Path, *extra: str) -> int:
    return spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(REPO_ROOT),
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
            "--core",
            *extra,
        ]
    )


@pytest.mark.parametrize("mode", [(), ("--copy",)], ids=["symlink", "copy"])
def test_installed_execute_and_harvest_show_execution_sections(
    tmp_path: Path, mode: tuple[str, ...]
) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _install(project, *mode) == 0

    for name in PROCEDURES:
        installed = (
            project / ".agents" / "skills" / name / "procedure.md",
            project / ".claude" / "skills" / name / "procedure.md",
            project / ".cursor" / "commands" / f"{name}.md",
            project / ".opencode" / "commands" / f"{name}.md",
        )
        for path in installed:
            text = path.read_text(encoding="utf-8")
            for section in SECTIONS:
                assert section in text, f"{path} missing {section}"

    template = project / "docs" / "memory" / "active_tasks" / "_task-template.md"
    seeded = template.read_text(encoding="utf-8")
    for section in SECTIONS:
        assert section in seeded
