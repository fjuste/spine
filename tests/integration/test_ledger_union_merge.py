"""Parallel harvests on two branches merge ledger INDEX.md without conflict (merge=union)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from spine_cli import memory  # noqa: E402
from spine_cli.constants import LEDGER_GITATTRIBUTES_LINE  # noqa: E402
from spine_cli.docs import seed_docs  # noqa: E402
from spine_cli.gitignore import ensure_gitattributes_line  # noqa: E402
from spine_cli.log import Log  # noqa: E402

CONFLICT_MARKER = "<<<<<<<"


def _git(project: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True, check=False)


def _commit_all(project: Path, message: str) -> None:
    assert _git(project, "add", "-A").returncode == 0
    result = _git(project, "commit", "-q", "-m", message)
    assert result.returncode == 0, result.stderr


def _harvest(project: Path, entry_id: str, date: str, title: str) -> None:
    path = project / "docs" / "memory" / "ledger" / "deliveries" / f"{entry_id}.md"
    path.write_text(
        f"---\nid: {entry_id}\ndate: {date}\ntitle: {title}\nsummary: {title} shipped.\n"
        f"tags:\n  - type/feature\ntask: {entry_id[11:]}\n---\n\n**Description:** {title}.\n",
        encoding="utf-8",
    )
    memory.write_indexes(project)


def test_parallel_harvests_merge_without_conflict(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert _git(project, "init", "-q", "-b", "main").returncode == 0
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test")
    _git(project, "config", "commit.gpgsign", "false")
    seed_docs(project, REPO_ROOT, Log())
    ensure_gitattributes_line(project, LEDGER_GITATTRIBUTES_LINE, Log())
    _commit_all(project, "seed")

    _git(project, "checkout", "-q", "-b", "feature/a")
    _harvest(project, "2026-01-02-001-alpha", "2026-01-02", "Alpha")
    _commit_all(project, "harvest alpha")

    _git(project, "checkout", "-q", "main")
    _git(project, "checkout", "-q", "-b", "feature/b")
    _harvest(project, "2026-01-03-002-beta", "2026-01-03", "Beta")
    _commit_all(project, "harvest beta")

    _git(project, "checkout", "-q", "feature/a")
    merge = _git(project, "merge", "-q", "--no-edit", "feature/b")

    assert merge.returncode == 0, merge.stdout + merge.stderr
    index = project / "docs" / "memory" / "ledger" / "deliveries" / "INDEX.md"
    merged = index.read_text(encoding="utf-8")
    assert CONFLICT_MARKER not in merged
    assert "Alpha" in merged and "Beta" in merged

    memory.write_indexes(project)
    regenerated = index.read_text(encoding="utf-8")
    entries = memory.collect_entries(project / "docs" / "memory", "deliveries")
    assert regenerated == memory.render_index("deliveries", entries)
    assert regenerated.index("Beta") < regenerated.index("Alpha")
