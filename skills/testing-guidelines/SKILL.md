---
name: testing-guidelines
description: "Testing patterns and quality guardrails — when to test, how to structure tests, merge gates"
risk: low
source: spine
date_added: "2026-04-29"
---

# Testing Guidelines

## When to Use
- When writing tests for a new feature or bugfix
- When defining test strategy in a plan
- When reviewing test coverage or quality

## Philosophy
- **Red, Green, Refactor**: write the test BEFORE the implementation
- Tests are executable documentation of expected behavior
- No test = not ready

## Test Structure
```
tests/
  unit/           # Isolated, no external I/O
  integration/    # DB, external APIs (mocked or real)
  conftest.py     # Shared fixtures
```

## Rules
- Every public function: at least 1 success test + 1 failure test
- Descriptive names: `test_create_task_returns_201_with_valid_data()`
- Use pytest fixtures for setup/teardown
- 1 assertion per test when possible
- Fast execution (unit tests in seconds; integration controlled)

## Test Plan per Task (Minimum)
- **Positive case**: expected path works
- **Negative case**: invalid input / controlled error
- **Regression**: critical old behavior not broken

## Merge Gate
- Acceptance criteria met
- Test plan executed
- No critical failures open
- Memory bank updated: `ledger/learnings/` entry for incidents; `ledger/deliveries/` entry for the delivery

## Pragmatic Exception
In critical hotfix: implement first, create regression test immediately after stabilizing.

## Reference
Full guardrails: `docs/quality/guardrails.md`
TDD deep-dive: skill `test-driven-development`
