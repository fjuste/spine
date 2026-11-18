---
task_id: 024
title: Memory validator warns on stale open tasks
goal: "`spine_validate.py memory` names the files in `active_tasks/` that need a human to close them: tasks without a valid status, REVIEW tasks not updated in over 14 days, and DONE tasks never moved to `completed_tasks/`"
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/validator-stale-open-tasks
base: develop
execution_skill: executing-plans
roadmap_idea: I35
created_at: 2026-11-16
updated_at: 2026-11-16
completed_at: 2026-11-16
related_learnings:
  - LEARN-002
---

# 024-validator-stale-open-tasks

## Discovery notes

- 2026-11-16 — Survey of the 11 local consumer banks plus Spine (read-only): 31 open tasks without a frontmatter status in 3 banks (Spine 7, a billing bank 20, another 3); 9 REVIEW tasks in 7 banks, last updated 33–163 days ago; 8 DONE tasks still in `active_tasks/` across 3 banks.
- 2026-11-16 — Human chose a 14-day REVIEW threshold (14 and 30 both flag all 9 real REVIEW tasks today; 14 flags while context is fresh).
- 2026-11-16 — Human chose to include DONE tasks left in `active_tasks/` (same fix, same check), beyond the I35 row's two cases.
- LEARN-002 applies: `/spine-harvest` step 4c.1 runs this validator before step 5 closes the task, so a task harvested after more than 14 days in REVIEW flags itself. The harvest procedure must say that this warning clears at step 5.

## Objective

Add an open-task health check to `spine_validate.py memory`, next to the budget and ledger checks. It reads frontmatter of the files the digest treats as tasks (`active_tasks/NNN-*.md`; `_task-template.md` ignored) and reports one `WARNING:` line per problem kind, listing up to 5 file names plus `(+N more)` like the ledger check:

| Problem | Condition | Fix named in the warning |
|---|---|---|
| No valid status | `status` missing, or not one of `PLANNING`, `IN_PROGRESS`, `REVIEW`, `DONE` (case-insensitive, as the digest reads it) | add frontmatter `status:`, or harvest / move to `completed_tasks/` |
| Stale REVIEW | `status: REVIEW` and `updated_at` more than `STALE_REVIEW_DAYS = 14` days before today; a missing or unparseable `updated_at` counts as stale | run `/spine-harvest`, or set `status: IN_PROGRESS` if work resumed |
| DONE left behind | `status: DONE` in `active_tasks/` | `git mv` to `completed_tasks/` |

Healthy banks print one OK line for `docs/memory/active_tasks/` with the open-task count. Warnings keep exit 0. PLANNING and IN_PROGRESS tasks are never flagged, whatever their age. The check never edits files: closing a task stays a human decision.

Where the validator runs (LEARN-002): only `/spine-harvest` step 4c.1 (`commands/spine-harvest.md`). That step gets one sentence: a stale-REVIEW warning for the task being harvested clears at step 5; every other open-task warning is a follow-up for the human.

Out of scope: closing Spine's own 7 legacy tasks (human decision after this ships), showing warnings in the digest, flagging old PLANNING or IN_PROGRESS tasks, I36 (narrative budget).

## Inputs

- `scripts/spine_cli/memory.py` — `open_tasks`, `read_frontmatter`, `collect_files`/`TASK` kind, `check_ledger`/`LedgerCheck`/`_file_list` pattern, `CLOSED_STATUS`, `UNKNOWN_STATUS`
- `scripts/spine_validate.py` — `validate_memory`
- `tests/unit/test_memory_budgets.py` — `_write`, `sv` loader, `validate_memory` CLI tests
- `commands/spine-harvest.md` step 4c.1; `rules/02-memory-bank.md` § Memory budgets; `README.md` and `AGENTS.md` § Memory budgets
- `docs/memory/ledger/learnings/LEARN-002-new-validator-check-reorders-command-steps.md`

## Expected Outputs

- `scripts/spine_cli/memory.py` — `STALE_REVIEW_DAYS`, `OPEN_TASKS_SCOPE`, `OpenTasksCheck` dataclass, `check_open_tasks(root, today)`
- `scripts/spine_validate.py` — `validate_memory` reports the open-task check (`today = date.today()`)
- `tests/unit/test_memory_open_tasks.py` — new tests
- `commands/spine-harvest.md`, `rules/02-memory-bank.md`, `README.md`, `AGENTS.md` — document the three warnings

## Acceptance Criteria (verifiable, TDD-ready)

- [x] AC1: Open tasks with a missing or non-standard status are reported in one warning naming the files; PLANNING, IN_PROGRESS and lowercase standard values are not.
  - Test: `test_open_tasks_without_valid_status_are_flagged` (no frontmatter, no `status:`, `status: BLOCKED`); `test_standard_statuses_are_not_flagged` (`planning` lowercase, IN_PROGRESS dated a year ago).
- [x] AC2: REVIEW tasks with `updated_at` more than 14 days before today are flagged; exactly 14 days is not; a REVIEW task without a parseable `updated_at` is flagged.
  - Test: `test_review_older_than_threshold_is_flagged`, `test_review_at_threshold_is_not_flagged`, `test_review_without_updated_at_is_flagged` (explicit `today`).
- [x] AC3: DONE tasks in `active_tasks/` are reported in one warning that names `completed_tasks/` as the destination.
  - Test: `test_done_tasks_left_in_active_tasks_are_flagged`.
- [x] AC4: `spine_validate.py memory` prints the open-task warnings on stderr with exit 0, lists at most 5 files plus `(+N more)`, ignores `_task-template.md`, and prints an OK line with the open-task count when healthy; a bank without `active_tasks/` gets no open-task line.
  - Test: `test_validate_memory_warns_on_stale_open_tasks_exit_0`, `test_open_task_warning_caps_file_list`, `test_validate_memory_open_tasks_ok_line`, `test_task_template_is_not_checked`, `test_no_active_tasks_dir_skips_check`.
- [x] AC5: Harvest step 4c.1 says a stale-REVIEW warning for the task being harvested clears at step 5; rule 02, README and AGENTS.md list the three open-task warnings.
  - Test: `test_harvest_explains_own_task_review_warning` (grep `commands/spine-harvest.md`); `test_docs_list_open_task_warnings` parametrized over the three docs (each names `14 days` and `completed_tasks/`).

## Test Strategy

- Positive: each of the three problem kinds flagged with file names; OK line on a healthy bank.
- Negative: PLANNING/IN_PROGRESS never flagged regardless of age; REVIEW at exactly 14 days not flagged; template ignored; no `active_tasks/` → no line; exit code stays 0.
- Regression: `tests/unit/test_memory_budgets.py` (existing `validate_memory` output and warning counts), then `pytest tests/`.
- Smoke: `python3 scripts/spine_validate.py memory` on Spine's own bank (expect one warning naming 7 tasks without status, 5 shown + `(+2 more)`) and on two local consumer banks (read-only).
- Command: `pytest -v tests/unit/test_memory_open_tasks.py tests/unit/test_memory_budgets.py && pytest tests/`

## Implementation Plan

### Task 1: Check function (tests first)

**Files:**
- Create: `tests/unit/test_memory_open_tasks.py`
- Modify: `scripts/spine_cli/memory.py` (new block after `check_ledger`)

**Step 1:** Write AC1–AC3 tests against `memory.check_open_tasks(root, today=date(2026, 11, 16))`, with a local `_task(name, frontmatter)` writer.

**Step 2:** Run `pytest -v tests/unit/test_memory_open_tasks.py` — expect FAIL (`check_open_tasks` missing).

**Step 3:** Implement in `memory.py`:
- Constants: `STALE_REVIEW_DAYS = 14`, `TASK_STATUSES = frozenset({"PLANNING", "IN_PROGRESS", "REVIEW", CLOSED_STATUS})`, `OPEN_TASKS_SCOPE = f"{MEMORY_DIR.as_posix()}/active_tasks/"` (`memory.py` has no active-tasks dir constant; `SCANNED_DIRS` holds the literal).
- `OpenTasksCheck(scope, tasks, problems)` frozen dataclass, `tasks` = count of non-DONE task files.
- `check_open_tasks(root: Path, today: date) -> OpenTasksCheck | None` — `None` when `active_tasks/` does not exist; reads task files via `collect_files` (kind `TASK`), one problem message per kind, file names through a list helper that caps at `PROBLEM_FILES_SHOWN` (generalize `_file_list` to take names only if it stays a one-line change; otherwise add a sibling helper).

**Step 4:** Run the test file — expect PASS.

### Task 2: Validator output

**Files:**
- Modify: `scripts/spine_validate.py` (`validate_memory`), `tests/unit/test_memory_open_tasks.py`

**Step 1:** Write AC4 tests through `sv.main(["memory"])` (load the validator like `test_memory_budgets.py`; dates relative to `date.today()`).

**Step 2:** Run — expect FAIL.

**Step 3:** In `validate_memory`, after the ledger loop: `check = check_open_tasks(root, date.today())`; warn per problem as `f"{check.scope}: {problem}"`, else `report.ok(check.scope, f"{check.tasks} open task(s), no stale tasks")`. Update the docstring.

**Step 4:** Run both test files — expect PASS (existing warning counts in `test_memory_budgets.py` unchanged: their banks have no `active_tasks/`).

### Task 3: Docs and full run

**Files:**
- Modify: `commands/spine-harvest.md` (step 4c.1), `rules/02-memory-bank.md` (§ Memory budgets), `README.md`, `AGENTS.md` (§ Memory budgets); `tests/unit/test_memory_open_tasks.py`

**Step 1:** Write the two AC5 doc tests — expect FAIL.

**Step 2:** Harvest 4c.1: in the "Every other warning" bullet, name the three open-task warnings and add that a stale-REVIEW warning for the task being harvested clears at step 5. Rule 02: one paragraph after the budget table. README / AGENTS.md: one sentence each in § Memory budgets.

**Step 3:** `pytest tests/`; smoke-run the validator on Spine and two consumer banks.

## Execution notes
- 2026-11-16 — decision — Generalized the ledger file-list helper as `_name_list(names)`; `_file_list(entries)` now delegates to it in one line, so ledger and open-task warnings share the 5-file cap and `(+N more)` format. → no promotion
- 2026-11-16 — decision — Harvest 4c.1 tells the agent not to report a stale-REVIEW warning naming the task being harvested (it clears at step 5). A DONE warning cannot fire for that task: step 5 sets `status: DONE` and moves the file together. → no promotion
- 2026-11-16 — out-of-scope — `commands/spine-harvest.md` step 7 asks for each remaining warning as "(scope, chars, limit, suggested owner)"; open-task and ledger warnings have no chars/limit. Harmless; reword if summaries get confusing. → suggested task
- 2026-11-16 — environment — Only 9 of the 11 surveyed consumer banks are reachable through a `.spine` symlink under the workspace; smoke covered those 9. → no promotion

## Execution evidence
**Tests executed:**
- `pytest -v tests/unit/test_memory_open_tasks.py tests/unit/test_memory_budgets.py`
- `pytest tests/`

**Test results:** 35 passed (15 new open-task tests + 20 budget tests, warning counts unchanged); full suite 342 passed.

**Manual / external evidence:** Claude (agent), 2026-11-16, branch `feature/validator-stale-open-tasks` (uncommitted working tree), `python3 scripts/spine_validate.py memory`:
- Spine's own bank: one warning, `7 tasks without a valid status:`, 5 names shown + `(+2 more)`; exit 0.
- 9 local consumer banks via `--project-root` (read-only): all three warning kinds observed (no-status 2 banks, stale REVIEW 5 banks, DONE left behind 3 banks); one healthy bank printed `OK (1 open task(s), no stale tasks)`. Raw output not stored (re-run the command to reproduce).

## Delivery summary

- **Delivered:** `spine_validate.py memory` warns on open tasks without a valid status, REVIEW tasks idle over 14 days and DONE tasks left in `active_tasks/`; harvest 4c.1, rule 02, README and AGENTS.md document it. Delivery entry: `ledger/deliveries/2026-11-16-024-validator-stale-open-tasks.md`.
- **Evidence:** `pytest tests/` 342 passed (15 new tests) at execution and at harvest; smoke runs on Spine's bank and 9 local consumer banks (see Execution evidence).
- **Execution notes routing:** both `decision` notes → no promotion (easy to reverse, no real trade-off); `out-of-scope` → suggested task in `progress.md` Current state candidates; `environment` → no promotion (not a risk).
- **Learning:** no incident or rework. LEARN-002 was applied at planning (harvest step reads the validator after this check exists): no recurrence. Regression test: `test_harvest_explains_own_task_review_warning`.
- **Roadmap:** I35 Done.
