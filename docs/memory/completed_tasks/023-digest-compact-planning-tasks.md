---
task_id: 023
title: Digest open tasks — full lines for active work, compact lines for PLANNING
goal: The digest keeps `NNN | STATUS | title — goal` only for IN_PROGRESS and REVIEW tasks and lists PLANNING tasks as `NNN title`, so a bank with many planned tasks no longer spends most of its Open tasks section on goals nobody is working on
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/digest-compact-planning-tasks
base: develop
execution_skill: executing-plans
roadmap_idea: I34
created_at: 2026-11-15
updated_at: 2026-11-16
completed_at: 2026-11-16
related_learnings: []
---

# 023-digest-compact-planning-tasks

## Objective

`spine.py memory digest` prints one line per open task as `NNN | STATUS | title — goal` (capped at `TASK_LINE_MAX_CHARS = 320`). On a consumer bank with 18 PLANNING tasks those lines take about 4.7k of a 13.7k digest, although a session only needs the goal of the task it works on, and the goal is one file open away.

Render by status (`TaskLine.render` / `open_tasks` in `scripts/spine_cli/memory.py`):

| Status | Line | Example |
|---|---|---|
| `IN_PROGRESS`, `REVIEW` | unchanged: `NNN \| STATUS \| title — goal` | `009 \| IN_PROGRESS \| Ninth — Do nine` |
| any other open status (`UNKNOWN` for files without frontmatter, non-standard values) | `NNN \| STATUS \| title` (status kept, goal dropped) | `005 \| UNKNOWN \| 005-legacy` |
| `PLANNING` | `NNN title` | `001 First` |

Order: IN_PROGRESS, REVIEW, other statuses, then PLANNING; each group by task id. When at least one PLANNING task exists, one label line `Planning (goal in the task file):` precedes the PLANNING group, so an agent knows what the bare lines are and where the goal lives. The 320-char cap still applies to every line.

Keeping the status on non-standard lines (rather than collapsing them to `NNN title`) keeps pre-v2.1 tasks visibly different from planned work; I35 will warn about them.

Out of scope: stale-task warnings (I35), narrative budget (I36), changing `DIGEST_BUDGET_CHARS`.

## Inputs

- `docs/memory/ledger/roadmap.md` — Idea Bank I34 and its Review Log sizing (4.7k → about 1.3k for 18 PLANNING lines)
- `scripts/spine_cli/memory.py` — `TaskLine`, `open_tasks`, `OPEN_STATUS_RANK`, `build_digest`
- `tests/unit/test_memory_digest.py` — `bank` fixture and open-task assertions
- `tests/unit/test_memory_budgets.py` — `_many_open_tasks` builds PLANNING tasks with 300-char goals to push the digest over budget
- `rules/02-memory-bank.md` § Core SYNC (digest line format), `README.md` and `AGENTS.md` § Memory digest

## Expected Outputs

- `scripts/spine_cli/memory.py` — status-dependent rendering, PLANNING ranked last, label line in `build_digest`
- `tests/unit/test_memory_digest.py` — updated expectations and new cases
- `tests/unit/test_memory_budgets.py` — `_many_open_tasks` writes `IN_PROGRESS` tasks so the digest overrun case still overruns
- `rules/02-memory-bank.md`, `README.md`, `AGENTS.md` — digest description names both line forms

## Acceptance Criteria (verifiable, TDD-ready)

- [x] AC1: IN_PROGRESS and REVIEW tasks keep `NNN | STATUS | title — goal`, and a REVIEW/IN_PROGRESS task without goal keeps `NNN | STATUS | title`.
  - Test: `test_digest_sections_order_and_one_line_per_task` (existing `009`/`007` lines unchanged); `test_digest_active_task_without_goal_has_no_dash`.
- [x] AC2: PLANNING tasks render as `NNN title` with no status and no goal; their goal text and body never appear in the digest.
  - Test: `test_digest_planning_tasks_render_id_and_title_only` — `001 First` and `003 Third` present, `Do one`/`Do three`/`| PLANNING |` absent.
- [x] AC3: Open tasks with any other status keep the status and drop the goal (`005 | UNKNOWN | 005-legacy`; a non-standard `status: BLOCKED` with a goal prints `NNN | BLOCKED | title`).
  - Test: existing `UNKNOWN` assertion; `test_digest_nonstandard_status_keeps_status_drops_goal`.
- [x] AC4: Order is IN_PROGRESS, REVIEW, other statuses, then PLANNING (each by id), and the label `Planning (goal in the task file):` sits directly before the first PLANNING line only when a PLANNING task exists.
  - Test: `test_digest_sections_order_and_one_line_per_task` (full section block); `test_digest_planning_label_absent_without_planning_tasks`.
- [x] AC5: A bank with 18 PLANNING tasks whose goals are 250 chars yields an Open tasks section under 1,500 chars (vs. about 4.7k before), and `DONE` tasks stay excluded.
  - Test: `test_digest_many_planning_tasks_stay_compact` (via `memory.digest_section_sizes`); existing `DONE` exclusion test.
- [x] AC6: The digest budget check still flags an overrun, and rule 02, README and AGENTS.md describe both line forms.
  - Test: `test_check_budgets_flags_each_scope_over_limit` with `_many_open_tasks` writing `IN_PROGRESS`; `grep -n "NNN title" rules/02-memory-bank.md README.md AGENTS.md` returns one hit per file.

## Test Strategy

- Positive: active lines unchanged; PLANNING compact; label present; non-standard statuses keep status.
- Negative: no PLANNING goal or `| PLANNING |` in the digest; no label without PLANNING tasks; DONE tasks absent.
- Regression: full `tests/unit/test_memory_digest.py` and `tests/unit/test_memory_budgets.py`; then `pytest tests/`. Run `python3 scripts/spine.py memory digest` on Spine's own bank (7 `UNKNOWN` tasks — output unchanged) as a smoke check.
- Command: `pytest -v tests/unit/test_memory_digest.py tests/unit/test_memory_budgets.py && pytest tests/`

## Implementation Plan

### Task 1: Tests first

**Files:** `tests/unit/test_memory_digest.py`, `tests/unit/test_memory_budgets.py`

- [x] Step 1: Update the expected Open tasks block in `test_digest_sections_order_and_one_line_per_task` to `009 | IN_PROGRESS | Ninth — Do nine`, `007 | REVIEW | Seventh — Do seven`, `Planning (goal in the task file):`, `001 First`, `003 Third`.
- [x] Step 2: Change the `004` no-goal assertion to a REVIEW task (`004 | REVIEW | No goal\n`) and add the AC2–AC5 tests listed above.
- [x] Step 3: Switch `_many_open_tasks` to `status: IN_PROGRESS`.
- [x] Step 4: Run `pytest -v tests/unit/test_memory_digest.py tests/unit/test_memory_budgets.py`; confirm the new assertions fail for the expected reason.

### Task 2: Rendering

**Files:** `scripts/spine_cli/memory.py`

- [x] Step 1: Add constants `FULL_LINE_STATUSES = frozenset({"IN_PROGRESS", "REVIEW"})`, `PLANNING_STATUS = "PLANNING"`, `PLANNING_STATUS_RANK = 3`, `PLANNING_LABEL = "Planning (goal in the task file):"`.
- [x] Step 2: `TaskLine.render` — full line for `FULL_LINE_STATUSES`, `NNN title` for PLANNING, `NNN | STATUS | title` otherwise; keep `_cap`. Update the docstring.
- [x] Step 3: `TaskLine.sort_key` — PLANNING ranks after other statuses.
- [x] Step 4: `build_digest` — insert `PLANNING_LABEL` before the first PLANNING line.
- [x] Step 5: Re-run the two test files until green.

### Task 3: Docs and full run

**Files:** `rules/02-memory-bank.md`, `README.md`, `AGENTS.md`

- [x] Step 1: Rule 02 Core SYNC paragraph: "one line per open task (`NNN | STATUS | title — goal` for IN_PROGRESS/REVIEW, `NNN title` under a Planning label for PLANNING)". Mirror the wording in README and AGENTS.md § Memory digest.
- [x] Step 2: `pytest tests/`; `python3 scripts/spine.py memory digest` smoke check.

## Execution notes
- 2026-11-15 — deviation — Added `test_digest_other_statuses_sit_between_review_and_planning` (a `BLOCKED` task between REVIEW and the Planning label), not listed in the plan; AC4's fixture has no non-standard status, so the "other statuses before PLANNING" order was otherwise untested. Additive only, no change to scope or approach. → no promotion
- 2026-11-15 — environment — Spine's own bank has no goals on its 7 `UNKNOWN` tasks, so its digest Open tasks section is byte-identical before and after this change (smoke check). → no promotion

## Execution evidence
**Tests executed:**
- `pytest -v tests/unit/test_memory_digest.py tests/unit/test_memory_budgets.py` (red first: 6 new/updated assertions failed on missing `PLANNING_LABEL` and goals still printed; then green)
- `pytest tests/`
- `grep -c "NNN title" rules/02-memory-bank.md README.md AGENTS.md`
- `python3 scripts/spine.py memory digest` (Spine's own bank), diffed against the pre-change `memory.py`

**Test results:**
- Targeted: 76 passed
- Full suite: 327 passed
- grep: 1 hit per file
- Smoke check: Open tasks section unchanged for the 7 `UNKNOWN` tasks; task 023 shows as a full IN_PROGRESS line

**Manual / external evidence:** 2026-11-15, branch `feature/digest-compact-planning-tasks` (uncommitted working tree). An ad-hoc script built 18 PLANNING tasks with 250-char goals and measured the Open tasks section with `memory.digest_section_sizes`: 5,278 chars before, 524 after. The script was a throwaway in the session scratchpad and was not kept.

## Delivery summary
Delivered 2026-11-16 → `ledger/deliveries/2026-11-16-023-digest-compact-planning-tasks.md`. Digest open-task lines depend on status: full for IN_PROGRESS/REVIEW, `NNN title` under a Planning label for PLANNING, status without goal otherwise. Evidence: `pytest tests/` 327 passed (execution and harvest). The agent's 2026-11-15 measurement with 18 PLANNING tasks: Open tasks section 5,278 → 524 chars (throwaway scratchpad script, not kept). Notes: deviation (extra ordering test) → no promotion; environment (Spine's UNKNOWN tasks have no goals) → no promotion, since I35 already covers stale tasks. No incidents or rework, so no learning entry. Roadmap I34 → Done.
