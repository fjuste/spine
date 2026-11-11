---
description: "Core protocol for solo-lean operation: focus on delivery, testing, and memory."
globs: 
alwaysApply: true
---

# CORE PROTOCOL (Solo Lean)

## 1. Mandatory minimum flow
1. **Sync & clarify:** Follow `02-memory-bank.md` — tiered SYNC; when `graphify-out/graph.json` exists, follow the **Graphify Discovery Protocol** (`GRAPH_REPORT.md` → `graphify query` → targeted file reads), then post-SYNC assumptions, ambiguities, and simplest approach.
2. **Plan:** create/update `docs/memory/active_tasks/<sequential-number>-<descriptive-name>.md` matching `_task-template.md` (Obsidian frontmatter + body sections; optional `## Implementation Plan` for bite-sized steps). Do not create the branch during planning.
3. **Branch:** at execution time, create or switch to `branch` from task frontmatter, based on `base`.
4. **Test (TDD):**
   a. Write a failing test for the first acceptance criterion.
   b. Implement the minimum code to make it pass.
   c. Refactor if needed while keeping tests green.
   d. Repeat for each acceptance criterion.
5. **Execute:** implement atomically and validate all tests pass.
6. **Harvest:** append delivery log in `progress.md`; update `learnings.md` when applicable; update `decision-log.md` and `domain-glossary.md` when applicable; move task to `completed_tasks/` via `git mv`.

## 2. Definition of Done
- [ ] Isolated branch created from `develop`
- [ ] `docs/memory/active_tasks/<sequential-number>-<descriptive-name>.md` with frontmatter, scope, and acceptance criteria
- [ ] Tests executed and passing
- [ ] Task `## Execution notes` (or `No deviations from plan.`) and `## Execution evidence` filled before `REVIEW`
- [ ] `docs/memory/ledger/progress.md` updated (Current state + delivery log entry)
- [ ] `docs/memory/ledger/learnings.md` updated (if incident, root cause, or rework recorded)
- [ ] Task file in `docs/memory/completed_tasks/` with `status: DONE`
- [ ] `docs/memory/global/decision-log.md` updated (if there was an architectural decision)
- [ ] `docs/memory/global/domain-glossary.md` updated (if canonical domain terms were promoted during discovery)

## 3. Guard rails
- When the user types `/graphify`, invoke the graphify skill before other work (rebuild, query, or explain per skill).
- Never use `git push --force`.
- Never assume an ambiguous requirement without confirmation. Surface assumptions and tradeoffs first.
- No silent decisions: architectural decisions require a recorded "why".
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If an implementation exceeds 3x the minimum viable lines, justify why.

## 4. Commits
Prefer Conventional Commits:
- `feat:`
- `fix:`
- `refactor:`
- `test:`
- `docs:`
- `chore:`
