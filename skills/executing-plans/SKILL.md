---
name: executing-plans
description: "Use when you have a written implementation plan to execute in a separate session with review checkpoints"
risk: unknown
source: community
date_added: "2026-02-27"
---

# Executing Plans

## Overview

Load a Memory Bank task file, review critically, execute in batches, validate tests, and leave the task in `REVIEW` for `/spine-harvest`.

**Core principle:** Batch execution with checkpoints; frontmatter is the source of truth for branch, status, and skill selection.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Command orchestrator:** Prefer `/spine-execute <plan_file_path>` in Spine consumer projects — it enforces GitFlow, frontmatter updates, and test evidence. This skill describes the execution pattern inside that command.

## Step 1: Load and review

1. Read `docs/memory/active_tasks/NNN-descriptive-name.md`.
2. Parse **YAML frontmatter first:** `branch`, `base`, `execution_skill`, `status`, `tags`, `goal`.
3. Read body sections: Objective, Acceptance Criteria, Test Strategy.
4. If `## Implementation Plan` exists, use Task/Step blocks as the execution checklist.
5. If Implementation Plan is **missing** and there are **>3** acceptance criteria, stop and ask to extend the plan or proceed criterion-by-criterion.
6. Review critically — raise blockers before coding.

**Legacy fallback:** If frontmatter is missing, read inline `## Branch:` / `Suggested execution skill` and request plan correction to `_task-template.md` format.

## Step 2: Branch setup (GitFlow)

Per [`commands/spine-execute.md`](../../commands/spine-execute.md):

- `base` must be `develop`
- `branch` must be `feature/<descriptive-name>`
- Checkout base, pull, create or switch to feature branch
- Do not proceed if branch policy is violated

## Step 3: Execute batch

**Default batch size:** first 3 tasks (from Implementation Plan) or first 3 acceptance criteria.

For each unit of work:

1. Mark progress (TodoWrite or task body checklist)
2. Follow steps exactly when Implementation Plan provides them
3. Run verifications from Test Strategy
4. Mark complete

## Step 4: Report checkpoint

When batch complete:

- Show what was implemented
- Show verification output
- Ask: "Ready for feedback?" before next batch

## Step 5: Complete development (stop before harvest)

After all work passes tests:

1. Update frontmatter: `status: REVIEW`, bump `updated_at`
2. Record in `## Execution evidence`: **Tests executed** and **Test results** (plus manual/external runs when any)
3. Confirm `## Execution notes` holds the dated entries written during execution, or the single line `No deviations from plan.`
4. Stop — do **not** merge, harvest, or move to `completed_tasks/`
5. User runs `/spine-harvest` for delivery log, learnings, and `git mv`

**Do not use** `superpowers:finishing-a-development-branch`. Spine owns closure via `/spine-harvest`.

## When to stop and ask for help

Record each deviation, incident, rework, decision, out-of-scope finding, or environment fact in `## Execution notes` when it happens (see `/spine-execute` step 6.5). Before stopping mid-task, append the resume point.

Stop immediately when:

- Blocker mid-batch (missing dependency, failing test, unclear instruction)
- Plan has critical gaps
- Branch/frontmatter does not match GitFlow policy

## When to Use

When frontmatter `execution_skill` is `executing-plans`, or when `/spine-execute` selects this skill for generic implementation workflows.
