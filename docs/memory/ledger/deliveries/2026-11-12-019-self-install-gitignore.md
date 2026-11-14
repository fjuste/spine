---
id: 2026-11-12-019-self-install-gitignore
date: 2026-11-12
title: Self-install keeps IDE trees ignored in the Spine repository
summary: Self-install keeps IDE trees ignored in the Spine repository
tags:
  - type/bug
  - area/infra
  - stack/python
task: 019-self-install-gitignore
---

**Task:** 019-self-install-gitignore | **Branch:** feature/self-install-gitignore
**Tags:** type/bug, area/infra, stack/python
**Description:** `spine.py install`/`update` detect a self-install (project root is the Spine clone, `same_path(project, spine)`) and keep `.spine`, `.agents/`, `.cursor/`, `.claude/` and `.opencode/` ignored instead of removing the IDE-tree ignores consumer installs drop (`SELF_INSTALL_GITIGNORE_KEEP`, `adjust_install_gitignore(..., self_install=)`). `AGENTS.md` § 6 documents the self-install (`install --core --project-root=.`, working-tree caveat). Before the task, commit `1b85e7e` untracked the committed absolute `.spine` symlink. Evidence: `pytest -q tests/` 229 passed (7 new in `test_spine_cli.py`). Manual runs by the agent on 2026-11-12 at `ab0c327`: dry run with 0 ignore removals and 0 conflicts; real `install --core` exit 0, 0 conflicts, 0 warnings, `.gitignore` unchanged, no new untracked trees (raw output in the session scratchpad, temporary). Graphify and MkDocs not active.
