from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_graphify_policy_is_optional_and_consumer_scoped() -> None:
    text = _read("templates/docs/memory/global/system-patterns.md").lower()
    assert "graphify" in text
    assert "optional" in text or "not a dependency" in text
    assert "discovery protocol" in text or "graphify query" in text


def test_install_sh_has_optional_graphify_onboarding() -> None:
    text = _read("install.sh").lower()
    assert "graphify" in text
    assert "prompt_graphify_opt_in" in text
    assert "graphify_integration_complete" in text
    assert "install-graphify.sh" in text
    assert "graphify-uninstall" in text
    assert "tri-platform" in text or "cursor, opencode, claude" in text
    assert "$update_mode && return 1" not in text


def test_install_graphify_sh_tri_platform_co_install() -> None:
    text = _read("scripts/install-graphify.sh").lower()
    assert "graphify cursor install" in text
    assert "graphify opencode install" in text
    assert "graphify claude install" in text
    assert "merge-graphify-opencode.py" in text
    assert "validate-graphify-integration.sh" in text
    assert "--targets=" in text


def test_spine_bootstrap_detects_graphify_artifacts() -> None:
    text = _read("commands/spine-bootstrap.md").lower()
    assert "graphify-out/" in text
    assert "validate-graphify-integration.sh" in text
    assert "graph_report.md" in text
    assert "mandatory summary" in text and "graphify" in text


def test_spine_plan_has_graphify_discovery_protocol() -> None:
    text = _read("commands/spine-plan.md").lower()
    assert "graphify-out/graph.json" in text
    assert "graphify discovery protocol" in text
    assert "fallback" in text


def test_core_rules_keep_memory_bank_mandatory_and_graph_conditional() -> None:
    core = _read("rules/01-core-protocol.md").lower()
    memory = _read("rules/02-memory-bank.md").lower()
    assert "follow `02-memory-bank.md`" in core
    assert "graphify" in core
    assert "/graphify" in core
    assert "docs/memory/" in memory
    assert "graphify-out/graph.json" in memory
    assert "memory bank remains mandatory" in memory
    assert "graphify discovery protocol" in memory
    assert "graph_report.md" in memory
    assert "graphify query" in memory


def test_graphifyignore_template_exists() -> None:
    p = Path("templates/dot.graphifyignore")
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    assert ".spine" in text
    assert ".agents/" in text
    assert ".cursor/" in text
    assert ".opencode/" in text


def test_readme_documents_graphify_interactive_first() -> None:
    text = _read("README.md").lower()
    assert "## optional: graphify" in text
    assert "graphifyy" in text
    assert "interactive" in text or "answer" in text and "yes" in text
    assert "validate-graphify-integration.sh" in text
    assert "graph_report.md" in text
    assert "cursor" in text and "opencode" in text and "claude" in text
    assert "--with-graphify" in text


def test_system_patterns_links_to_readme_graphify_section() -> None:
    text = _read("templates/docs/memory/global/system-patterns.md")
    assert "github.com/fjuste/spine#optional-graphify" in text.lower()


def test_spine_update_documents_existing_project_graphify_adoption() -> None:
    text = _read("commands/spine-update.md").lower()
    assert "adopt graphify on an existing project" in text
    assert "--graphify-init" in text
    assert "validate-graphify-integration.sh" in text


def test_install_sh_prompts_graphify_interactively() -> None:
    text = _read("install.sh").lower()
    assert "prompt_graphify_opt_in" in text
    assert "enable graphify for this project?" in text
    assert "complete graphify integration" in text
    assert "--no-graphify-prompt" in text
    assert "medium/large" in text


def test_spine_harvest_refreshes_graphify_when_in_use() -> None:
    text = _read("commands/spine-harvest.md").lower()
    assert "graphify refresh" in text
    assert "graphify-out/graph.json" in text
    assert "graphify update ." in text
    assert "do not block harvest" in text
    assert "graphify query" in text


def test_validate_graphify_integration_script_exists() -> None:
    path = Path("scripts/validate-graphify-integration.sh")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "graphify.mdc" in text
    assert "graphify.js" in text
    assert "claude" in text.lower()
    assert "--targets=" in text


def test_merge_graphify_opencode_script_exists() -> None:
    path = Path("scripts/merge-graphify-opencode.py")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "merge_graphify_into_opencode" in text
    assert "strip_graphify_from_opencode" in text


def test_agents_md_documents_tri_platform_graphify() -> None:
    text = _read("AGENTS.md").lower()
    assert "validate-graphify-integration.sh" in text
    assert "graphify discovery protocol" in text
    assert "graphify-uninstall" in text
    assert "answer" in text and "yes" in text


def test_validate_scripts_use_interactive_first_recovery() -> None:
    integration = _read("scripts/validate-graphify-integration.sh").lower()
    bootstrap = _read("scripts/validate-bootstrap-ready.sh").lower()
    assert "answer yes" in integration or "answering yes" in integration
    assert "answer yes" in bootstrap
    assert "--with-graphify" in integration
