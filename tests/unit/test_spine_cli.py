"""Behavioral tests for the Python Spine installer."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import spine  # noqa: E402
from spine_cli.constants import CORE_SKILLS, DOCS_SEED_PATHS  # noqa: E402

REMOVED_SHELL = (
    "install.sh",
    "install.ps1",
    "scripts/install-vendor.sh",
    "scripts/update.sh",
    "scripts/link-spine.sh",
    "scripts/spine-init.sh",
    "scripts/install-graphify.sh",
    "scripts/install-mkdocs.sh",
    "scripts/validate-task.sh",
    "scripts/validate-bootstrap-ready.sh",
    "scripts/validate-graphify-integration.sh",
    "scripts/validate-mkdocs-integration.sh",
)


def _spine_fixture(path: Path) -> None:
    """Minimal Spine clone with one skill and the files install reads."""
    (path / "rules").mkdir(parents=True)
    (path / "skills" / "writing-plans").mkdir(parents=True)
    (path / "commands").mkdir()
    (path / "agents").mkdir()
    docs = path / "templates" / "docs"
    (docs / "memory" / "global").mkdir(parents=True)
    (docs / "memory" / "ledger").mkdir(parents=True)
    (docs / "memory" / "active_tasks").mkdir(parents=True)
    (docs / "governance").mkdir()
    (docs / "quality").mkdir()
    (docs / "workflow").mkdir()
    (path / "templates" / "opencode.json").write_text(
        '{"$schema": "https://opencode.ai/config.json", "instructions": ["spine"]}\n',
        encoding="utf-8",
    )
    for name in ("01-core-protocol.md", "02-memory-bank.md", "03-code-quality.md"):
        (path / "rules" / name).write_text(f"# {name}\n", encoding="utf-8")
    (path / "skills" / "writing-plans" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (path / "commands" / "spine-plan.md").write_text("# plan\n", encoding="utf-8")
    (path / "agents" / "ask.md").write_text("# ask\n", encoding="utf-8")
    for relative in DOCS_SEED_PATHS:
        dest = docs / relative.removeprefix("docs/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(f"template {relative}\n", encoding="utf-8")
    (path / ".git").mkdir()
    (path / ".git" / "HEAD").write_text("ref: refs/heads/master\n", encoding="utf-8")


def _install(project: Path, spine_dir: Path, *extra: str) -> int:
    return spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(spine_dir),
            "--skills=writing-plans",
            "--targets=cursor,opencode",
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
            *extra,
        ]
    )


def test_windows_install_uses_vendor_without_extra_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source) == 0
    spine_dir = project / ".spine"
    assert spine_dir.is_dir()
    assert not spine_dir.is_symlink()
    assert (project / ".spine-vendor").is_file()
    skill = project / ".agents" / "skills" / "writing-plans"
    assert skill.is_dir()
    assert not skill.is_symlink()
    assert (project / "docs" / "memory" / "global" / "project-brief.md").is_file()
    assert (project / "opencode.json").is_file()


def test_windows_install_rejects_symlink_modes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source, "--copy") == 1
    assert not (project / ".spine-vendor").exists()


def test_install_creates_spine_symlink_and_skill_hub(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source) == 0
    link = project / ".spine"
    assert link.is_symlink()
    assert link.resolve() == source.resolve()
    skill = project / ".agents" / "skills" / "writing-plans"
    assert skill.is_symlink()
    assert skill.readlink() == Path("../../.spine/skills/writing-plans")
    gitignore = (project / ".gitignore").read_text(encoding="utf-8")
    assert ".spine" in gitignore
    assert ".agents/" in gitignore
    assert (project / "opencode.json").is_file()
    assert (project / ".opencode" / "agents" / "ask.md").is_symlink()
    assert not (project / ".agents" / "skills" / "spine-plan").exists()
    assert not (project / ".agents" / "workflows").exists()
    assert not (project / ".claude" / "rules").exists()


def test_install_does_not_overwrite_docs_or_seed_sample_task(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    brief = project / "docs" / "memory" / "global" / "project-brief.md"
    brief.parent.mkdir(parents=True)
    brief.write_text("KEEP\n", encoding="utf-8")
    assert _install(project, source) == 0
    assert brief.read_text(encoding="utf-8") == "KEEP\n"
    assert not (project / "docs" / "memory" / "active_tasks" / "003-fix-quote-item.md").exists()
    assert "003-fix-quote-item" not in (REPO_ROOT / "scripts" / "spine_cli" / "docs.py").read_text(
        encoding="utf-8"
    )


def test_install_copy_keeps_spine_symlink_and_writes_real_files(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source, "--copy") == 0
    assert (project / ".spine").is_symlink()
    skill = project / ".agents" / "skills" / "writing-plans"
    assert skill.is_dir()
    assert not skill.is_symlink()
    assert (skill / "SKILL.md").is_file()


def test_add_remove_and_list_skills(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source) == 0
    capsys.readouterr()
    assert spine.main(["install", "--project-root", str(project), "--spine-dir", str(source), "--list-skills"]) == 0
    listed = capsys.readouterr().out
    assert "writing-plans" in listed
    assert spine.main(
        ["install", "--project-root", str(project), "--remove-skill=writing-plans"]
    ) == 0
    assert not (project / ".agents" / "skills" / "writing-plans").exists()
    assert spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--add-skill=writing-plans",
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
        ]
    ) == 0
    assert (project / ".agents" / "skills" / "writing-plans").is_symlink()


def test_vendor_refuses_symlink_then_force_converts(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    (project / ".spine").symlink_to(source)
    refused = spine.main(
        ["vendor", "--project-root", str(project), "--spine-dir", str(source), "--skills=writing-plans"]
    )
    assert refused == 3
    assert (project / ".spine").is_symlink()
    converted = spine.main(
        [
            "vendor",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--skills=writing-plans",
            "--targets=cursor",
            "--force",
        ]
    )
    assert converted == 0
    assert (project / ".spine-vendor").is_file()
    assert (project / ".spine").is_dir()
    assert not (project / ".spine").is_symlink()
    assert not (project / ".spine" / ".git").exists()


def test_vendor_update_requires_spine_dir(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert spine.main(
        [
            "vendor",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--skills=writing-plans",
            "--targets=cursor",
        ]
    ) == 0
    code = spine.main(["vendor", "--project-root", str(project), "--update"])
    assert code == 1


def test_uninstall_preserves_docs_and_opencode(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    symlink_project = tmp_path / "link"
    vendor_project = tmp_path / "vendor"
    _spine_fixture(source)
    symlink_project.mkdir()
    vendor_project.mkdir()
    assert _install(symlink_project, source) == 0
    assert spine.main(
        [
            "vendor",
            "--project-root",
            str(vendor_project),
            "--spine-dir",
            str(source),
            "--skills=writing-plans",
            "--targets=cursor",
        ]
    ) == 0
    for project, keep_spine in ((symlink_project, True), (vendor_project, False)):
        brief = project / "docs" / "memory" / "global" / "project-brief.md"
        opencode = project / "opencode.json"
        assert brief.is_file()
        assert opencode.is_file()
        assert spine.main(["uninstall", "--project-root", str(project)]) == 0
        assert brief.is_file()
        assert opencode.is_file()
        assert (project / ".spine").exists() is keep_spine
        assert not (project / ".spine-vendor").exists()


def test_rsync_install_writes_canonical_source_without_nested_git(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source, "--rsync") == 0
    spine_dir = project / ".spine"
    assert spine_dir.is_dir()
    assert not spine_dir.is_symlink()
    assert not (spine_dir / ".git").exists()
    assert (spine_dir / ".spine-canonical-source").read_text(encoding="utf-8").strip() == str(source.resolve())
    again = spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--rsync",
            "--skills=writing-plans",
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
        ]
    )
    assert again == 3


def test_update_no_pull_does_not_call_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source) == 0
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> object:
        calls.append(list(args))

        class _Result:
            returncode = 0

        return _Result()

    monkeypatch.setattr("spine_cli.update.subprocess.run", fake_run)
    code = spine.main(
        [
            "update",
            "--project-root",
            str(project),
            "--no-pull",
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
        ]
    )
    assert code == 0
    assert calls == []


def test_update_pulls_via_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert _install(project, source) == 0
    calls: list[list[str]] = []

    def fake_run(args: list[str], **_kwargs: object) -> object:
        calls.append(list(args))

        class _Result:
            returncode = 0

        return _Result()

    monkeypatch.setattr("spine_cli.update.subprocess.run", fake_run)
    code = spine.main(
        [
            "update",
            "--project-root",
            str(project),
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
        ]
    )
    assert code == 0
    assert ["git", "-C", str((project / ".spine").resolve()), "pull"] in calls


def test_update_refuses_vendor_mode(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    project.mkdir()
    assert spine.main(
        [
            "vendor",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--skills=writing-plans",
            "--targets=cursor",
        ]
    ) == 0
    code = spine.main(["update", "--project-root", str(project), "--no-pull"])
    assert code == 1


def test_graphify_flag_invokes_cli_and_validator(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    template = source / "templates" / "dot.graphifyignore"
    template.write_text(".spine\n", encoding="utf-8")
    project.mkdir()
    calls: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        return "/usr/bin/graphify" if name == "graphify" else None

    def fake_run(args: list[str], **_kwargs: object) -> object:
        calls.append(list(args))

        class _Result:
            returncode = 0
            stdout = "graphifyy 0.8.0\n"
            stderr = ""

        return _Result()

    monkeypatch.setattr("spine_cli.graphify_setup.shutil.which", fake_which)
    monkeypatch.setattr("spine_cli.graphify_setup.subprocess.run", fake_run)
    validated: list[str] = []
    import spine_validate

    original = spine_validate.validate_graphify

    def wrapped(root: Path, targets: str, report: object = None) -> object:
        validated.append(targets)
        return original(root, targets, report)

    monkeypatch.setattr(spine_validate, "validate_graphify", wrapped)
    code = spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--skills=writing-plans",
            "--targets=cursor",
            "--with-graphify",
            "--no-mkdocs-prompt",
        ]
    )
    assert code == 0
    assert ["graphify", "update", "."] in calls
    assert ["graphify", "cursor", "install"] in calls
    assert validated
    assert (project / ".graphifyignore").is_file()


def test_core_skills_match_constant() -> None:
    assert CORE_SKILLS == (
        "writing-plans",
        "executing-plans",
        "test-driven-development",
        "systematic-debugging",
        "verification-before-completion",
    )
    assert "docs/memory/ledger/learnings.md" in DOCS_SEED_PATHS


def test_operational_shell_scripts_are_gone() -> None:
    for relative in REMOVED_SHELL:
        assert not (REPO_ROOT / relative).exists(), relative


def test_global_flag_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    code = spine.main(["install", "--project-root", str(project), "--global"])
    assert code == 1


def _install_default(project: Path, source: Path, *extra: str) -> int:
    return spine.main(
        [
            "install",
            "--project-root",
            str(project),
            "--spine-dir",
            str(source),
            "--no-graphify-prompt",
            "--no-mkdocs-prompt",
            *extra,
        ]
    )


def test_default_install_wires_slash_commands_on_four_tools(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    (source / "commands" / "spine-plan.md").write_text(
        "---\ndescription: Plan a task\nagent: build\n---\n# plan\n",
        encoding="utf-8",
    )
    project.mkdir()
    assert _install_default(project, source, "--skills=writing-plans") == 0

    skill = project / ".agents" / "skills" / "spine-plan" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "name: spine-plan" in text
    assert 'description: "Plan a task"' in text
    assert "disable-model-invocation: true" in text
    procedure = project / ".agents" / "skills" / "spine-plan" / "procedure.md"
    assert procedure.is_symlink()
    assert procedure.resolve() == (source / "commands" / "spine-plan.md").resolve()
    assert (project / ".cursor" / "commands" / "spine-plan.md").is_symlink()
    assert (project / ".opencode" / "commands" / "spine-plan.md").is_symlink()
    claude_skill = project / ".claude" / "skills" / "spine-plan" / "SKILL.md"
    assert claude_skill.is_file()
    assert claude_skill.read_text(encoding="utf-8") == text
    rule = project / ".claude" / "rules" / "02-memory-bank.md"
    assert rule.is_symlink()
    assert rule.resolve() == (source / "rules" / "02-memory-bank.md").resolve()
    assert "02-memory-bank.md" in rule.read_text(encoding="utf-8")
    assert not (project / ".agents" / "workflows" / "spine-plan.md").exists()


def test_copy_install_materializes_workflow_procedure(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    command = "---\ndescription: Plan a task\n---\n# plan\n"
    (source / "commands" / "spine-plan.md").write_text(command, encoding="utf-8")
    project.mkdir()
    assert _install_default(project, source, "--copy", "--skills=writing-plans") == 0
    procedure = project / ".agents" / "skills" / "spine-plan" / "procedure.md"
    assert procedure.is_file()
    assert not procedure.is_symlink()
    assert procedure.read_text(encoding="utf-8") == command
    claude_skill = project / ".claude" / "skills" / "spine-plan" / "SKILL.md"
    assert claude_skill.is_file()
    assert not (project / ".claude" / "skills").is_symlink()
    copied_rule = project / ".claude" / "rules" / "02-memory-bank.md"
    assert copied_rule.is_file()
    assert not copied_rule.is_symlink()
    assert copied_rule.read_text(encoding="utf-8") == (
        source / "rules" / "02-memory-bank.md"
    ).read_text(encoding="utf-8")


def test_update_keeps_workflow_skill_and_removes_legacy_workflow(tmp_path: Path) -> None:
    source = tmp_path / "spine"
    project = tmp_path / "proj"
    _spine_fixture(source)
    extra = source / "skills" / "extra-skill"
    extra.mkdir()
    (extra / "SKILL.md").write_text("# extra\n", encoding="utf-8")
    project.mkdir()
    assert _install_default(project, source) == 0
    assert (project / ".agents" / "skills" / "extra-skill").is_symlink()
    assert (project / ".agents" / "skills" / "spine-plan" / "SKILL.md").is_file()

    legacy = project / ".agents" / "workflows" / "spine-plan.md"
    legacy.parent.mkdir()
    legacy.symlink_to("../../../.spine/commands/spine-plan.md")

    assert _install_default(project, source, "--update", "--skills=writing-plans") == 0
    assert (project / ".agents" / "skills" / "spine-plan" / "SKILL.md").is_file()
    assert (project / ".agents" / "skills" / "writing-plans").exists()
    assert not (project / ".agents" / "skills" / "extra-skill").exists()
    assert not legacy.exists()

