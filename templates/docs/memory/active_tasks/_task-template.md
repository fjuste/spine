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
