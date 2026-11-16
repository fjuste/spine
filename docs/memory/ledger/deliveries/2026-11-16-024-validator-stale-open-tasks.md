---
id: 2026-11-16-024-validator-stale-open-tasks
date: 2026-11-16
title: Memory validator warns on stale open tasks
summary: spine_validate.py memory names open tasks to close — no valid status, REVIEW idle over 14 days, DONE left in active_tasks/ — with exit 0.
tags:
  - type/feature
  - area/memory
  - stack/python
task: 024-validator-stale-open-tasks
---

**Branch:** feature/validator-stale-open-tasks

**Description:** `check_open_tasks(root, today)` in `scripts/spine_cli/memory.py` reads the frontmatter of `active_tasks/NNN-*.md` (template ignored) and reports one warning per problem kind, naming up to 5 files plus `(+N more)`: tasks without a valid `status:`, REVIEW tasks whose `updated_at` is more than 14 days old or missing, and DONE tasks never moved to `completed_tasks/`. PLANNING and IN_PROGRESS tasks are never flagged; nothing is edited. `spine_validate.py memory` prints the warnings (exit 0) or an OK line with the open-task count, and no line when `active_tasks/` is absent. Harvest step 4c.1 says a stale-REVIEW warning for the task being harvested clears at step 5 (LEARN-002 applied at planning); rule 02, README and AGENTS.md document the check. Evidence: 15 new tests in `tests/unit/test_memory_open_tasks.py` written first; `pytest tests/` 342 passed at execution and again at harvest. Smoke runs by the agent on 2026-11-16 (output not stored; re-run the command): Spine's bank shows one warning for its 7 legacy tasks without status; 9 local consumer banks showed all three warning kinds and one healthy OK line. Graphify and MkDocs not active. Roadmap I35 Done.
