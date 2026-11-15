"""Contract tests: tasks carry execution notes and evidence for a fresh-session harvest."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = "templates/docs/memory/active_tasks/_task-template.md"
NOTES = "## Execution notes"
EVIDENCE = "## Execution evidence"
NOTE_TYPES = (
    "deviation",
    "incident",
    "rework",
    "decision",
    "out-of-scope",
    "environment",
    "resume",
)
NO_DEVIATIONS = "No deviations from plan"


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return the body of a level-2 section, up to the next level-2 heading."""
    start = text.index(heading) + len(heading)
    end = text.find("\n## ", start)
    return text[start:] if end == -1 else text[start:end]


def test_task_template_places_execution_sections_after_implementation_plan() -> None:
    text = _read(TEMPLATE)
    plan = text.index("## Implementation Plan")
    notes = text.index(NOTES)
    evidence = text.index(EVIDENCE)
    assert plan < notes < evidence


def test_task_template_execution_notes_are_typed_dated_and_append_only() -> None:
    body = _section(_read(TEMPLATE), NOTES)
    lowered = body.lower()
    for note_type in NOTE_TYPES:
        assert f"`{note_type}`" in body, f"missing note type {note_type}"
    assert "YYYY-MM-DD" in body
    assert "append-only" in lowered
    assert "never rewrite" in lowered
    assert NO_DEVIATIONS in body
    assert "stop" in lowered and "human" in lowered
    assert "root cause" in lowered


def test_task_template_execution_evidence_lists_tests_and_manual_runs() -> None:
    body = _section(_read(TEMPLATE), EVIDENCE)
    lowered = body.lower()
    assert "Tests executed" in body
    assert "Test results" in body
    assert "manual" in lowered
    for field in ("who", "when", "commit", "command", "raw output"):
        assert field in lowered, f"evidence missing {field}"
    assert "secret" in lowered and "token" in lowered


def test_spine_execute_writes_notes_as_they_happen() -> None:
    text = _read("commands/spine-execute.md")
    lowered = text.lower()
    assert NOTES in text
    assert EVIDENCE in text
    assert "when it happens" in lowered
    assert "not in a batch" in lowered
    assert "resume point" in lowered


def test_resume_point_has_its_own_note_type() -> None:
    template = _section(_read(TEMPLATE), NOTES)
    resume_line = next(line for line in template.splitlines() if "midway" in line)
    assert "`resume`" in resume_line
    assert "`deviation`" not in resume_line
    execute = _read("commands/spine-execute.md")
    stop_line = next(line for line in execute.splitlines() if "stops midway" in line)
    assert "`resume`" in stop_line
    assert "`deviation`" not in stop_line
    assert "latest `resume` entry" in execute
    harvest = _read("commands/spine-harvest.md")
    resume_row = next(line for line in harvest.splitlines() if line.strip().startswith("| `resume`"))
    assert "no promotion" in resume_row.lower()


def test_spine_execute_scope_restriction_points_to_out_of_scope_note() -> None:
    text = _read("commands/spine-execute.md")
    restriction = next(line for line in text.splitlines() if "**Restriction:**" in line)
    assert NOTES in restriction
    assert "`out-of-scope`" in restriction
    assert '"Notes"' not in text


def test_spine_execute_completion_gate_requires_both_sections() -> None:
    text = _read("commands/spine-execute.md")
    gate = text[text.index("**Completion Gate") :]
    assert NOTES in gate
    assert EVIDENCE in gate
    assert NO_DEVIATIONS in gate
    assert "Tests executed" in gate
    assert "Test results" in gate


def test_spine_harvest_reads_execution_sections_before_memory_bank_update() -> None:
    text = _read("commands/spine-harvest.md")
    read_step = text.index("**Execution record")
    update_step = text.index("**Memory Bank Update:**")
    assert read_step < update_step
    step = text[read_step:update_step]
    assert NOTES in step
    assert EVIDENCE in step
    assert "new session" in step.lower()


def test_spine_harvest_routes_each_note_type_to_a_destination() -> None:
    text = _read("commands/spine-harvest.md")
    step = text[text.index("**Execution record") : text.index("**Memory Bank Update:**")]
    for note_type in NOTE_TYPES:
        assert f"`{note_type}`" in step, f"harvest does not route {note_type}"
    for destination in (
        "ledger/learnings/",
        "ledger/decisions/",
        "domain-glossary.md",
        "system-patterns.md",
        "Known Risks",
        "Known Opportunities",
    ):
        assert destination in step, f"harvest missing destination {destination}"
    assert "all three" in step
    assert "→ LEARN-" in step
    assert "→ no promotion" in step


def test_spine_harvest_cites_evidence_and_handles_legacy_tasks() -> None:
    text = _read("commands/spine-harvest.md")
    lowered = text.lower()
    assert "evidence" in lowered[lowered.index("**description:**") :]
    assert "legacy task" in lowered
    assert "missing" in lowered


def test_executing_plans_skill_records_into_task_sections() -> None:
    text = _read("skills/executing-plans/SKILL.md")
    assert NOTES in text
    assert EVIDENCE in text


def test_memory_bank_rule_documents_execution_sections_and_authors() -> None:
    text = _read("rules/02-memory-bank.md")
    assert NOTES in text
    assert EVIDENCE in text
    access = text[text.index("## Access Rules") :]
    access = access[: access.index("\n## ", 1)]
    assert "Execution notes" in access
    assert "/spine-execute" in access
    assert "/spine-harvest" in access


def test_readme_documents_execution_sections() -> None:
    text = _read("README.md")
    assert NOTES in text
    assert EVIDENCE in text
