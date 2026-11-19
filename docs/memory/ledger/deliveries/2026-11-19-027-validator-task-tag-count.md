---
id: 2026-11-19-027-validator-task-tag-count
date: 2026-11-19
title: Validator counts only tags as tags
summary: spine_validate.py task counts items of the tags field only; related_learnings and other list fields no longer trip the 5-tag limit.
why: Tasks that link learnings were blocked at git commit by the pre-commit hook; they now commit.
tags:
  - area/tooling
  - type/bug
task: 027-validator-task-tag-count
---

**Branch:** feature/validator-task-tag-count

**Description:** `validate_task` in `scripts/spine_validate.py` counted every indented `- ` line in the frontmatter as a tag, so a task with block-list `related_learnings` (or any other list field) failed the 1–5 tag bound, and the pre-commit hook from 026 blocked the commit. The count now uses `spine_cli.memory.read_frontmatter_list(content, "tags")`, which also accepts inline `tags: [a, b]` (previously counted as 0 and rejected). Evidence: 2 regression tests in `tests/unit/test_spine_validate.py` written first and seen failing (`test_task_other_list_fields_are_not_tags`, `test_task_inline_tags_count`); existing empty/6-tag bounds unchanged; `pytest tests/` 416 passed at execution and again at harvest. Graphify and MkDocs not active; no roadmap idea.
