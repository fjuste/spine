---
id: 2026-11-16-023-digest-compact-planning-tasks
date: 2026-11-16
title: Digest open tasks — full lines for active work, compact lines for PLANNING
summary: Digest keeps title — goal only for IN_PROGRESS/REVIEW; PLANNING tasks print as NNN title under a label; 18 planned tasks shrink from 5,278 to 524 chars.
tags:
  - type/feature
  - area/memory
  - stack/python
task: 023-digest-compact-planning-tasks
---

**Branch:** feature/digest-compact-planning-tasks

**Description:** `TaskLine.render` in `scripts/spine_cli/memory.py` now picks the line by status: IN_PROGRESS and REVIEW keep `NNN | STATUS | title — goal`; PLANNING prints `NNN title`, sorted last, after a single `Planning (goal in the task file):` label; any other open status (UNKNOWN, non-standard values) keeps the status and drops the goal. The 320-char line cap is unchanged. Rule 02, README and AGENTS.md describe both line forms. Evidence: tests written first (6 new or updated assertions failed, then passed); `pytest tests/` 327 passed at execution and again at harvest. A throwaway script run by the agent on 2026-11-15 (session scratchpad, not kept) measured the Open tasks section for 18 PLANNING tasks with 250-char goals: 5,278 chars before, 524 after. Spine's own digest is unchanged for its 7 UNKNOWN tasks. One added test beyond the plan covers the other-statuses-before-PLANNING order. Graphify and MkDocs not active. Roadmap I34 Done.
