"""Tests for ``spine.py memory migrate`` (legacy log files -> per-entry ledger)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import spine  # noqa: E402
from spine_cli import memory, migrate  # noqa: E402

HEADING_DECISIONS = """# Decision Log

## Architectural Decisions

Intro line kept by the template.

---

### 2026-06-25 - Bootstrap baseline established

**Context:** First bootstrap.

**Decision:** Baseline.

---

### 2026-07-29 — Sharpen prototype pointer (Decision #27)

**Context:** Em dash separator.

### YYYY-MM-DD - TITLE

**Context:** placeholder body.

### 2026-08-01 – En dash title

#### Detail
Body with a deeper sub-heading.

### 2026-09-22-single-node - Single node deploy
**Tags:** area/infra, type/decision
**Task:** 031-single-node | **Branch:** feature/single-node

**Decision:** keep one node.
"""

TABLE_DECISIONS = """# Decision Log

| Data | Decisão | Porquê | Alternativas consideradas |
|------|---------|--------|---------------------------|
| 2026-11-03 | **Lote emitido no Emissor Nacional** — PDF conferido | O DANFSe confirma | Esperar a nota 519 |
| 2026-03-31 | Adotar `main` como branch canônica | Padrão moderno | Manter `master` |
| YYYY-MM-DD | placeholder | x | y |
"""

LEARNINGS = """# Learnings Registry

Recurring problems, root causes, and prevention notes.

---

## LEARN-001 — Example incident slug

**First seen:** 2026-01-15 | **Task:** 001-example-task
**Tags:** area/api, type/incident

**Symptoms:** Brief description.

## LEARN-002 — Loop invalid re-prompt without buttons

**First seen:** 2026-06-06 | **Task:** 044-fix-loop-invalid-buttons
**Tags:** area/chatbot, type/incident

### Sintomas
- Bot re-prompted.

### Recurrences
- 2026-06-09 — task 045 (again)

---

## LEARN-006 — Eager CID input

**Data:** 2026-06-12 (incidente) / 2026-06-13 (registro)

**Task:** `047-loop-cid`

Body text.
"""

H3_LEARNINGS = """# Learnings

### LEARN-003 - Report incomplete

**First seen:** 2026-07-01
**Tags:** area/reports

**Root cause:** missing persistence.
"""

PROGRESS = """# Progress

## Current state
- In flight: none.
- Next: migrate.

## Delivery log (newest first)

### 2026-11-14 — Memory budgets — digest-first limits
**Task:** 020-memory-budgets | **Branch:** feature/memory-budgets
**Tags:** type/feature, area/memory, stack/python
**Description:** New validator.

### 2026-07-08 — Hotfix without task
**Description:** No task line.

### YYYY-MM-DD — Title
**Task:** NNN-slug | **Branch:** feature/slug

## O que funciona (snapshot)
- Something works.
"""

PROGRESS_WITHOUT_LOG = """# Progress

## Current state
- In flight: none.

## O que funciona (snapshot)
- Something works.
"""


def _bank(
    root: Path,
    decision_log: str | None = HEADING_DECISIONS,
    learnings: str | None = LEARNINGS,
    progress: str | None = PROGRESS,
) -> Path:
    memory_dir = root / "docs" / "memory"
    for folder in memory.LEDGER_FOLDERS:
        (memory_dir / "ledger" / folder).mkdir(parents=True)
    (memory_dir / "global").mkdir(parents=True)
    if decision_log is not None:
        (memory_dir / "global" / "decision-log.md").write_text(decision_log, encoding="utf-8")
    if learnings is not None:
        (memory_dir / "ledger" / "learnings.md").write_text(learnings, encoding="utf-8")
    if progress is not None:
        (memory_dir / "ledger" / "progress.md").write_text(progress, encoding="utf-8")
    memory.write_indexes(root)
    return memory_dir


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted((root / "docs").rglob("*"))
        if path.is_file()
    }


def _by_id(entries: list[migrate.LegacyEntry]) -> dict[str, migrate.LegacyEntry]:
    return {entry.base_id: entry for entry in entries}


# Parsers ---------------------------------------------------------------------


def test_parse_heading_decisions() -> None:
    result = migrate.parse_decision_log(HEADING_DECISIONS)

    entries = _by_id(result.entries)
    assert list(entries) == [
        "2026-06-25-bootstrap-baseline-established",
        "2026-07-29-sharpen-prototype-pointer-decision-27",
        "2026-08-01-en-dash-title",
        "2026-09-22-single-node",
    ]
    assert entries["2026-07-29-sharpen-prototype-pointer-decision-27"].title == "Sharpen prototype pointer (Decision #27)"
    assert entries["2026-08-01-en-dash-title"].title == "En dash title"
    single = entries["2026-09-22-single-node"]
    assert (single.date, single.title) == ("2026-09-22", "Single node deploy")
    assert single.tags == ("area/infra", "type/decision")
    assert single.task == "031-single-node"
    assert all(entry.kind == "decisions" for entry in result.entries)
    assert result.unparsed == []


def test_parse_table_decisions() -> None:
    result = migrate.parse_decision_log(TABLE_DECISIONS)

    first, second = result.entries
    assert first.base_id == "2026-11-03-lote-emitido-no-emissor-nacional"
    assert first.title == "Lote emitido no Emissor Nacional"
    assert first.body == (
        "**Decision:** **Lote emitido no Emissor Nacional** — PDF conferido\n\n"
        "**Why:** O DANFSe confirma\n\n"
        "**Alternatives considered:** Esperar a nota 519\n"
    )
    assert second.title == "Adotar `main` como branch canônica"
    assert second.base_id == "2026-03-31-adotar-main-como-branch-canonica"
    assert (second.tags, second.task) == ((), "")
    assert len(result.placeholders) == 1
    assert result.unparsed == []


def test_parse_learnings_with_metadata_and_subheadings() -> None:
    result = migrate.parse_learnings(LEARNINGS)

    entries = _by_id(result.entries)
    assert list(entries) == ["LEARN-002", "LEARN-006"]
    loop = entries["LEARN-002"]
    assert (loop.date, loop.task) == ("2026-06-06", "044-fix-loop-invalid-buttons")
    assert loop.tags == ("area/chatbot", "type/incident")
    assert "### Sintomas\n- Bot re-prompted." in loop.body
    assert "### Recurrences\n- 2026-06-09" in loop.body
    eager = entries["LEARN-006"]
    assert (eager.date, eager.task, eager.tags) == ("2026-06-12", "047-loop-cid", ())
    assert result.unparsed == []

    h3 = migrate.parse_learnings(H3_LEARNINGS).entries
    assert [(entry.base_id, entry.title, entry.date) for entry in h3] == [
        ("LEARN-003", "Report incomplete", "2026-07-01")
    ]


def test_parse_delivery_log_section() -> None:
    result = migrate.parse_delivery_log(PROGRESS)

    assert result is not None
    first, second = result.entries
    assert first.base_id == "2026-11-14-020-memory-budgets"
    assert first.title == "Memory budgets — digest-first limits"
    assert first.tags == ("type/feature", "area/memory", "stack/python")
    assert first.task == "020-memory-budgets"
    assert first.line == PROGRESS.split("\n").index("### 2026-11-14 — Memory budgets — digest-first limits") + 1
    assert second.base_id == "2026-07-08-hotfix-without-task"
    assert result.unparsed == []
    assert migrate.parse_delivery_log(PROGRESS_WITHOUT_LOG) is None


def test_placeholders_are_skipped() -> None:
    assert [line for line, _ in migrate.parse_decision_log(HEADING_DECISIONS).placeholders] == [
        HEADING_DECISIONS.split("\n").index("### YYYY-MM-DD - TITLE") + 1
    ]
    assert len(migrate.parse_learnings(LEARNINGS).placeholders) == 1
    delivery = migrate.parse_delivery_log(PROGRESS)
    assert delivery is not None and len(delivery.placeholders) == 1
    for template in ("### [DATE] - [TITLE]\n**Context:** [Fill in]\n", "### [DATA] - [TITULO]\n"):
        parsed = migrate.parse_decision_log("# Decision Log\n\n## Architectural Decisions\n\n" + template)
        assert (parsed.entries, parsed.unparsed, len(parsed.placeholders)) == ([], [], 1)


def test_summary_is_title_capped() -> None:
    long_title = "Word " * 60
    text = f"# Decision Log\n\n### 2026-01-01 - {long_title}\n\nBody.\n"

    entry = migrate.parse_decision_log(text).entries[0]

    assert len(entry.title) == memory.ENTRY_SUMMARY_MAX_CHARS
    assert entry.summary == entry.title
    assert entry.summary.endswith(memory.ELLIPSIS)
    short = migrate.parse_learnings(H3_LEARNINGS).entries[0]
    assert short.summary == short.title


def test_slug_folds_accents_and_caps_length() -> None:
    assert migrate.slugify("Decisão: Ação rápida — já!") == "decisao-acao-rapida-ja"
    long_slug = migrate.slugify("alpha " * 30)
    assert len(long_slug) <= migrate.SLUG_MAX_CHARS
    assert not long_slug.endswith("-")
    assert long_slug.split("-") == ["alpha"] * len(long_slug.split("-"))
    assert migrate.slugify("—") == migrate.FALLBACK_SLUG


def test_duplicate_ids_get_suffixes(tmp_path: Path) -> None:
    text = "# Decision Log\n\n### 2026-01-01 - Same\n\nA.\n\n### 2026-01-01 - Same\n\nB.\n\n### 2026-01-01 - Same\n\nC.\n"
    _bank(tmp_path, decision_log=text, learnings=None, progress=None)

    plan = migrate.build_plan(tmp_path)

    ids = [item.entry_id for item in plan.planned]
    assert ids == ["2026-01-01-same", "2026-01-01-same-2", "2026-01-01-same-3"]
    report = migrate.render_report(plan, apply=False)
    assert "2026-01-01-same-2" in report and "suffix" in report


def test_body_is_copied_verbatim() -> None:
    entries = _by_id(migrate.parse_decision_log(HEADING_DECISIONS).entries)

    assert entries["2026-06-25-bootstrap-baseline-established"].body == "**Context:** First bootstrap.\n\n**Decision:** Baseline.\n"
    assert entries["2026-08-01-en-dash-title"].body == "#### Detail\nBody with a deeper sub-heading.\n"
    assert entries["2026-09-22-single-node"].body.startswith("**Tags:** area/infra, type/decision\n**Task:** 031-single-node")


# Rendering -------------------------------------------------------------------


def test_rendered_entry_round_trips_through_read_entry(tmp_path: Path) -> None:
    entries = (
        migrate.parse_decision_log(HEADING_DECISIONS).entries
        + migrate.parse_decision_log(TABLE_DECISIONS).entries
        + migrate.parse_learnings(LEARNINGS).entries
        + migrate.parse_learnings("## LEARN-009 - #hash: colon title\n\nBody.\n").entries
    )
    for index, entry in enumerate(entries):
        path = tmp_path / f"{index}.md"
        path.write_text(migrate.render_entry(entry, entry.base_id), encoding="utf-8")

        read = memory.read_entry(path)

        assert (read.entry_id, read.date, read.title, read.summary, read.tags, read.task) == (
            entry.base_id,
            entry.date,
            entry.title,
            entry.summary,
            entry.tags,
            entry.task,
        )
        assert memory.strip_frontmatter(path.read_text(encoding="utf-8")).lstrip("\n") == entry.body


def test_migrated_entries_pass_summary_checks(tmp_path: Path) -> None:
    long_title = "Long " * 60
    _bank(tmp_path, decision_log=HEADING_DECISIONS + f"\n### 2026-10-01 - {long_title}\n\nBody.\n")

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert all(check.problems == () for check in memory.check_ledger(tmp_path))


# Plan, report and apply ------------------------------------------------------


def test_dry_run_reports_and_writes_nothing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path)
    before = _snapshot(tmp_path)

    assert spine.main(["memory", "migrate", "--project-root", str(tmp_path)]) == 0

    assert _snapshot(tmp_path) == before
    out = capsys.readouterr().out
    assert "dry run" in out
    assert "ledger/decisions/2026-06-25-bootstrap-baseline-established.md" in out
    assert "ledger/learnings/LEARN-002-loop-invalid-re-prompt-without-buttons.md" in out
    assert "ledger/deliveries/2026-11-14-020-memory-budgets.md" in out
    assert "placeholder" in out
    assert "--apply" in out


def test_dry_run_lists_dropped_preamble(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path)

    assert migrate.run_migrate(str(tmp_path), apply=False) == 0

    out = capsys.readouterr().out
    assert "preamble" in out
    assert "Intro line kept by the template." in out
    assert "Recurring problems, root causes, and prevention notes." in out


def test_no_legacy_files_prints_nothing_to_migrate(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path, decision_log=None, learnings=None, progress=PROGRESS_WITHOUT_LOG)

    assert migrate.run_migrate(str(tmp_path), apply=False) == 0
    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert capsys.readouterr().out.count("nothing to migrate") == 2


def test_apply_writes_entries_and_removes_legacy(tmp_path: Path) -> None:
    memory_dir = _bank(tmp_path)

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert not (memory_dir / "global" / "decision-log.md").exists()
    assert not (memory_dir / "ledger" / "learnings.md").exists()
    assert (memory_dir / "ledger" / "decisions" / "2026-09-22-single-node.md").is_file()
    assert (memory_dir / "ledger" / "learnings" / "LEARN-006-eager-cid-input.md").is_file()
    assert (memory_dir / "ledger" / "deliveries" / "2026-07-08-hotfix-without-task.md").is_file()
    counts = {folder: len(memory.collect_entries(memory_dir, folder)) for folder in memory.LEDGER_FOLDERS}
    assert counts == {"decisions": 4, "learnings": 2, "deliveries": 2}
    checks = memory.check_budgets(tmp_path)
    assert not [check for check in checks if check.over and check.detail == memory.LOG_HINT]
    assert memory.LEGACY_LABEL not in memory.build_digest(tmp_path)


def test_apply_keeps_other_progress_sections(tmp_path: Path) -> None:
    memory_dir = _bank(tmp_path)

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert (memory_dir / "ledger" / "progress.md").read_text(encoding="utf-8") == PROGRESS_WITHOUT_LOG.replace(
        "- In flight: none.\n", "- In flight: none.\n- Next: migrate.\n"
    )


def test_apply_cuts_trailing_delivery_log(tmp_path: Path) -> None:
    progress = PROGRESS.split("## O que funciona")[0]
    memory_dir = _bank(tmp_path, progress=progress)

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert (memory_dir / "ledger" / "progress.md").read_text(encoding="utf-8") == (
        "# Progress\n\n## Current state\n- In flight: none.\n- Next: migrate.\n"
    )


def test_apply_regenerates_indexes(tmp_path: Path) -> None:
    memory_dir = _bank(tmp_path)

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    for folder in memory.LEDGER_FOLDERS:
        index = memory.index_path(memory_dir, folder).read_text(encoding="utf-8")
        assert index == memory.render_index(folder, memory.collect_entries(memory_dir, folder))
    assert "Eager CID input" in memory.index_path(memory_dir, "learnings").read_text(encoding="utf-8")


def test_apply_creates_missing_ledger_folders(tmp_path: Path) -> None:
    memory_dir = tmp_path / "docs" / "memory"
    (memory_dir / "global").mkdir(parents=True)
    (memory_dir / "global" / "decision-log.md").write_text(TABLE_DECISIONS, encoding="utf-8")

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert len(memory.collect_entries(memory_dir, "decisions")) == 2
    assert memory.index_path(memory_dir, "decisions").is_file()


def test_apply_is_idempotent(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _bank(tmp_path)
    assert migrate.run_migrate(str(tmp_path), apply=True) == 0
    after_first = _snapshot(tmp_path)
    capsys.readouterr()

    assert migrate.run_migrate(str(tmp_path), apply=True) == 0

    assert "nothing to migrate" in capsys.readouterr().out
    assert _snapshot(tmp_path) == after_first


def test_apply_refuses_on_unparsed_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    table = TABLE_DECISIONS + "\nA note written after the table.\n"
    learnings = LEARNINGS + "\n## Notes\n\nStray section.\n"
    _bank(tmp_path, decision_log=table, learnings=learnings)
    before = _snapshot(tmp_path)

    assert spine.main(["memory", "migrate", "--apply", "--project-root", str(tmp_path)]) == 1

    assert _snapshot(tmp_path) == before
    out = capsys.readouterr().out
    table_line = table.split("\n").index("A note written after the table.") + 1
    notes_line = learnings.split("\n").index("## Notes") + 1
    assert f"line {table_line}" in out and "A note written after the table." in out
    assert f"line {notes_line}" in out and "Stray section." in out
    assert "unparsed" in out.lower()


def test_apply_refuses_on_existing_entry_conflict(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    memory_dir = _bank(tmp_path)
    existing = memory_dir / "ledger" / "learnings" / "LEARN-002-already-harvested.md"
    existing.write_text("---\nid: LEARN-002\ndate: 2026-11-01\ntitle: Already harvested\nsummary: Done.\n---\n", encoding="utf-8")
    memory.write_indexes(tmp_path)
    before = _snapshot(tmp_path)

    assert migrate.run_migrate(str(tmp_path), apply=True) == 1

    assert _snapshot(tmp_path) == before
    out = capsys.readouterr().out
    assert "conflict" in out.lower() and "LEARN-002" in out


def test_parse_h2_and_bracketed_date_decisions() -> None:
    text = (
        "# Decision Log\n\n## Decisoes Arquiteturais\n\n"
        "### [2026-04-15] - Bootstrap do Memory Bank\n**Contexto:** A.\n\n"
        "## 2026-11-04 — Data Lineage na POC (Task 013)\n\n**Contexto:** B.\n\n### Detalhe\nC.\n"
    )

    result = migrate.parse_decision_log(text)

    assert [(entry.base_id, entry.title) for entry in result.entries] == [
        ("2026-04-15-bootstrap-do-memory-bank", "Bootstrap do Memory Bank"),
        ("2026-11-04-data-lineage-na-poc-task-013", "Data Lineage na POC (Task 013)"),
    ]
    assert result.entries[1].body == "**Contexto:** B.\n\n### Detalhe\nC.\n"
    assert result.unparsed == []


def test_intro_text_without_entries_is_preamble() -> None:
    text = "# Learnings Registry\n\nRecurring problems.\n\n---\n\n_No learnings recorded yet._\n"

    result = migrate.parse_learnings(text)

    assert (result.entries, result.unparsed) == ([], [])
    assert [line for _, line in result.preamble] == ["# Learnings Registry", "Recurring problems.", "_No learnings recorded yet._"]


def test_unrecognized_entry_level_heading_is_unparsed() -> None:
    text = (
        "# Decision Log\n\n### 2026-03 - Month-only date\n**Context:** A.\n\n"
        "### 2026-04-01 - Dated\n\nBody.\n\n### Standing rule without date\n**Decision:** B.\n"
    )

    result = migrate.parse_decision_log(text)

    assert [entry.title for entry in result.entries] == ["Dated"]
    assert [line for line, _ in result.unparsed] == [3, 4, 10, 11]
    assert result.preamble == [(1, "# Decision Log")]


def test_headings_inside_code_fences_stay_in_body() -> None:
    text = (
        "# Progress\n\n## Delivery log (newest first)\n\n"
        "### 2026-05-01 — Deploy fix\n**Task:** 040-deploy-fix\n\n"
        "```bash\n# expect HTTP/2 200\ncurl -I https://example.test\n```\n\n"
        "~~~\n## not a heading either\n~~~\n"
    )

    result = migrate.parse_delivery_log(text)

    assert result is not None and result.unparsed == []
    assert result.entries[0].body.endswith("```bash\n# expect HTTP/2 200\ncurl -I https://example.test\n```\n\n~~~\n## not a heading either\n~~~\n")


# Docs ------------------------------------------------------------------------

MIGRATE_DOCS = (
    "rules/02-memory-bank.md",
    "commands/spine-harvest.md",
    "commands/spine-update.md",
    "README.md",
    "AGENTS.md",
)


def test_docs_describe_memory_migrate() -> None:
    for relative in MIGRATE_DOCS:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        assert "spine.py memory migrate" in text, relative
        assert "--apply" in text, relative
    rule = (REPO_ROOT / "rules/02-memory-bank.md").read_text(encoding="utf-8")
    for phrase in ("dry run", "verbatim", "unparsed", "conflict", "memory index", "## Delivery log"):
        assert phrase in rule, phrase


def test_migrate_not_called_planned() -> None:
    for relative in MIGRATE_DOCS:
        for number, line in enumerate((REPO_ROOT / relative).read_text(encoding="utf-8").split("\n"), start=1):
            if "migrate" in line:
                assert not re.search(r"\bplanned\b", line, re.IGNORECASE), f"{relative}:{number}"
