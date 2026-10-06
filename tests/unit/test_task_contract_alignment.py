"""Cross-file invariants for Memory Bank task contract alignment."""

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_task_template_has_implementation_plan_section() -> None:
    text = _read("templates/docs/memory/active_tasks/_task-template.md")
    assert "## Implementation Plan" in text
    assert "do not use inline" in text.lower() or "metadata lives in frontmatter" in text.lower()


def test_no_sample_numbered_task_in_templates() -> None:
    active = Path("templates/docs/memory/active_tasks")
    numbered = [
        p.name
        for p in active.glob("*.md")
        if p.name != "_task-template.md" and p.name[:3].isdigit()
    ]
    assert numbered == [], f"unexpected sample tasks: {numbered}"


def test_writing_plans_aligns_with_template() -> None:
    text = _read("skills/writing-plans/SKILL.md").lower()
    assert "_task-template" in text
    assert "implementation plan" in text
    assert "superpowers:executing-plans" not in text
    assert "docs/memory/active_tasks/" in text


def test_executing_plans_reads_frontmatter_and_impl_plan() -> None:
    text = _read("skills/executing-plans/SKILL.md").lower()
    assert "frontmatter" in text
    assert "implementation plan" in text
    assert "docs/memory/active_tasks/" in text
    super_lines = [
        line for line in text.splitlines() if "superpowers:" in line
    ]
    assert super_lines, "expected explicit rejection of superpowers handoff"
    assert all("do not" in line for line in super_lines)


def test_spine_plan_lists_implementation_plan() -> None:
    text = _read("commands/spine-plan.md")
    assert "## Implementation Plan" in text
    assert "Plan contract checklist" in text
    assert "spine_validate.py" in text
    assert "Contract validation" in text
    assert "python3 .spine/scripts/spine_validate.py task" in text
    assert "py -3" in text
    assert "bridge mode" in text.lower()
    assert "gitignored" in text.lower()


def test_spine_execute_reads_implementation_plan() -> None:
    text = _read("commands/spine-execute.md")
    assert "## Implementation Plan" in text


def test_spine_harvest_and_execute_share_frontmatter_fields() -> None:
    execute = _read("commands/spine-execute.md").lower()
    harvest = _read("commands/spine-harvest.md").lower()
    for field in ("frontmatter", "branch", "base", "tags"):
        assert field in execute, f"spine-execute missing {field}"
        assert field in harvest, f"spine-harvest missing {field}"


def test_memory_bank_rule_documents_implementation_plan() -> None:
    text = _read("rules/02-memory-bank.md")
    assert "## Implementation Plan" in text
    assert "Anti-patterns" in text


def test_bootstrap_precondition_is_install_sh() -> None:
    text = _read("commands/spine-bootstrap.md")
    assert "bash .spine/install.sh" in text
    assert "/spine-install" not in text


def test_validate_task_script_exists() -> None:
    assert Path("scripts/validate-task.sh").exists()
    text = _read("scripts/spine_validate.py")
    assert "Implementation Plan" in text
    assert "superpowers:" in text
    assert "python3 .spine/scripts/spine_validate.py task" in text


def test_validate_bootstrap_ready_checks_validator_script() -> None:
    text = _read("scripts/spine_validate.py")
    assert '"scripts" / "spine_validate.py"' in text
