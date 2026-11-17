---
id: LEARN-007
date: 2026-11-17
title: Code added to the install pass also runs on every update
summary: run_install is update's reconcile pass; an unplanned git call there broke update --no-pull's no-subprocess contract. Check update tests when touching install.
tags:
  - type/rework
  - area/infra
  - stack/python
task: 026-pre-commit-memory-validation
---

**Symptoms:** An unplanned "refresh the installed hook block on every update" step in `run_install` made `test_update_no_pull_does_not_call_git` and `test_update_pulls_via_git` fail: `update --no-pull` now ran `git rev-parse` (the tests patch `subprocess.run` and assert no call / only the pull).

**Root cause:** `spine.py update` runs `run_install` with `update_mode=True` as its reconcile step, so every unconditional side effect added to `run_install` runs on every update. The step was added beyond the plan without checking the update path's contract.

**Detect early:** A change to `scripts/spine_cli/install.py` that runs a subprocess or reads git outside a flag guard; `update_mode` in a new condition.

**Prevention:** Gate new install side effects behind their opt-in flag, and run `tests/unit/test_spine_cli.py` (update tests) with any `install.py` change. Do not add steps the plan did not ask for.

**Regression test:** `tests/unit/test_spine_cli.py::test_update_no_pull_does_not_call_git`, `::test_update_pulls_via_git`.

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
