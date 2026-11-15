---
id: 2026-07-08-016-opencode-template-test-sync
date: 2026-07-08
title: Sync opencode template tests with current schema
summary: Sync opencode template tests with current schema
tags:
  - type/bug
  - area/testing
  - area/config
task: 016-opencode-template-test-sync
---

**Task:** 016-opencode-template-test-sync | **Branch:** feature/opencode-template-test-sync
**Tags:** type/bug, area/testing, area/config
**Description:** Fixed 5 stale assertions in `test_opencode_template.py` to match the current `templates/opencode.json` schema. Removed 2 tests for `agent.build`/`agent.plan` (no longer in template — IDE-level config). Updated model assertion to `qwen3.7-max`, compaction check to `auto`/`prune`/`tail_turns`. Full suite: 89 passed, 0 failed. Graphify and MkDocs not active.
