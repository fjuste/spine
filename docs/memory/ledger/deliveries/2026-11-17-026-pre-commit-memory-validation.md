---
id: 2026-11-17-026-pre-commit-memory-validation
date: 2026-11-17
title: Pre-commit memory check — staged memory files are validated at git commit, for every agent and for humans
summary: Opt-in git pre-commit hook runs spine_validate.py staged; it blocks staged task contract errors, bad entry summaries and stale INDEX.md; budgets only warn.
why: Memory-format errors from any agent or human now stop at git commit instead of surfacing at harvest.
tags:
  - type/feature
  - area/memory
  - stack/python
task: 026-pre-commit-memory-validation
---

**Branch:** feature/pre-commit-memory-validation

**Description:** New `spine_validate.py staged` subcommand: lists staged changes under `docs/memory/` (`git diff --cached --name-status -z -M --relative`), materializes the index copy into a temporary directory (`ls-files` → `checkout-index`) and checks only that snapshot. Errors (exit 1, closing `Commit blocked: N memory error(s)…`): staged task files in `active_tasks/` or `completed_tasks/` that fail `validate_task` (pure renames skipped, so legacy tasks close with `git mv`), changed ledger entries with a missing or over-160-char `summary:`, and a missing or stale `INDEX.md` in a ledger folder the commit touches (deletes included). Budget and open-task problems print `WARNING:` only; no staged memory change → silent exit 0; outside git → `ERROR:`. Works for a project in a subdirectory of a larger repository and for `git commit <paths>` (inherits `GIT_INDEX_FILE`). New `scripts/spine_cli/precommit.py` writes a marked POSIX sh block into `<git rev-parse --git-path hooks>/pre-commit`: new `#!/bin/sh` hook (0755), inserted after the shebang of an existing sh/bash/zsh hook, replaced in place when present, and refused with a `NOTE:` and the manual line for other hooks (python, no shebang, husky, lefthook, pre-commit framework). The block skips with a note when `.spine` or Python is missing. Installer: `install`/`update --with-pre-commit`, `install --pre-commit-uninstall` (side command), a TTY prompt while the block is absent, `spine.py uninstall` removes the block; `vendor` and Windows install do not co-install it. Docs: README § Optional: pre-commit memory check, AGENTS.md flags and paragraph, rule 01 guard rail against `git commit --no-verify`, `/spine-commit` rejection step. Evidence: 14 tests in `tests/unit/test_precommit_staged.py` and 22 in `tests/unit/test_precommit_hook.py` (real git repositories, global git config isolated, end-to-end `git commit` blocked then allowed); mutation check on the ledger check; `pytest tests/` 414 passed, exit 0, at execution and at harvest (379 before). Dogfood: the pilot installed the hook in this repository on 2026-11-17 (`install --core --with-pre-commit`); the REVIEW commit and this harvest commit ran through it (one `WARNING:` for the 7 legacy tasks, no errors). Graphify and MkDocs not active. Roadmap I8 Done.
