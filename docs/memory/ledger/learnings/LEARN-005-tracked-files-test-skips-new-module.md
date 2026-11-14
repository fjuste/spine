---
id: LEARN-005
date: 2026-11-14
title: A test over git-tracked files skips a new untracked module
summary: The legacy-mention sweep reads only tracked files, so it passed before a new module was committed; `pytest | tail` then hid the failure.
tags:
  - type/incident
  - area/testing
task: 022-memory-migrate
---

**Symptoms:** Commit `e666045` added `scripts/spine_cli/migrate.py` after a green `pytest` run (317 passed). The next run failed `test_old_log_paths_only_mentioned_as_legacy` on that file. The commit after it (`69f9207`) still went in, because the check was `pytest … | tail`, which returns tail's exit code.

**Root cause:** The 021 sweep test lists files with `git ls-files`, so a new untracked module is invisible to it until it is committed. A pipe into `tail` masks pytest's exit code.

**Detect early:** A test that enumerates files through git, a new file in the change, or a test command piped into another tool.

**Prevention:** Run the full suite again right after a commit that adds new files (or `git add` them before the pre-commit run). Check pytest's own exit code: redirect to a file and `echo $?` instead of piping, or use `set -o pipefail`.

**Regression test:** `tests/unit/test_ledger_entries.py::test_old_log_paths_only_mentioned_as_legacy` (now green with `migrate.py` tracked).

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
