---
id: LEARN-002
date: 2026-11-14
title: A new validator check can invalidate the step that runs the validator
summary: Adding a check to a validator a command already runs can require moving that step; plans must list where the validator runs.
tags:
  - area/memory
  - type/refactor
task: 021-per-entry-ledger
---

**Symptoms:** Task 021 added a stale-`INDEX.md` check to `spine_validate.py memory`. The harvest step that runs the validator (task 020's 4a.1) sat right after `progress.md`, before learnings and decisions are written, so it would always have reported stale indexes. Found during execution; the step moved to 4c.1 (rework).

**Root cause:** The plan treated the validator change and the command text as separate work and never checked the order of the command steps that call the validator.

**Detect early:** A plan that adds a check to an existing validator or script also lists every command step that runs it, and confirms the step comes after everything the check depends on.

**Prevention:** In `/spine-plan`, for any change to `spine_validate.py` or `spine.py`, grep `commands/` for the invocation and note the step order in the Implementation Plan.

**Regression test:** `tests/unit/test_memory_budgets.py::test_harvest_runs_memory_budget_step` pins step 4c.1 after step 4c.

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
