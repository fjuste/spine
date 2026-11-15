---
task_id: 016
title: Sync opencode template tests with current schema
goal: Update test_opencode_template.py assertions to match templates/opencode.json current schema (model, compaction, agents), making all 5 tests pass
status: DONE
tags:
  - type/bug
  - area/testing
  - area/config
branch: feature/opencode-template-test-sync
base: develop
execution_skill: executing-plans
created_at: 2026-07-08
updated_at: 2026-07-08
completed_at: 2026-07-08
related_learnings: []
---

# 016-opencode-template-test-sync

## Discovery notes

Investigated in task 015 final validation. The 5 failures are pre-existing on `develop` (confirmed via `git checkout develop && pytest`). Root cause: `templates/opencode.json` was updated to a newer OpenCode schema, but `tests/unit/test_opencode_template.py` was not synchronized. Direction: update tests to match the template — the template is the deployable source of truth for consumer projects.

## Objective

Align `tests/unit/test_opencode_template.py` with the current `templates/opencode.json` schema. The template was intentionally updated (e.g., `compaction.auto` instead of `compaction.enabled`, `qwen3.7-max` instead of `deepseek-v4-pro`, no explicit `agent.build`/`agent.plan`). The tests still assert the old schema. Fix the tests, not the template.

## Inputs

- `templates/opencode.json` (current schema — source of truth)
- `tests/unit/test_opencode_template.py` (5 stale assertions)

## Expected Outputs

- `tests/unit/test_opencode_template.py` — 5 failing tests updated to match current template schema, all passing

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] `test_opencode_template_has_model_and_default_agent` passes with assertions matching current template schema
  - Test: `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_model_and_default_agent -v` exits 0

- [ ] `test_opencode_template_registers_ask_agent` passes with `qwen3.7-max` model and no stale `variant` check
  - Test: `pytest tests/unit/test_opencode_template.py::test_opencode_template_registers_ask_agent -v` exits 0

- [ ] `test_opencode_template_build_agent_configured` removed or rewritten to reflect template reality (no `agent.build`)
  - Test: test either removed or rewritten; if kept, matches current template

- [ ] `test_opencode_template_plan_agent_medium_variant` removed or rewritten to reflect template reality (no `agent.plan`)
  - Test: test either removed or rewritten; if kept, matches current template

- [ ] `test_opencode_template_has_spine_instructions_and_compaction` passes with `compaction.auto` instead of `compaction.enabled`
  - Test: `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_spine_instructions_and_compaction -v` exits 0

- [ ] Full test_opencode_template.py suite passes: `pytest tests/unit/test_opencode_template.py -v` exits 0
  - Test: `pytest tests/unit/test_opencode_template.py -v`

## Test Strategy

- **Positive:** All 5 currently-failing tests pass after assertions are updated to match `templates/opencode.json` schema.
- **Negative:** No new test introduced that would break if the template evolves again (tests should remain schema-validating, not value-rigid).
- **Regression:** `pytest tests/ -v` — all other test files (86 passing) remain green.
- **Command:** `pytest tests/unit/test_opencode_template.py -v`

## Implementation Plan

### Task 1: Update `test_opencode_template_has_model_and_default_agent`

**Files:**
- Modify: `tests/unit/test_opencode_template.py:11-18`

**Step 1:** Template has no top-level `model`/`small_model`. Assert they are absent or test the `permission` block that does exist. Replace:
- Remove `assert cfg["model"]` (line 14), `assert cfg["model"] == ...` (line 16), `assert cfg["small_model"]` (line 17), `assert cfg["small_model"] == ...` (line 18)
- Add `assert cfg["permission"]` and verify key permissions exist
- Keep `assert cfg["$schema"]` and `assert cfg["default_agent"] == "ask"`

**Step 2:** Run `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_model_and_default_agent -v` — expect PASS.

**Step 3:** Commit with: `test: sync model/default_agent template test with current schema`

### Task 2: Update `test_opencode_template_registers_ask_agent`

**Files:**
- Modify: `tests/unit/test_opencode_template.py:21-29`

**Step 1:** Fix assertions to match current `agent.ask`:
- `ask["model"]` → `"opencode-go/qwen3.7-max"` (not `deepseek-v4-pro`)
- `assert "variant" not in ask` → remove (template has `temperature` and `description` now, but `variant` being absent is incidental — better to assert what IS present instead of what ISN'T)
- Add `assert ask["temperature"] == 0.3` and `assert ask["description"]`
- Keep `mode`, `prompt`, `permission.edit`, `permission.bash` assertions

**Step 2:** Run `pytest tests/unit/test_opencode_template.py::test_opencode_template_registers_ask_agent -v` — expect PASS.

**Step 3:** Commit with: `test: sync ask agent template test with qwen model`

### Task 3: Handle `agent.build` and `agent.plan` tests

**Files:**
- Modify: `tests/unit/test_opencode_template.py:32-44`

**Step 1:** Template has no `agent.build` or `agent.plan`. These agents are configured at the OpenCode IDE level, not in the template. Two options:
- **Remove** both tests entirely (cleanest — they test nothing that exists)
- **Rewrite** to assert `agent` only contains `ask`

Choose removal — the tests assert a contract that no longer exists. No replacement value is possible.

**Step 2:** Run `pytest tests/unit/test_opencode_template.py -v` — expect 3 tests collected (not 5), all passing.

**Step 3:** Commit with: `test: remove stale build/plan agent template tests`

### Task 4: Update `test_opencode_template_has_spine_instructions_and_compaction`

**Files:**
- Modify: `tests/unit/test_opencode_template.py:47-51`

**Step 1:** Fix compaction assertion. Current schema uses `auto` not `enabled`:
- Replace `assert cfg["compaction"]["enabled"] is True` with `assert cfg["compaction"]["auto"] is True`
- Optionally add `assert cfg["compaction"]["prune"] is False` and `assert cfg["compaction"]["tail_turns"] == 4`
- Keep `instructions` assertions as-is

**Step 2:** Run `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_spine_instructions_and_compaction -v` — expect PASS.

**Step 3:** Commit with: `test: sync compaction template test with auto/prune schema`

### Task 5: Final validation

**Files:**
- Test: `tests/unit/test_opencode_template.py`
- Test: `tests/` (full suite)

**Step 1:** Run `pytest tests/unit/test_opencode_template.py -v` — expect all collected tests pass.

**Step 2:** Run `pytest tests/ -v` — expect 91 passed (or 89 if build/plan removed), 0 failed.

**Step 3:** Commit with: `test: verify all opencode template tests pass after schema sync`

## REVIEW checklist

- **Tests executed:**
  - `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_model_and_default_agent -v` — PASSED
  - `pytest tests/unit/test_opencode_template.py::test_opencode_template_registers_ask_agent -v` — PASSED
  - `pytest tests/unit/test_opencode_template.py::test_opencode_template_has_spine_instructions_and_compaction -v` — PASSED
  - `pytest tests/unit/test_opencode_template.py -v` — 3 PASSED, 0 FAILED
  - `pytest tests/ -v` — 89 PASSED, 0 FAILED
- **Test results:** All tests pass. 2 removed (build/plan agent no longer in template), 3 updated to match current `templates/opencode.json` schema. Full regression suite green.

## Delivery summary

**Date:** 2026-07-08
**Branch:** feature/opencode-template-test-sync

**What changed:**
- `tests/unit/test_opencode_template.py` — 5 stale assertions fixed to match current `templates/opencode.json` schema.
- `test_opencode_template_has_model_and_default_agent`: removed stale `model`/`small_model` assertions, added `permission` block check.
- `test_opencode_template_registers_ask_agent`: updated model assertion to `qwen3.7-max`, added `temperature`/`description` checks.
- `test_opencode_template_build_agent_configured` and `test_opencode_template_plan_agent_medium_variant`: removed (agents no longer in template — configured at IDE level).
- `test_opencode_template_has_spine_instructions_and_compaction`: replaced `compaction.enabled` with `compaction.auto`, added `prune`/`tail_turns` checks.

**Validation:** `pytest tests/` — 89 passed, 0 failed.
**Graphify:** Not active — skipped.
**MkDocs:** Not active — skipped. No public API or architecture changes.
