"""Tests for the per-entry ledger (ledger/{decisions,learnings,deliveries}/ + INDEX.md)."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402


def _entry(
    entry_id: str,
    date: str,
    title: str,
    summary: str = "One-line summary.",
    tags: str = "  - area/memory\n  - type/feature\n",
    task: str = "",
    superseded_by: str = "",
    body: str = "Body.\n",
) -> str:
    return (
        "---\n"
        f"id: {entry_id}\n"
        f"date: {date}\n"
        f"title: {title}\n"
        f"summary: {summary}\n"
        f"tags:\n{tags}"
        f"task: {task}\n"
        f"superseded_by: {superseded_by}\n"
        "---\n\n"
        f"{body}"
    )


def _write_entry(root: Path, folder: str, name: str, text: str) -> Path:
    path = root / "docs" / "memory" / "ledger" / folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _memory_dir(root: Path) -> Path:
    return root / "docs" / "memory"


# =============================================================================
# Task 1: ledger entry model
# =============================================================================


def test_frontmatter_list_tags_are_parsed() -> None:
    block = "---\ntags:\n  - area/memory\n  - type/feature\ngoal: x\n---\n"
    inline = "---\ntags: [area/api, 'type/bug']\n---\n"
    single = "---\ntags: area/infra\n---\n"
    assert memory.read_frontmatter_list(block, "tags") == ["area/memory", "type/feature"]
    assert memory.read_frontmatter_list(inline, "tags") == ["area/api", "type/bug"]
    assert memory.read_frontmatter_list(single, "tags") == ["area/infra"]
    assert memory.read_frontmatter_list("---\ngoal: x\n---\n", "tags") == []
    assert memory.read_frontmatter_list("# no frontmatter\n", "tags") == []


def test_collect_entries_reads_frontmatter(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "decisions",
        "2026-11-12-memory-digest.md",
        _entry("2026-11-12-memory-digest", "2026-11-12", "Core SYNC reads the digest", task="018-memory-digest"),
    )

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "decisions")

    assert entry.entry_id == "2026-11-12-memory-digest"
    assert entry.date == "2026-11-12"
    assert entry.title == "Core SYNC reads the digest"
    assert entry.summary == "One-line summary."
    assert entry.tags == ("area/memory", "type/feature")
    assert entry.task == "018-memory-digest"
    assert entry.superseded_by == ""
    assert entry.filename == "2026-11-12-memory-digest.md"


def test_collect_entries_ignores_template_and_index(tmp_path: Path) -> None:
    _write_entry(tmp_path, "learnings", "_template.md", _entry("LEARN-000", "2026-01-01", "Template"))
    _write_entry(tmp_path, "learnings", "INDEX.md", "# Learnings\n")
    _write_entry(tmp_path, "learnings", "notes.txt", "not markdown")
    _write_entry(tmp_path, "learnings", "LEARN-001-flaky.md", _entry("LEARN-001", "2026-02-01", "Flaky"))

    entries = memory.collect_entries(_memory_dir(tmp_path), "learnings")

    assert [entry.entry_id for entry in entries] == ["LEARN-001"]


def test_collect_entries_newest_first(tmp_path: Path) -> None:
    for name, date in (("2026-01-05-a.md", "2026-01-05"), ("2026-03-01-b.md", "2026-03-01"), ("2026-02-01-c.md", "2026-02-01")):
        _write_entry(tmp_path, "deliveries", name, _entry(name[:-3], date, name))

    entries = memory.collect_entries(_memory_dir(tmp_path), "deliveries")

    assert [entry.date for entry in entries] == ["2026-03-01", "2026-02-01", "2026-01-05"]


def test_collect_entries_falls_back_to_filename(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-04-01-no-frontmatter.md", "# Just a body\n")

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "decisions")

    assert entry.entry_id == "2026-04-01-no-frontmatter"
    assert entry.title == "2026-04-01-no-frontmatter"
    assert entry.summary == ""


def test_collect_entries_missing_folder_returns_empty(tmp_path: Path) -> None:
    assert memory.collect_entries(_memory_dir(tmp_path), "decisions") == []


def test_learning_recurrences_are_counted(tmp_path: Path) -> None:
    body = (
        "**Symptoms:** x\n\n"
        "**Recurrences:**\n"
        "- (append-only — one line per recurrence with date and task ref)\n"
        "- 2026-03-01 — task 012-foo (again)\n"
        "- 2026-04-01 — task 015-bar (again)\n"
        "\n"
        "Trailing paragraph.\n"
        "- not a recurrence\n"
    )
    _write_entry(tmp_path, "learnings", "LEARN-002-x.md", _entry("LEARN-002", "2026-02-01", "X", body=body))

    [entry] = memory.collect_entries(_memory_dir(tmp_path), "learnings")

    assert entry.recurrences == 2


# =============================================================================
# Task 2: INDEX.md generation
# =============================================================================


def _rows(index: str) -> list[str]:
    lines = [line for line in index.split("\n") if line.startswith("| ")]
    return lines[1:]  # drop the header row (the separator starts with "|-")


def test_index_lists_entries_newest_first(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-old.md", _entry("2026-01-01-old", "2026-01-01", "Old decision"))
    _write_entry(tmp_path, "decisions", "2026-05-01-new.md", _entry("2026-05-01-new", "2026-05-01", "New decision"))

    index = memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions"))

    rows = _rows(index)
    assert len(rows) == 2
    assert rows[0].startswith("| 2026-05-01 | [New decision](2026-05-01-new.md) | active |")
    assert rows[1].startswith("| 2026-01-01 | [Old decision](2026-01-01-old.md) | active |")
    assert "area/memory, type/feature" in rows[0]
    assert rows[0].endswith("| One-line summary. |")
    assert "spine.py memory index" in index


def test_index_marks_superseded_decisions(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "decisions",
        "2026-01-01-old.md",
        _entry("2026-01-01-old", "2026-01-01", "Old", superseded_by="2026-05-01-new"),
    )

    index = memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions"))

    assert "| superseded by [2026-05-01-new](2026-05-01-new.md) |" in _rows(index)[0]


def test_index_counts_learning_recurrences(tmp_path: Path) -> None:
    body = "**Recurrences:**\n- 2026-03-01 — task 012-foo\n- 2026-04-01 — task 015-bar\n"
    _write_entry(tmp_path, "learnings", "LEARN-002-x.md", _entry("LEARN-002", "2026-02-01", "Flaky test", body=body))

    [row] = _rows(memory.render_index("learnings", memory.collect_entries(_memory_dir(tmp_path), "learnings")))

    assert row.startswith("| LEARN-002 | [Flaky test](LEARN-002-x.md) | area/memory, type/feature | 2 |")


def test_index_shows_delivery_task(tmp_path: Path) -> None:
    _write_entry(
        tmp_path,
        "deliveries",
        "2026-11-12-019-self-install.md",
        _entry("2026-11-12-019-self-install", "2026-11-12", "Self-install", task="019-self-install"),
    )

    [row] = _rows(memory.render_index("deliveries", memory.collect_entries(_memory_dir(tmp_path), "deliveries")))

    assert row.startswith("| 2026-11-12 | [Self-install](2026-11-12-019-self-install.md) | 019-self-install |")


def test_index_escapes_pipes(tmp_path: Path) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A | B", summary="x | y"))

    [row] = _rows(memory.render_index("decisions", memory.collect_entries(_memory_dir(tmp_path), "decisions")))

    assert "[A \\| B]" in row and "x \\| y" in row


def test_empty_index_has_header_only() -> None:
    index = memory.render_index("learnings", [])
    assert index.startswith("# Learnings\n")
    assert _rows(index) == []
    assert "| ID | Title | Tags | Recurrences | Summary |" in index


def test_index_ignores_template_and_index(tmp_path: Path) -> None:
    _write_entry(tmp_path, "learnings", "_template.md", _entry("LEARN-000", "2026-01-01", "Template entry"))
    _write_entry(tmp_path, "learnings", "LEARN-001-a.md", _entry("LEARN-001", "2026-02-01", "Real entry"))

    memory.write_indexes(tmp_path)

    index = (_memory_dir(tmp_path) / "ledger" / "learnings" / "INDEX.md").read_text(encoding="utf-8")
    assert "Real entry" in index
    assert "Template entry" not in index


def test_index_is_idempotent(tmp_path: Path) -> None:
    _write_entry(tmp_path, "deliveries", "2026-02-01-a.md", _entry("2026-02-01-a", "2026-02-01", "A"))
    _write_entry(tmp_path, "decisions", "2026-02-01-b.md", _entry("2026-02-01-b", "2026-02-01", "B"))

    written = memory.write_indexes(tmp_path)
    index_path = _memory_dir(tmp_path) / "ledger" / "deliveries" / "INDEX.md"
    first = index_path.read_text(encoding="utf-8")

    assert sorted(path.parent.name for path in written) == ["decisions", "deliveries"]
    assert memory.write_indexes(tmp_path) == []
    assert index_path.read_text(encoding="utf-8") == first


def test_write_indexes_skips_missing_folders(tmp_path: Path) -> None:
    (_memory_dir(tmp_path) / "ledger").mkdir(parents=True)

    assert memory.write_indexes(tmp_path) == []
    assert not (_memory_dir(tmp_path) / "ledger" / "decisions").exists()


def test_cli_memory_index_writes_indexes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import spine

    _write_entry(tmp_path, "decisions", "2026-02-01-b.md", _entry("2026-02-01-b", "2026-02-01", "B"))

    assert spine.main(["memory", "index", "--project-root", str(tmp_path)]) == 0
    assert "docs/memory/ledger/decisions/INDEX.md" in capsys.readouterr().out

    assert spine.main(["memory", "index", "--project-root", str(tmp_path)]) == 0
    assert "up to date" in capsys.readouterr().out


# =============================================================================
# Task 3: digest Logs section
# =============================================================================


def _logs_section(digest: str) -> str:
    return digest.split("## Logs\n", 1)[1].split("\n## ", 1)[0]


def test_digest_lists_ledger_folders(tmp_path: Path) -> None:
    for day in range(1, 8):
        name = f"2026-01-0{day}-d{day}"
        superseded = "2026-01-07-d7" if day == 1 else ""
        _write_entry(tmp_path, "decisions", f"{name}.md", _entry(name, f"2026-01-0{day}", f"Decision {day}", superseded_by=superseded))
    _write_entry(tmp_path, "learnings", "LEARN-001-a.md", _entry("LEARN-001", "2026-02-01", "Flaky"))
    (_memory_dir(tmp_path) / "ledger" / "deliveries").mkdir(parents=True)

    logs = _logs_section(memory.build_digest(tmp_path))

    assert "- ledger/decisions/: 7 entries (1 superseded), see INDEX.md; newest:" in logs
    assert "  - 2026-01-07 — Decision 7" in logs
    assert "Decision 2" not in logs  # only the newest 5
    assert "- ledger/learnings/: 1 entry, see INDEX.md; newest:" in logs
    assert "  - LEARN-001 — Flaky" in logs
    assert "- ledger/deliveries/: 0 entries" in logs


def test_digest_labels_legacy_files(tmp_path: Path) -> None:
    memory_dir = _memory_dir(tmp_path)
    (memory_dir / "global").mkdir(parents=True)
    (memory_dir / "global" / "decision-log.md").write_text("# Decision Log\n\n### 2026-01-01 - Old\nx\n", encoding="utf-8")
    (memory_dir / "ledger").mkdir(parents=True)
    (memory_dir / "ledger" / "progress.md").write_text(
        "## Current state\n- Next: x\n\n## Delivery log (newest first)\n### 2026-01-02 — Shipped\n", encoding="utf-8"
    )

    logs = _logs_section(memory.build_digest(tmp_path))

    assert f"- global/decision-log.md: 1 entry {memory.LEGACY_LABEL}; newest:" in logs
    assert f"- ledger/progress.md delivery log: 1 entry {memory.LEGACY_LABEL}; newest:" in logs


def test_digest_omits_progress_without_delivery_log(tmp_path: Path) -> None:
    memory_dir = _memory_dir(tmp_path)
    (memory_dir / "ledger").mkdir(parents=True)
    (memory_dir / "ledger" / "progress.md").write_text("## Current state\n- Next: x\n", encoding="utf-8")

    logs = _logs_section(memory.build_digest(tmp_path))

    assert "progress.md" not in logs
    assert logs.strip() == "(none)"


# =============================================================================
# Task 4: validator warnings
# =============================================================================


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("spine_validate", REPO_ROOT / "scripts" / "spine_validate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sv = _load_validator()


def _validate(root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> tuple[int, str, str]:
    monkeypatch.chdir(root)
    code = sv.main(["memory"])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def _check(root: Path, folder: str) -> memory.LedgerCheck:
    [check] = [item for item in memory.check_ledger(root) if item.scope.endswith(f"ledger/{folder}/")]
    return check


def test_validate_warns_missing_entry_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A", summary=""))
    _write_entry(tmp_path, "decisions", "2026-01-02-b.md", _entry("2026-01-02-b", "2026-01-02", "B", summary=""))
    memory.write_indexes(tmp_path)

    code, _, err = _validate(tmp_path, monkeypatch, capsys)

    assert code == 0
    warnings = [line for line in err.splitlines() if "without `summary:`" in line]
    assert len(warnings) == 1
    assert "2 entries" in warnings[0]
    assert "2026-01-01-a.md" in warnings[0] and "2026-01-02-b.md" in warnings[0]


def test_validate_warns_long_entry_summary(tmp_path: Path) -> None:
    long_summary = "s" * (memory.ENTRY_SUMMARY_MAX_CHARS + 1)
    exact_summary = "s" * memory.ENTRY_SUMMARY_MAX_CHARS
    _write_entry(tmp_path, "learnings", "LEARN-001-a.md", _entry("LEARN-001", "2026-01-01", "A", summary=long_summary))
    _write_entry(tmp_path, "learnings", "LEARN-002-b.md", _entry("LEARN-002", "2026-01-02", "B", summary=exact_summary))
    memory.write_indexes(tmp_path)

    check = _check(tmp_path, "learnings")

    assert check.entries == 2
    [problem] = check.problems
    assert f"over {memory.ENTRY_SUMMARY_MAX_CHARS} chars" in problem
    assert "LEARN-001-a.md" in problem and "LEARN-002-b.md" not in problem


def test_validate_warns_stale_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_entry(tmp_path, "deliveries", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A"))
    memory.write_indexes(tmp_path)
    _write_entry(tmp_path, "deliveries", "2026-01-02-b.md", _entry("2026-01-02-b", "2026-01-02", "B"))

    code, _, err = _validate(tmp_path, monkeypatch, capsys)

    assert code == 0
    assert "INDEX.md is stale" in err
    assert memory.INDEX_CMD in err


def test_validate_warns_missing_index(tmp_path: Path) -> None:
    _write_entry(tmp_path, "deliveries", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A"))

    assert any("INDEX.md missing" in problem for problem in _check(tmp_path, "deliveries").problems)


def test_validate_fresh_ledger_is_ok(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_entry(tmp_path, "decisions", "2026-01-01-a.md", _entry("2026-01-01-a", "2026-01-01", "A"))
    memory.write_indexes(tmp_path)

    code, out, err = _validate(tmp_path, monkeypatch, capsys)

    assert code == 0
    assert "docs/memory/ledger/decisions/: OK (1 entry, INDEX.md up to date)" in out
    assert "WARNING:" not in err


def test_validate_legacy_file_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    limit = memory.LOG_BUDGET_CHARS["ledger/learnings.md"]
    path = _memory_dir(tmp_path) / "ledger" / "learnings.md"
    path.parent.mkdir(parents=True)
    path.write_text("x" * (limit + 1), encoding="utf-8")

    _, _, err = _validate(tmp_path, monkeypatch, capsys)

    assert "legacy" in memory.LOG_HINT and "migrate" in memory.LOG_HINT
    assert f"docs/memory/ledger/learnings.md: {limit + 1:,} chars > {limit:,} — {memory.LOG_HINT}" in err


# =============================================================================
# Task 5: templates and seeds
# =============================================================================


def _seed(project: Path) -> None:
    from spine_cli.docs import seed_docs
    from spine_cli.log import Log

    project.mkdir(exist_ok=True)
    seed_docs(project, REPO_ROOT, Log())


def test_seed_creates_ledger_folders(tmp_path: Path) -> None:
    _seed(tmp_path)

    ledger = _memory_dir(tmp_path) / "ledger"
    for folder in memory.LEDGER_FOLDERS:
        assert (ledger / folder / "_template.md").is_file()
        assert (ledger / folder / "INDEX.md").read_text(encoding="utf-8") == memory.render_index(folder, [])
    progress = (ledger / "progress.md").read_text(encoding="utf-8")
    assert "## Current state" in progress
    assert "## Delivery log" not in progress


def test_seed_skips_legacy_log_templates(tmp_path: Path) -> None:
    from spine_cli.constants import DOCS_SEED_PATHS

    _seed(tmp_path)

    assert not (_memory_dir(tmp_path) / "global" / "decision-log.md").exists()
    assert not (_memory_dir(tmp_path) / "ledger" / "learnings.md").exists()
    assert "docs/memory/global/decision-log.md" not in DOCS_SEED_PATHS
    assert "docs/memory/ledger/learnings.md" not in DOCS_SEED_PATHS


def test_seeded_ledger_passes_checks(tmp_path: Path) -> None:
    _seed(tmp_path)

    checks = memory.check_ledger(tmp_path)

    assert [check.entries for check in checks] == [0, 0, 0]
    assert all(not check.problems for check in checks)
    assert memory.write_indexes(tmp_path) == []


@pytest.mark.parametrize("folder", memory.LEDGER_FOLDERS)
def test_entry_templates_have_frontmatter_fields(folder: str) -> None:
    text = memory.read_text(REPO_ROOT / "templates" / "docs" / "memory" / "ledger" / folder / "_template.md")
    fields = memory.read_frontmatter(text)
    for key in ("id", "date", "title", "summary", "task"):
        assert key in fields, f"{folder} template missing {key}"
    assert memory.read_frontmatter_list(text, "tags")
    assert ("superseded_by" in fields) == (folder == "decisions")
    if folder == "learnings":
        assert "**Recurrences:**" in text


# =============================================================================
# Task 7: rules, commands, skills and docs
# =============================================================================

OLD_LOG_RE = re.compile(r"decision-log|learnings\.md|delivery log", re.IGNORECASE)
SWEEP_EXCLUDED_PREFIXES = ("tests/", "docs/")


def _read_repo(relative: str) -> str:
    return memory.read_text(REPO_ROOT / relative)


def test_harvest_writes_ledger_entries() -> None:
    text = _read_repo("commands/spine-harvest.md")
    for needle in (
        "ledger/deliveries/",
        "ledger/learnings/INDEX.md",
        "ledger/decisions/",
        "superseded_by",
        "python3 .spine/scripts/spine.py memory index",
        "→ DEC ",
        "→ LEARN-",
    ):
        assert needle in text, needle
    assert re.search(r"legacy[^\n]*learnings\.md", text), "recurrence check must also search a legacy learnings.md"


def test_bootstrap_writes_baseline_decision_entry() -> None:
    text = _read_repo("commands/spine-bootstrap.md")
    assert "ledger/decisions/" in text
    assert "baseline" in text
    assert "spine.py memory index" in text


@pytest.mark.parametrize("relative", ["commands/spine-plan.md", "skills/grill-me/SKILL.md"])
def test_plan_and_grill_read_decisions_index(relative: str) -> None:
    assert "ledger/decisions/INDEX.md" in _read_repo(relative)


def test_memory_bank_rule_documents_ledger_entries() -> None:
    text = _read_repo("rules/02-memory-bank.md")
    assert "## Ledger entries" in text
    section = text.split("## Ledger entries", 1)[1].split("\n## ", 1)[0]
    for needle in (
        "INDEX.md",
        "merge=union",
        "superseded_by",
        "summary:",
        f"{memory.ENTRY_SUMMARY_MAX_CHARS}",
        "python3 .spine/scripts/spine.py memory index",
        "legacy",
        "LEARN-NNN",
    ):
        assert needle in section, needle
    for folder in memory.LEDGER_FOLDERS:
        assert f"{folder}/" in section


def test_old_log_paths_only_mentioned_as_legacy() -> None:
    files = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.split()
    offenders: list[str] = []
    for relative in files:
        if relative.startswith(SWEEP_EXCLUDED_PREFIXES) or not (REPO_ROOT / relative).is_file():
            continue
        try:
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if OLD_LOG_RE.search(line) and "legacy" not in line.lower():
                offenders.append(f"{relative}:{number}: {line.strip()[:120]}")
    assert not offenders, "old log layout mentioned without 'legacy':\n" + "\n".join(offenders)
