---
id: 2026-11-14-020-memory-budgets
date: 2026-11-14
title: Memory budgets — digest-first limits in the validator and Current state compaction at harvest
summary: Memory budgets — digest-first limits in the validator and Current state compaction at harvest
tags:
  - type/feature
  - area/memory
  - stack/python
task: 020-memory-budgets
---

**Task:** 020-memory-budgets | **Branch:** feature/memory-budgets
**Tags:** type/feature, area/memory, stack/python
**Description:** New `spine_validate.py memory` (`--project-root`, `--dry-run`) measures `docs/memory/` against named constants in `spine_cli/memory.py` (`check_budgets`, `BudgetCheck`): digest ≤ 8,000, Current state ≤ 1,500, narrative body ≤ 3,000, `decision-log.md` ≤ 5,000, `progress.md`/`learnings.md` ≤ 6,000. Over-budget scopes are `WARNING:` lines with a remedy hint (exit 0); the digest warning lists its sections largest first; a missing `docs/memory/` is the only error. The digest output is unchanged. `/spine-harvest` gains step 4a.1 (compact Current state, list other warnings as follow-ups, no `global/` edit without a human-approved diff); `02-memory-bank.md` § Memory budgets, README and AGENTS.md document it. Evidence: `pytest tests/` 248 passed (19 new in `test_memory_budgets.py`). Manual read-only runs by the agent on 2026-11-13 at `e4abadb`: onboarding-hub 10 warnings (digest 13,553, Current state 5,434), agenthub 9 (digest 10,522, Current state 6,563), intelligence-engine 10 (digest and Current state within budget), Spine 1 (`progress.md` 9,370); `git status docs/memory` unchanged in each; per-project table in the task's Execution evidence. Graphify and MkDocs not active.
