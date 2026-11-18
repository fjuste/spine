---
id: LEARN-006
date: 2026-11-17
title: A dataclass breaks a script that tests load with importlib
summary: test_spine_validate.py loads spine_validate.py via importlib without sys.modules; a @dataclass there failed collection. Use NamedTuple in that script.
tags:
  - type/incident
  - area/testing
  - stack/python
task: 026-pre-commit-memory-validation
---

**Symptoms:** Adding `@dataclass(frozen=True) class StagedChange` to `scripts/spine_validate.py` made `tests/unit/test_spine_validate.py` fail at collection with `AttributeError: 'NoneType' object has no attribute '__dict__'` in `dataclasses._is_type`. The new tests, which import the module normally, passed.

**Root cause:** `test_spine_validate.py` loads the script with `importlib.util.spec_from_file_location` + `exec_module` and never registers it in `sys.modules`. With `from __future__ import annotations`, `dataclass` resolves string annotations through `sys.modules[cls.__module__]`, which is missing.

**Detect early:** A new `@dataclass` (or anything that looks up its own module) in `scripts/spine_validate.py` or another script loaded by path; running only the new test files.

**Prevention:** In `spine_validate.py`, use `typing.NamedTuple` or a plain class for records. Run the full suite, not only the new test files, after touching a script that other tests load by path.

**Regression test:** `pytest tests/unit/test_spine_validate.py` (collection) with `StagedChange` as a `NamedTuple`.

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
