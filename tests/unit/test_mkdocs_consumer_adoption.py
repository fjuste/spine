from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_mkdocs_is_optional_and_documented_in_system_patterns() -> None:
    text = _read("templates/docs/memory/global/system-patterns.md").lower()
    assert "mkdocs" in text
    assert "optional" in text or "not a dependency" in text
    assert "python3 .spine/scripts/spine_validate.py mkdocs" in text
    assert "documentation-driven-development" in text


def test_install_sh_has_mkdocs_onboarding() -> None:
    text = _read("install.sh").lower()
    assert "mkdocs" in text
    assert "prompt_mkdocs_opt_in" in text
    assert "mkdocs_integration_complete" in text
    assert "install-mkdocs.sh" in text
    assert "mkdocs-uninstall" in text
    assert "setup_project_mkdocs" in text


def test_install_mkdocs_sh_seeds_templates_and_builds() -> None:
    text = _read("scripts/install-mkdocs.sh").lower()
    assert "mkdocs" in text
    assert "--init-mkdocs" in text
    assert "--uninstall" in text
    assert "validate-mkdocs-integration.sh" in text
    assert "mkdocs build" in text
    assert "templates/docs/mkdocs" in text
    assert "mkdocs.yml" in text


def test_spine_harvest_has_mkdocs_steps() -> None:
    text = _read("commands/spine-harvest.md").lower()
    assert "mkdocs refresh" in text
    assert "docs/mkdocs/mkdocs.yml" in text
    assert "mkdocs build" in text
    assert "--strict" in text
    assert "do not block harvest" in text
    assert "mkdocs documentation" in text


def test_mkdocs_templates_exist() -> None:
    assert Path("templates/docs/mkdocs/mkdocs.yml").exists()
    assert Path("templates/docs/mkdocs/index.md").exists()
    assert Path("templates/docs/mkdocs/architecture.md").exists()

    yml_text = _read("templates/docs/mkdocs/mkdocs.yml")
    assert "site_name" in yml_text
    assert "PROJECT_NAME_PLACEHOLDER" in yml_text
    assert "readthedocs" in yml_text

    index_text = _read("templates/docs/mkdocs/index.md")
    assert "PROJECT_NAME_PLACEHOLDER" in index_text


def test_readme_documents_mkdocs() -> None:
    text = _read("README.md").lower()
    assert "## optional: mkdocs" in text
    assert "pip install mkdocs" in text or "mkdocs" in text
    assert "interactive" in text or "answer" in text and "yes" in text
    assert "validate-mkdocs-integration.sh" in text
    assert "--with-mkdocs" in text
    assert "--mkdocs-uninstall" in text


def test_agents_md_documents_mkdocs() -> None:
    text = _read("AGENTS.md").lower()
    assert "mkdocs" in text
    assert "validate-mkdocs-integration.sh" in text
    assert "docs/mkdocs" in text
    assert "documentation-driven-development" in text
    assert "mkdocs-uninstall" in text


def test_validate_mkdocs_integration_script_exists() -> None:
    assert Path("scripts/validate-mkdocs-integration.sh").exists()
    text = _read("scripts/spine_validate.py")
    assert "docs/mkdocs/mkdocs.yml" in text
    assert "mkdocs build" in text
    assert "--strict" in text
    assert "uv run --extra docs mkdocs" in text


def test_install_mkdocs_script_exists() -> None:
    path = Path("scripts/install-mkdocs.sh")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "--init-mkdocs" in text
    assert "--project-root=" in text
    assert "templates/docs/mkdocs" in text
    assert "mkdocs build" in text


def test_mkdocs_skill_exists() -> None:
    path = Path("skills/documentation-driven-development/SKILL.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "documentation is part of the definition of done" in text.lower()
    assert "docs/mkdocs" in text
    assert "mkdocs build" in text
    assert "when mkdocs is active" in text.lower() or "docs/mkdocs/mkdocs.yml" in text.lower()


def test_install_sh_prompts_mkdocs_interactively() -> None:
    text = _read("install.sh").lower()
    assert "prompt_mkdocs_opt_in" in text
    assert "enable mkdocs for this project?" in text
    assert "mkdocs: skipped" in text or "re-run and press enter" in text
    assert "--no-mkdocs-prompt" in text


def test_update_sh_has_mkdocs_passthrough() -> None:
    text = _read("scripts/update.sh").lower()
    assert "--with-mkdocs" in text
    assert "with_mkdocs" in text


def test_bootstrap_ready_warns_mkdocs_incomplete() -> None:
    text = _read("scripts/spine_validate.py").lower()
    assert "mkdocs" in text
    assert "docs/mkdocs/mkdocs.yml" in text
    assert "{validate_cmd} mkdocs" in text
    assert "answer yes at the mkdocs prompt" in text
    assert "--with-mkdocs" in text


def test_core_protocol_harvest_includes_mkdocs_deliverable() -> None:
    text = _read("commands/spine-harvest.md").lower()
    assert "mkdocs" in text


def test_spine_update_documents_mkdocs_adoption() -> None:
    text = _read("commands/spine-update.md").lower()
    assert "mkdocs" in text.lower()
    assert "--with-mkdocs" in text
    assert "python3 .spine/scripts/spine_validate.py mkdocs" in text


def test_system_patterns_links_to_readme_mkdocs_section() -> None:
    text = _read("templates/docs/memory/global/system-patterns.md")
    assert "github.com/fjuste/spine#optional-mkdocs" in text.lower()


def test_mkdocs_gitignore_template_exists() -> None:
    path = Path("templates/docs/mkdocs/.gitignore")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "site/" in text
