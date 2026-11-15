---
description: "Core protocol for solo-lean operation: focus on delivery, testing, and memory."
globs: 
alwaysApply: true
---

# CORE PROTOCOL (Solo Lean)

## 1. Mandatory minimum flow
1. **Sync & clarify:** Follow `02-memory-bank.md` — tiered SYNC, Core tier via `python3 .spine/scripts/spine.py memory digest` (do its `SETUP:` work when flagged; legacy file list only if the command fails); when `graphify-out/graph.json` exists, follow the **Graphify Discovery Protocol** (`GRAPH_REPORT.md` → `graphify query` → targeted file reads), then post-SYNC assumptions, ambiguities, and simplest approach.
2. **Plan:** create/update `docs/memory/active_tasks/<sequential-number>-<descriptive-name>.md` matching `_task-template.md` (Obsidian frontmatter + body sections; optional `## Implementation Plan` for bite-sized steps). Do not create the branch during planning.
3. **Branch:** at execution time, create or switch to `branch` from task frontmatter, based on `base`.
4. **Test (TDD):**
   a. Write a failing test for the first acceptance criterion.
   b. Implement the minimum code to make it pass.
   c. Refactor if needed while keeping tests green.
   d. Repeat for each acceptance criterion.
5. **Execute:** implement atomically and validate all tests pass.
6. **Harvest:** write the delivery entry in `ledger/deliveries/` and refresh `progress.md` Current state; add or update `ledger/learnings/` and `ledger/decisions/` entries and `domain-glossary.md` when applicable; run `spine.py memory index`; move task to `completed_tasks/` via `git mv`.

## 2. Definition of Done
- [ ] Isolated branch created from `develop`
- [ ] `docs/memory/active_tasks/<sequential-number>-<descriptive-name>.md` with frontmatter, scope, and acceptance criteria
- [ ] Tests executed and passing
- [ ] Task `## Execution notes` (or `No deviations from plan.`) and `## Execution evidence` filled before `REVIEW`
- [ ] `docs/memory/ledger/progress.md` Current state updated and a delivery entry in `docs/memory/ledger/deliveries/`
- [ ] Entry in `docs/memory/ledger/learnings/` added or updated (if incident, root cause, or rework recorded)
- [ ] Task file in `docs/memory/completed_tasks/` with `status: DONE`
- [ ] Entry in `docs/memory/ledger/decisions/` added (if there was an architectural decision)
- [ ] Ledger `INDEX.md` files regenerated (`python3 .spine/scripts/spine.py memory index`)
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
