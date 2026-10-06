from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_ask_agent_exists_with_opencode_frontmatter() -> None:
    text = _read("agents/ask.md")
    assert "description:" in text
    assert "Read-only thinking partner" in text
    assert "mode: primary" in text
    assert "permission:" in text
    assert "edit: deny" in text
    assert "task: deny" in text
    assert "bash: allow" in text


def test_ask_agent_has_spine_read_only_context() -> None:
    text = _read("agents/ask.md").lower()
    assert "read-only context (spine)" in text
    assert "02-memory-bank.md" in text
    assert "relevant to the question" in text
    assert "tiered sync" in text
    assert "graphify-out/graph.json" in text
    assert "do not" in text and "create or update memory bank" in text


def test_ask_agent_overrides_execution_protocol() -> None:
    text = _read("agents/ask.md").lower()
    assert "override (ask only" in text
    assert "ignore steps 2" in text or "ignore steps 2–6" in text or "ignore steps 2-6" in text
    assert "plan" in text and "branch" in text and "harvest" in text


def test_ask_agent_references_quality_rule_without_duplicating_sync_list() -> None:
    text = _read("agents/ask.md")
    assert "03-code-quality.md" in text
    assert "global/project-brief.md" not in text
    assert "04-code-quality" not in text


def test_ask_agent_has_spine_handoff() -> None:
    text = _read("agents/ask.md").lower()
    assert "spine handoff" in text
    assert "/spine-plan" in text
    assert "/spine-plan-bridge" not in text
    assert "grill me" in text or "grill with docs" in text
    assert "build" in text
    assert "do not" in text and "task" in text


def test_ask_agent_allows_read_only_diagnostics() -> None:
    text = _read("agents/ask.md").lower()
    assert "read-only diagnostics" in text
    assert "pytest --collect-only" in text
    assert "git status" in text
    assert "docker ps" in text
    assert "kubectl get" in text


def test_core_protocol_defers_sync_to_memory_bank() -> None:
    core = _read("rules/01-core-protocol.md").lower()
    memory = _read("rules/02-memory-bank.md").lower()
    assert "follow `02-memory-bank.md`" in core
    assert "**clarify:**" not in core
    assert "key assumptions" in memory
    assert "push back" in memory
    assert "if a simpler alternative exists" in memory


def test_installer_deploys_opencode_agents() -> None:
    text = _read("scripts/spine_cli/wiring.py")
    assert ".opencode" in text and "agents" in text
    assert "warn_global_opencode_agents" in text
    assert "get_mode_files" not in text
    assert ".opencode/modes" not in text
    assert ".config/opencode/agents" in text


def test_readme_documents_project_only_opencode_agents() -> None:
    text = _read("README.md").lower()
    assert "per project only" in text or "project-only" in text
    assert "~/.config/opencode/agents" in text


def test_readme_documents_agents_not_modes() -> None:
    text = _read("README.md")
    assert "agents/" in text
    assert ".opencode/agents/" in text
    assert "modes/ask.md" not in text
    assert "## OpenCode Agents" in text
