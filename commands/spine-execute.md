---
description: Execute the active task with implementation, validation, and status updates in the memory-bank
agent: build
---

# Slash Command: /spine-execute <plan_file_path>
Act as a Software Engineer focused on rigorous implementation.

1. **Active Task Selection:** Use the provided `<plan_file_path>` argument.
   - Validate if the file exists and has a `.md` extension.
   - File must be under `docs/memory/active_tasks/` (open tasks only; completed tasks live in `completed_tasks/`).
2. **Branch Setup:** Read `branch` and `base` from task YAML frontmatter (fallback: legacy `## Branch:` / `## Base:` if present).
   - **GitFlow is mandatory (not optional) during execution.**
   - `base` must be `develop` and `branch` must follow `feature/<descriptive-name>`.
   - If `branch` or `base` are missing, stop and request a plan correction before implementation.
   - If `base` is not `develop` or `branch` does not match `feature/<descriptive-name>`, stop and request correction to comply with GitFlow.
   - **Sync base before any feature work (multi-dev / shared repo):**
     1. `git fetch origin`
     2. `git checkout develop`
     3. `git pull --ff-only origin develop`
        - If `--ff-only` fails (local `develop` diverged), **STOP** and ask the user to reconcile before continuing.
        - If checkout/pull is blocked by a dirty working tree, **STOP** and ask to commit or stash first.
   - If the specified `branch` does not exist yet: `git checkout -b <branch>` (from the updated `develop`).
   - If the `branch` already exists:
     1. `git checkout <branch>`
     2. Integrate latest `develop`: `git merge origin/develop` (or rebase onto `origin/develop` if the user prefers rebase).
     3. If merge/rebase conflicts, **STOP** and ask the user to resolve before implementation.
3. **Context Reading:** Read the selected active task mandatorily:
   - YAML frontmatter (`goal`, `tags`, `execution_skill`, …)
   - `## Acceptance Criteria`, `## Test Strategy`
   - `## Implementation Plan` when present — use Task/Step blocks as the execution checklist (batch via `@executing-plans`)
   - If Implementation Plan is **missing** and there are **>3** acceptance criteria, stop and ask to extend the plan or proceed criterion-by-criterion
   - `## Execution notes` and `## Execution evidence` when present — when resuming, continue from the latest `resume` entry recorded there
   - Legacy task without these sections: add both headings (empty) after `## Implementation Plan` (or after `## Test Strategy`) before starting
4. **Execution Skill Selection:**
   - Use the skill specified in frontmatter `execution_skill` (fallback: legacy `Suggested execution skill` field).
   - If no skill is specified, default to `@executing-plans`.
   - Respect `docs/governance/skills-policy.md` to validate allowlist/trial and per-project skill limits.
   - For UI/E2E with Playwright, follow the decision defined in the active task:
     - keep `playwright-cli` for short/interactive tasks;
     - use `playwright-skill` only for multi-step flows, multiple validations, and re-runnable scripts.
   - Do not switch from `playwright-cli` to `playwright-skill` (or vice versa) without recording an objective justification in the active task.
5. **Code discovery (when locating implementation targets):** If `graphify-out/graph.json` exists and the target file/module is unclear, follow the **Graphify Discovery Protocol** in `02-memory-bank.md` before broad Glob/grep scans.
6. **Atomic Implementation:** Implement the required code by following `docs/memory/global/system-patterns.md` and the active task guidelines.
6.5. **Execution Notes (continuous):** Append to `## Execution notes` in the task file when it happens — right after the fact, not in a batch at the end of execution. Entries are dated (`- YYYY-MM-DD — <type> — …`) and append-only: never rewrite or delete earlier entries.
   - `deviation` — what changed relative to the plan and why. If the change **contradicts** the plan (acceptance criteria, scope, or approach), record it and **STOP** for the human before continuing.
   - `incident` — symptom, root cause, fix.
   - `rework` — what was redone and why.
   - `decision` — choice made during execution and its reason (candidate for a `ledger/decisions/` entry; harvest decides).
   - `out-of-scope` — improvement found and not done (see step 9).
   - `environment` — fact discovered about infrastructure or an external service.
   - `resume` — resume point; see next bullet.
   - If execution stops midway (blocker, end of session, user interruption), append a `resume` entry with the resume point: last completed step, next step, open blocker. Record the blocker itself as a separate `incident` or `environment` entry when it is worth learning from. Keep `status: IN_PROGRESS`.
   - When execution finishes with nothing to record, the section holds a single line: `No deviations from plan.`
   - Never paste secrets, tokens, keys, or credentials in notes or evidence.
7. **Validation Cycle:**
   - Run the test command defined in the active task.
   - If it fails, analyze the error and fix the code (not the test, unless the test is logically wrong).
   - Repeat until all tests pass.
8. **Execution Status:** Update frontmatter at start and end:
   - At beginning: `status: IN_PROGRESS`, bump `updated_at`.
   - When complete: `status: REVIEW`, bump `updated_at`.
   - When marking `REVIEW`, fill `## Execution evidence`: **Tests executed** (commands) and **Test results** (summary). Add **Manual / external evidence** for any manual or external run: who ran it, when, commit/branch, command, short summary, and where the raw output lives (path or link — not pasted inline).
9. **Restriction:** Do not perform refactors outside the active task scope. If you find a necessary improvement, record it in `## Execution notes` as an `out-of-scope` entry (what, where, why it matters) and do not implement it.
10. **Completion Gate (mandatory):**
   - Before sending the final execution response, verify frontmatter `status` is `REVIEW`.
   - If status is not `REVIEW`, stop and update it before completion.
   - `REVIEW` is valid only if:
     - `## Execution notes` is filled — at least one dated entry, or the single line `No deviations from plan.`
     - `## Execution evidence` contains a `Tests executed` list and a `Test results` summary.
   - If notes or test evidence are missing, stop and update the active task file before completion.
