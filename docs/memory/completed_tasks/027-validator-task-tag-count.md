---
task_id: 027
title: Validator counts only tags as tags
goal: spine_validate.py task counts the items of the tags field only, not every list item in the frontmatter
status: DONE
tags:
  - area/tooling
  - type/bug
branch: feature/validator-task-tag-count
base: develop
execution_skill: test-driven-development
roadmap_idea:
created_at: 2026-11-19
updated_at: 2026-11-19
completed_at: 2026-11-19
related_learnings: []
---

# 027-validator-task-tag-count

## Objective

`validate_task` counts every indented `- ` line in the frontmatter as a tag. A task with block-list `related_learnings` (or any other list field) reports too many tags, and the pre-commit hook blocks the commit. Count the `tags` field only, reusing `spine_cli.memory.read_frontmatter_list` (block, inline `[a, b]` and scalar forms).

## Inputs

- `scripts/spine_validate.py` (`validate_task`)
- `scripts/spine_cli/memory.py` (`read_frontmatter_list`)

## Expected Outputs

- `scripts/spine_validate.py` counts tags with `read_frontmatter_list`
- Regression tests in `tests/unit/test_spine_validate.py`

## Acceptance Criteria (verifiable, TDD-ready)

- [x] Block-list `related_learnings` items do not count as tags
  - Test: `test_task_other_list_fields_are_not_tags` — 5 tags + 2 related_learnings items → 0 errors
- [x] Inline tags `[a, b]` count as tags
  - Test: `test_task_inline_tags_count` — `tags: [type/bug, area/tooling]` → 0 errors
- [x] Existing bounds still hold (empty → error; 6 → error)
  - Test: `test_task_tag_count_bounds` unchanged and green

## Test Strategy

- Positive: inline tags, extra list fields
- Negative: empty and 6 tags still fail
- Regression: full suite
- Command: `pytest tests/`

## Execution notes
No deviations from plan.

## Execution evidence
**Tests executed:** `python3 -m pytest -q tests/unit/test_spine_validate.py -k tag` (red: 2 new tests failed before the fix), then `python3 -m pytest -q tests/`
**Test results:** 416 passed
**Manual / external evidence:** `python3 scripts/spine_validate.py task docs/memory/active_tasks/027-validator-task-tag-count.md` passes on branch `feature/validator-task-tag-count`

## Delivery summary
- Root cause: the tag count was a regex over the whole frontmatter (`^[ \t]+- `), so list items of any field counted as tags.
- Prevention: count through `read_frontmatter_list(content, "tags")`, the shared frontmatter parser, instead of an ad-hoc regex.
- Regression tests: `test_task_other_list_fields_are_not_tags`, `test_task_inline_tags_count`; `pytest tests/` 416 passed (execution and harvest).
- Execution notes: `No deviations from plan.`; nothing promoted. Delivery entry `ledger/deliveries/2026-11-19-027-validator-task-tag-count.md`.
