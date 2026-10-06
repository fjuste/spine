from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_validate_bootstrap_ready_is_python() -> None:
    assert not Path("scripts/validate-bootstrap-ready.sh").exists()
    seeds = _read("scripts/spine_cli/constants.py")
    text = _read("scripts/spine_validate.py")
    assert "project-brief.md" in seeds
    assert "roadmap.md" in seeds
    assert "spine-bootstrap.md" in text
    assert "opencode.json" in text
    assert "spine_validate.py" in text


def test_global_templates_have_knowledge_sections() -> None:
    patterns = _read("templates/docs/memory/global/system-patterns.md")
    tech = _read("templates/docs/memory/global/tech-context.md")
    product = _read("templates/docs/memory/global/product-context.md")
    assert "## Project-Specific Alterations" in patterns
    assert "## Known Risks" in tech
    assert "## Known Opportunities (unplanned)" in product


def test_roadmap_template_english_placeholders() -> None:
    text = _read("templates/docs/memory/ledger/roadmap.md")
    assert "[Goal Name]" in text
    assert "[Nome]" not in text
    assert "ice_method" in text
    assert "last_updated" in text
    assert "last_reviewed" in text
    assert "review_cadence" in text
    assert "goals_active" in text
    assert "ideas_total" in text


def test_memory_bank_documents_bootstrap_knowledge_mapping() -> None:
    text = _read("rules/02-memory-bank.md")
    assert "Project-Specific Alterations" in text
    assert "Known Risks" in text
    assert "Known Opportunities" in text
    assert "Bootstrap fills" in text or "bootstrap fills" in text.lower()
    assert "does **not** create `active_tasks/`" in text


def test_spine_bootstrap_deep_assessment_and_agent_focus() -> None:
    text = _read("commands/spine-bootstrap.md")
    lower = text.lower()
    assert "python3 .spine/scripts/spine_validate.py bootstrap" in text
    assert "graphify-out/graph.json" in lower
    assert "agent-ready" in lower or "agent-optimized" in lower
    assert "maximize detail" in lower or "maximal detail" in lower


def test_spine_bootstrap_hunts_alterations_risks_opportunities() -> None:
    text = _read("commands/spine-bootstrap.md")
    assert "Project-Specific Alterations" in text
    assert "Known Risks" in text
    assert "Known Opportunities" in text
    assert "Alterations" in text


def test_spine_bootstrap_no_roadmap_task_or_plan() -> None:
    text = _read("commands/spine-bootstrap.md")
    lower = text.lower()
    assert "do not modify" in lower and "roadmap.md" in lower
    assert "initial task" not in lower
    assert "when there is delivery scope" not in lower
    assert "validate-task.sh" not in text
    assert "active_tasks/NNN" in text or "NNN-*.md" in text
    assert "/spine-plan" in text


def test_spine_bootstrap_no_seed_side_effects() -> None:
    text = _read("commands/spine-bootstrap.md")
    lower = text.lower()
    assert "forbidden" in lower
    assert "cp -r" in lower  # listed as forbidden action
    assert "/spine-install" not in lower


def test_spine_bootstrap_no_grill_me() -> None:
    text = _read("commands/spine-bootstrap.md").lower()
    assert "no `@grill-me`" in text or "no @grill-me" in text


def test_readme_documents_bootstrap_scope() -> None:
    text = _read("README.md")
    assert "spine_validate.py bootstrap" in text
    assert "validate-bootstrap-ready.sh" not in text
    assert "does **not** fill `roadmap.md`" in text or "not fill `roadmap.md`" in text


def test_agents_md_bootstrap_vs_plan() -> None:
    text = _read("AGENTS.md")
    assert "spine_validate.py bootstrap" in text
    assert "validate-bootstrap-ready.sh" not in text
    assert "roadmap.md" in text
    assert "/spine-plan" in text
