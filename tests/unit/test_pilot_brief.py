"""Tests for the pilot brief (``spine.py brief``, spine_cli.brief)."""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import spine  # noqa: E402
from spine_cli import brief, memory  # noqa: E402

TODAY = date(2026, 11, 16)
SECTIONS = ("WHERE WE ARE", "RECENT STORY", "WAITING ON YOU", "NEXT STEP")
DELIVERIES_DIR = "docs/memory/ledger/deliveries"

ROADMAP = """# Roadmap

## Goals

### G1: Lean context

Text.

### G2: Deterministic automation

Text.

## Idea Bank

| ID  | Idea | Goal | ICE | Confidence | Status |
|-----|------|------|-----|------------|--------|
| I3 | Digest with `a \\| b` escaped pipe | G1 | 300 | 7 | In Progress |
| I4 | Hook runtime | G2 | 210 | 6 | Candidate |
| I5 | Orphan idea | G9 | 100 | 5 | Candidate |
"""

PROGRESS_PLAIN = """# Progress

## Current state
- In flight: none.
- Blocked: nothing.
- Next: harvest 011, then plan I4.
"""

PROGRESS_WITH_NEXT = """---
next_step: Harvest task 011 so its delivery is recorded
next_command: /spine-harvest @docs/memory/active_tasks/011-review-task.md
next_alternatives:
  - /spine-plan for I4
  - /spine-roadmap --review
---
# Progress

## Current state
- In flight: none.
- Blocked: nothing.
- Next: harvest 011, then plan I4.
"""


def _write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _task(root: Path, folder: str, name: str, frontmatter: str) -> None:
    _write(root, f"docs/memory/{folder}/{name}", f"---\n{frontmatter}\n---\n# {name}\n")


def _delivery(root: Path, day: int, task: str = "", why: str = "") -> str:
    entry_date = f"2026-11-{day:02d}"
    lines = [
        f"id: {entry_date}-delivery-{day}",
        f"date: {entry_date}",
        f"title: Delivery number {day}",
        f"summary: Summary {day}",
        f"task: {task}",
    ]
    if why:
        lines.append(f"why: {why}")
    name = f"{entry_date}-delivery-{day}.md"
    _write(root, f"{DELIVERIES_DIR}/{name}", "---\n" + "\n".join(lines) + "\n---\n\nBody.\n")
    return name


def _bank(root: Path) -> Path:
    """Fixture bank: 7 deliveries, one IN_PROGRESS, one REVIEW and one statusless task."""
    _write(root, "docs/memory/ledger/progress.md", PROGRESS_PLAIN)
    for day in range(1, 8):
        _delivery(root, day)
    _task(root, "active_tasks", "010-in-progress.md", "task_id: 010\ntitle: Work in flight\nstatus: IN_PROGRESS")
    _task(
        root,
        "active_tasks",
        "011-review-task.md",
        f"task_id: 011\ntitle: Ready for review\nstatus: REVIEW\nupdated_at: {TODAY.isoformat()}",
    )
    _task(root, "active_tasks", "012-no-status.md", "task_id: 012\ntitle: Legacy task")
    return root


def _render(root: Path, git: brief.GitState | None = None, is_tty: bool = False) -> str:
    return brief.build_brief(root, TODAY, git, is_tty)


def _section_lines(output: str, heading: str) -> list[str]:
    lines = output.split("\n")
    start = lines.index(heading) + 1
    body: list[str] = []
    for line in lines[start:]:
        if line in SECTIONS or not line.strip():
            break
        body.append(line)
    return body


# =============================================================================
# Task 1: sections, arc, why (AC1, AC2, AC3)
# =============================================================================


def test_brief_prints_header_and_sections_in_order(tmp_path: Path) -> None:
    output = _render(_bank(tmp_path), brief.GitState(branch="develop", changes=0))

    header = output.split("\n")[0]
    assert tmp_path.name in header
    assert "develop" in header
    assert "clean tree" in header
    assert TODAY.isoformat() in header
    positions = [output.split("\n").index(heading) for heading in SECTIONS]
    assert positions == sorted(positions)


def test_brief_header_counts_uncommitted_changes(tmp_path: Path) -> None:
    output = _render(_bank(tmp_path), brief.GitState(branch="main", changes=3))

    assert "3 uncommitted changes" in output.split("\n")[0]


def test_brief_header_says_no_git_without_git(tmp_path: Path) -> None:
    output = _render(_bank(tmp_path), None)

    assert "no git" in output.split("\n")[0]


def test_brief_story_lists_newest_five_deliveries(tmp_path: Path) -> None:
    output = _render(_bank(tmp_path))

    story = _section_lines(output, "RECENT STORY")
    assert len(story) == 5
    for line, day in zip(story, (7, 6, 5, 4, 3)):
        assert f"11-{day:02d}  Delivery number {day}" in line


def test_brief_where_we_are_lists_in_progress_tasks(tmp_path: Path) -> None:
    where = _section_lines(_render(_bank(tmp_path)), "WHERE WE ARE")

    assert any("010" in line and "Work in flight" in line for line in where)
    assert not any("011" in line for line in where)


def test_brief_waiting_lists_review_task_and_open_task_warnings(tmp_path: Path) -> None:
    waiting = _section_lines(_render(_bank(tmp_path)), "WAITING ON YOU")

    review = [line for line in waiting if "011" in line and "Ready for review" in line]
    assert len(review) == 1
    assert "/spine-harvest" in review[0]
    assert any("without a valid `status:`" in line and "012-no-status.md" in line for line in waiting)


def test_brief_empty_section_prints_nothing(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_PLAIN)

    output = _render(tmp_path)

    assert _section_lines(output, "WHERE WE ARE") == ["  nothing"]
    assert _section_lines(output, "RECENT STORY") == ["  nothing"]
    assert _section_lines(output, "WAITING ON YOU") == ["  nothing"]


def test_brief_command_exits_1_without_memory_bank(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = spine.main(["brief", f"--project-root={tmp_path}"])

    assert code == 1
    assert "spine.py install" in capsys.readouterr().err


def test_brief_command_reads_git_state(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "trunk", str(tmp_path)], check=True)

    code = spine.main(["brief", f"--project-root={tmp_path}"])

    header = capsys.readouterr().out.split("\n")[0]
    assert code == 0
    assert "trunk" in header
    assert "1 uncommitted change" in header


def test_brief_command_says_no_git_outside_a_repository(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path)

    code = spine.main(["brief", f"--project-root={tmp_path}"])

    assert code == 0
    assert "no git" in capsys.readouterr().out.split("\n")[0]


def _arc_lines(root: Path) -> list[str]:
    return [line for line in _section_lines(_render(root), "WHERE WE ARE") if "Arc:" in line]


def test_arc_comes_from_newest_in_progress_task(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/roadmap.md", ROADMAP)
    _task(tmp_path, "active_tasks", "003-old.md", "task_id: 003\ntitle: Old\nstatus: IN_PROGRESS\nroadmap_idea: I4")
    _task(tmp_path, "active_tasks", "004-new.md", "task_id: 004\ntitle: New\nstatus: IN_PROGRESS\nroadmap_idea: I3")

    arc = _arc_lines(tmp_path)

    assert len(arc) == 1
    assert "Arc: G1 — Lean context" in arc[0]


def test_arc_falls_back_to_newest_delivered_task(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/roadmap.md", ROADMAP)
    _task(tmp_path, "completed_tasks", "001-older.md", "task_id: 001\ntitle: Older\nstatus: DONE\nroadmap_idea: I3")
    _task(tmp_path, "completed_tasks", "002-newer.md", "task_id: 002\ntitle: Newer\nstatus: DONE\nroadmap_idea: I4")
    _delivery(tmp_path, 1, task="001-older")
    _delivery(tmp_path, 2, task="002-newer")

    assert "Arc: G2 — Deterministic automation" in _arc_lines(tmp_path)[0]


@pytest.mark.parametrize(
    ("roadmap", "idea"),
    [
        (None, "I3"),  # no roadmap
        (ROADMAP, None),  # no roadmap_idea
        (ROADMAP, "I99"),  # unknown idea ID
        (ROADMAP, "I5"),  # idea points to an unknown goal
    ],
)
def test_arc_is_omitted_when_a_link_is_missing(tmp_path: Path, roadmap: str | None, idea: str | None) -> None:
    if roadmap is not None:
        _write(tmp_path, "docs/memory/ledger/roadmap.md", roadmap)
    idea_line = f"\nroadmap_idea: {idea}" if idea else ""
    _task(tmp_path, "active_tasks", "004-new.md", f"task_id: 004\ntitle: New\nstatus: IN_PROGRESS{idea_line}")

    assert _arc_lines(tmp_path) == []


def test_story_prints_why_under_its_delivery(tmp_path: Path) -> None:
    _delivery(tmp_path, 1)
    _delivery(tmp_path, 2, why="Pilots asked where the project stands at every session")
    _delivery(tmp_path, 3, why="x" * 200)

    story = _section_lines(_render(tmp_path), "RECENT STORY")

    assert "Delivery number 3" in story[0]
    capped = story[1].strip()
    assert capped.startswith("why: ")
    assert capped.endswith("…")
    assert len(capped) == len("why: ") + brief.WHY_MAX_CHARS
    assert "Delivery number 2" in story[2]
    assert story[3].strip() == "why: Pilots asked where the project stands at every session"
    assert "Delivery number 1" in story[4]
    assert len(story) == 5


def test_ledger_entry_reads_why(tmp_path: Path) -> None:
    name = _delivery(tmp_path, 1, why="Because")

    entry = memory.read_entry(tmp_path / DELIVERIES_DIR / name)

    assert entry.why == "Because"


def test_delivery_template_documents_why() -> None:
    template = (REPO_ROOT / "templates/docs/memory/ledger/deliveries/_template.md").read_text(encoding="utf-8")

    assert "why" in memory.read_frontmatter(template)
    assert "120" in template


# =============================================================================
# Task 2: links (AC4)
# =============================================================================


def _linked_bank(root: Path) -> Path:
    _bank(root)
    _write(root, "docs/memory/ledger/roadmap.md", ROADMAP)
    _task(root, "active_tasks", "013-arc.md", "task_id: 013\ntitle: Arc task\nstatus: IN_PROGRESS\nroadmap_idea: I3")
    return root


def test_terminal_output_uses_osc8_links_to_absolute_paths(tmp_path: Path) -> None:
    root = _linked_bank(tmp_path)

    output = _render(root, is_tty=True)

    delivery = (root / DELIVERIES_DIR / "2026-11-07-delivery-7.md").resolve().as_uri()
    task = (root / "docs/memory/active_tasks/013-arc.md").resolve().as_uri()
    roadmap = (root / "docs/memory/ledger/roadmap.md").resolve().as_uri()
    for uri in (delivery, task, roadmap):
        assert f"\x1b]8;;{uri}\x1b\\" in output
    assert "→ docs/memory" not in output


def test_non_terminal_output_has_relative_paths_and_no_escapes(tmp_path: Path) -> None:
    root = _linked_bank(tmp_path)

    output = _render(root, is_tty=False)

    assert "\x1b" not in output
    assert "→ docs/memory/ledger/deliveries/2026-11-07-delivery-7.md" in output
    assert "→ docs/memory/active_tasks/013-arc.md" in output
    assert "→ docs/memory/active_tasks/011-review-task.md" in output
    assert "→ docs/memory/ledger/roadmap.md" in output
    assert str(root) not in output


def test_brief_command_through_a_pipe_has_no_escapes(tmp_path: Path) -> None:
    _linked_bank(tmp_path)

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "spine.py"), "brief", f"--project-root={tmp_path}"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "\x1b" not in result.stdout
    assert "→ docs/memory/" in result.stdout


# =============================================================================
# Task 3: structured next step (AC5)
# =============================================================================

NEXT_FIELDS = ("next_step", "next_command", "next_alternatives")


def test_next_step_prints_recorded_fields(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_WITH_NEXT)

    next_step = _section_lines(_render(tmp_path), "NEXT STEP")

    assert next_step == [
        "  Harvest task 011 so its delivery is recorded",
        "  → type:  /spine-harvest @docs/memory/active_tasks/011-review-task.md",
        "  Alternatives: /spine-plan for I4 · /spine-roadmap --review",
    ]


def test_next_step_without_fields_prints_next_bullet_and_hint(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_PLAIN)

    next_step = _section_lines(_render(tmp_path), "NEXT STEP")

    assert next_step[0] == "  Next: harvest 011, then plan I4."
    assert "ask the agent to run /spine-harvest to record a next step" in next_step[1]


def test_next_step_with_empty_seeded_fields_falls_back(tmp_path: Path) -> None:
    template = (REPO_ROOT / "templates/docs/memory/ledger/progress.md").read_text(encoding="utf-8")
    _write(tmp_path, "docs/memory/ledger/progress.md", template)

    next_step = _section_lines(_render(tmp_path), "NEXT STEP")

    assert any("record a next step" in line for line in next_step)


def _digest_current_state(root: Path) -> list[str]:
    lines = memory.build_digest(root).split("\n")
    start = lines.index("## Current state") + 1
    return lines[start : lines.index("", start)]


def test_digest_shows_next_step_first_in_current_state(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_WITH_NEXT)

    state = _digest_current_state(tmp_path)

    assert state[0] == (
        "Next step: Harvest task 011 so its delivery is recorded"
        " — /spine-harvest @docs/memory/active_tasks/011-review-task.md"
    )
    assert state[1] == "- In flight: none."


def test_digest_current_state_unchanged_without_next_step(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_PLAIN)

    assert _digest_current_state(tmp_path)[0] == "- In flight: none."


def test_progress_frontmatter_keeps_current_state_budget_scoped_to_the_section(tmp_path: Path) -> None:
    _write(tmp_path, "docs/memory/ledger/progress.md", PROGRESS_WITH_NEXT)

    checks = {check.scope: check for check in memory.check_budgets(tmp_path)}

    current_state = checks[memory.CURRENT_STATE_SCOPE]
    assert current_state.chars == len(memory._section(PROGRESS_PLAIN, r"Current state").strip())


def test_progress_template_seeds_next_step_fields() -> None:
    template = (REPO_ROOT / "templates/docs/memory/ledger/progress.md").read_text(encoding="utf-8")

    fields = memory.read_frontmatter(template)
    for field in NEXT_FIELDS:
        assert field in fields
    assert memory._section(template, r"Current state") is not None


@pytest.mark.parametrize("relative", ["commands/spine-harvest.md", "commands/spine-plan.md", "rules/02-memory-bank.md"])
def test_harvest_plan_and_rule_name_the_next_step_fields(relative: str) -> None:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")

    for field in NEXT_FIELDS:
        assert f"`{field}`" in text, f"{relative} does not name {field}"


# =============================================================================
# Task 4: agents show the brief on request (AC6)
# =============================================================================


def test_core_protocol_tells_agents_to_show_the_brief_verbatim() -> None:
    rule = (REPO_ROOT / "rules/01-core-protocol.md").read_text(encoding="utf-8")

    assert "python3 .spine/scripts/spine.py brief" in rule
    assert "verbatim" in rule
    assert "where the project stands" in rule
    assert "Current state" in rule
    assert "spine.py update" in rule


# =============================================================================
# Task 5: docs and dogfooding (AC7)
# =============================================================================


@pytest.mark.parametrize("relative", ["README.md", "AGENTS.md", "rules/02-memory-bank.md"])
def test_docs_describe_the_pilot_brief(relative: str) -> None:
    text = (REPO_ROOT / relative).read_text(encoding="utf-8")

    for marker in ("spine.py brief", "`why:`", "`next_step`", "`next_command`", "`next_alternatives`", "verbatim"):
        assert marker in text, f"{relative} does not mention {marker}"


def test_spine_progress_records_a_next_step() -> None:
    progress = (REPO_ROOT / "docs/memory/ledger/progress.md").read_text(encoding="utf-8")

    recorded = memory.read_next_step(progress)
    assert recorded.step
    assert recorded.command
