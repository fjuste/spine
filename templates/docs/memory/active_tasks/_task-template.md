---
task_id: 000
title: Task title (human-readable)
goal: One-line outcome the task must achieve
status: PLANNING
tags:
  - type/feature
branch: feature/descriptive-name
base: develop
execution_skill: executing-plans
roadmap_idea:  # required when task originates from an Idea Bank ID (e.g., I3); otherwise leave empty
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
completed_at:
related_learnings: []
---

# 000-descriptive-name

> Reference template only — not a numbered task. Copy structure when creating tasks via `/spine-plan`.
> Only `_task-template.md` belongs under `templates/docs/memory/active_tasks/` (plus `.gitkeep` in seed).
> Do not use inline `**Status:**`, `**Branch:**`, or `superpowers:*` headers — metadata lives in frontmatter only.

## Discovery notes

(When `@grill-me` ran: resolved decisions, MVP, out-of-scope, glossary/decision-log promotions.)

## Objective

(Expanded goal — may elaborate frontmatter `goal`.)

## Inputs

- [Input files/data]

## Expected Outputs

- [Files/artifacts that must be generated]

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] [Criterion 1]
  - Test: [specific test that proves this criterion]
- [ ] [Criterion 2]
  - Test: [specific test that proves this criterion]

## Test Strategy

- Positive:
- Negative:
- Regression:
- Command: `pytest ...`

## Implementation Plan

(Optional — use when the task needs bite-sized execution steps. Omit for small tasks with ≤3 acceptance criteria.)

### Task 1: [Component name]

**Files:**
- Create: `path/to/file`
- Modify: `path/to/existing:line-range`
- Test: `tests/path/to/test.py`

**Step 1:** [One action — write failing test, run command, etc.]

**Step 2:** [Next action]

**Step 3:** Commit with semantic message.

## Execution notes

(Written by `/spine-execute` at the moment each fact happens — not in a batch at the end. Append-only: add new entries, never rewrite or delete earlier ones. `/spine-harvest` reads this section as its primary source, possibly in a new session, and appends the destination to each entry, e.g. `→ LEARN-023`, `→ decision-log 2026-11-11`, `→ no promotion`.)

Entry format: `- YYYY-MM-DD — <type> — <what happened>`. Types:

- `deviation` — what changed relative to the plan and why. If the change contradicts the plan, record it and stop for the human before continuing.
- `incident` — symptom, root cause, fix.
- `rework` — what was redone and why.
- `decision` — choice made during execution and its reason (decision-log candidate).
- `out-of-scope` — improvement found and not done.
- `environment` — fact discovered about infrastructure or an external service.
- `resume` — resume point when execution stops midway (see below). Temporary state; harvest does not promote it.

If execution stops midway (blocker, end of session), append a `resume` entry with the resume point: last completed step, next step, open blocker. Record the blocker itself as a separate `incident` or `environment` entry when it is worth learning from.

When nothing deviated, keep a single line: `No deviations from plan.`

## Execution evidence

(Written by `/spine-execute` before `status: REVIEW`. Never paste secrets, tokens, keys, or credentials — redact them and point to where the raw output is stored.)

**Tests executed:**

- `[command]`

**Test results:**

- [passed/failed counts, notable failures and how they were resolved]

**Manual / external evidence:** (one entry per run; omit when none)

- Who ran it: [person or agent] | When: YYYY-MM-DD | Commit/branch: [sha or branch]
  - Command: `[command or procedure]`
  - Summary: [observed result]
  - Raw output: [path, CI link, or ticket — not pasted inline]
