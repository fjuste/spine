---
task_id: 026
title: Git pre-commit hook validates staged memory files
goal: "An opt-in git `pre-commit` hook runs `spine_validate.py staged`, which blocks commits whose staged `docs/memory/` changes break the task contract, a ledger entry `summary:` or a ledger `INDEX.md`, for every agent and for humans"
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/pre-commit-memory-validation
base: develop
execution_skill: executing-plans
roadmap_idea: I8
created_at: 2026-11-17
updated_at: 2026-11-17
completed_at: 2026-11-17
related_learnings: [LEARN-002, LEARN-005, LEARN-006, LEARN-007]
---

# 026-pre-commit-memory-validation

## Discovery notes

- 2026-11-17 — Source: `docs/documentation/evolucao/hooks-and-summaries.md` § 3.3 H6 ("`spine_validate.py` on staged memory files", agent-neutral safety net). Agent hooks (I9, I11, I12, I13) stay out of scope.
- 2026-11-17 — Pilot chose **format errors only** block the commit: staged task files failing the task contract, changed ledger entries with a missing or over-160-char `summary:`, and a stale or missing `INDEX.md` in a ledger folder the commit touches. Budget and open-task warnings print but never block.
- 2026-11-17 — Pilot chose to validate the **staged snapshot**, not the working tree: it closes the loop where the hook fails, the agent fixes the file, forgets `git add` and commits the broken staged version.
- 2026-11-17 — Pilot chose **opt-in like Graphify/MkDocs**: TTY prompt during `install`/`update` (default yes), `--with-pre-commit` flag, `--pre-commit-uninstall` side command.
- 2026-11-17 — Planning finding: only files whose **content** changed are checked. A pure rename (`R100`) is skipped, so a human can `git mv` a legacy pre-v2.1 task (Spine's 008–014, or `completed_tasks/016`, which fails the contract today) to close it without being blocked. Same reason for checking only changed ledger entries: untouched legacy entries never block.
- 2026-11-17 — LEARN-002 applies: `/spine-harvest` and `/spine-plan` commit memory files, so their steps must already leave the staged snapshot valid (harvest runs `memory index` before committing; plan runs `spine_validate.py task`). Check both command files during execution; no reordering is expected.
- 2026-11-17 — LEARN-005 applies: hook tests use a real temporary git repository (`git init` in `tmp_path`), and the full suite is re-run after adding the new module with pytest's own exit code.
- Out of scope: `vendor` subcommand and Windows install (vendor mode) do not co-install the hook, same as Graphify/MkDocs today; `pre-commit` framework or husky configs are not written (the installer prints the manual line instead).

## Objective

Give Spine its first agent-neutral deterministic guard rail (roadmap G2): memory-format errors are stopped at `git commit`, whichever agent or human made them, instead of surfacing at harvest.

**Validator — `spine_validate.py staged`** (new subcommand, stdlib only, run from the project root):

1. List staged changes under `docs/memory/` with `git diff --cached --name-status -z -M -- docs/memory/`. No entries → exit 0 with no output (fast path for code-only commits).
2. Materialize the index copy of `docs/memory/` into a temporary directory (`git ls-files -z -- docs/memory/` piped to `git checkout-index -z --stdin --prefix=<tmp>/`). All checks read this snapshot, never the working tree.
3. **Task contract (blocks):** for each added, modified, copied or renamed-with-changes (`R` score < 100) file matching `docs/memory/{active,completed}_tasks/NNN-*.md`, run the existing `validate_task` on the snapshot copy. Errors print as `ERROR: <path>: <message>`.
4. **Ledger entries (blocks):** for each ledger folder (`decisions/`, `learnings/`, `deliveries/`) with any staged change (including deletes and `INDEX.md` itself): changed entry files with a missing or over-160-char `summary:` are errors; the folder's snapshot `INDEX.md` must equal `render_index` of the snapshot entries, else `ERROR: … INDEX.md is stale — run python3 .spine/scripts/spine.py memory index, then git add it`. Untouched entries are not checked for summaries.
5. **Warnings (never block):** budget overruns (`check_budgets`) and open-task problems (`check_open_tasks`) on the snapshot print as `WARNING:` lines; no `OK:` lines.
6. Exit 1 when any error was recorded, with a closing line: `Commit blocked: N memory error(s). Fix them, git add the files, and commit again.` Otherwise exit 0.
7. Outside a git work tree → `ERROR:` and exit 1.

Reuse `validate_task`, `collect_entries`, `render_index`, `index_path`, `check_budgets`, `check_open_tasks` and `ENTRY_SUMMARY_MAX_CHARS`; no logic duplicated from `spine_cli/memory.py`.

**Hook — marked block in the pre-commit file** (new module `scripts/spine_cli/precommit.py`):

- Hooks directory from `git rev-parse --git-path hooks` (honours `core.hooksPath` and worktrees); file `pre-commit`.
- Block between `# >>> spine pre-commit >>>` and `# <<< spine pre-commit <<<`, POSIX sh:

  ```sh
  # >>> spine pre-commit >>>
  if [ -f .spine/scripts/spine_validate.py ]; then
    spine_py=$(command -v python3 || command -v python)
    if [ -n "$spine_py" ]; then
      "$spine_py" .spine/scripts/spine_validate.py staged || exit 1
    else
      echo "spine pre-commit: python not found; memory validation skipped" >&2
    fi
  else
    echo "spine pre-commit: .spine not found; memory validation skipped" >&2
  fi
  # <<< spine pre-commit <<<
  ```

- No hook file → create it with `#!/bin/sh`, the block, mode 0755.
- Existing hook whose shebang names `sh`, `bash` or `zsh` → insert the block right after the shebang (so an `exit 0` later in the file cannot skip it); keep the rest unchanged.
- Existing block → replace it in place (idempotent; re-running install changes nothing).
- Any other existing hook (no shebang, other interpreter, hook managers such as husky) → leave the file untouched and print a `NOTE:` with the one line to add by hand: `python3 .spine/scripts/spine_validate.py staged || exit 1`.
- Uninstall removes only the block; if the file then holds only a shebang and blank lines, delete it.

**Installer wiring:** `spine.py install` and `spine.py update` accept `--with-pre-commit` (install the block) and `--pre-commit-uninstall` (side command: remove the block, then return, like `--mkdocs-uninstall`). On a TTY, without the flag and when the block is not already installed, prompt `Enable the git pre-commit memory check for this project? [Y/n]:` (same pattern as `_maybe_prompt_mkdocs`). `spine.py uninstall` also removes the block. Dry runs print what would change and write nothing.

**Docs:** README § Optional: pre-commit memory check; AGENTS.md (install flags list and a short Memory Bank paragraph); rule 01 guard rail: agents never bypass the hook with `git commit --no-verify` — fix, `git add`, commit again; `commands/spine-commit.md`: what to do when the hook rejects a commit. Dogfood: install the hook in the Spine repo itself.

## Inputs

- `scripts/spine_validate.py` (`validate_task`, `Report`, subcommand parser)
- `scripts/spine_cli/memory.py` (`collect_entries`, `render_index`, `index_path`, `LEDGER_FOLDERS`, `ENTRY_SUMMARY_MAX_CHARS`, `check_budgets`, `check_open_tasks`)
- `scripts/spine.py` (install/update argument parser, `Options` mapping), `scripts/spine_cli/options.py`, `scripts/spine_cli/install.py` (`_maybe_prompt_mkdocs`, `_install_side_command`, side-command dispatch), `scripts/spine_cli/uninstall.py`
- `docs/documentation/evolucao/hooks-and-summaries.md` § 3 (H6, local only)
- `README.md`, `AGENTS.md`, `rules/01-core-protocol.md`, `commands/spine-commit.md`, `commands/spine-harvest.md`, `commands/spine-plan.md`

## Expected Outputs

- `scripts/spine_validate.py` — `staged` subcommand
- `scripts/spine_cli/precommit.py` — install / uninstall / detect the marked block
- `scripts/spine.py`, `scripts/spine_cli/options.py`, `scripts/spine_cli/install.py`, `scripts/spine_cli/uninstall.py` — flags, prompt, uninstall
- `tests/unit/test_precommit_staged.py`, `tests/unit/test_precommit_hook.py`
- `README.md`, `AGENTS.md`, `rules/01-core-protocol.md`, `commands/spine-commit.md` — docs
- Spine repo: hook installed (local `.git/hooks/pre-commit`, not versioned)

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] AC1 — Staged task files are checked against the task contract on the staged snapshot: a staged task with an empty `tags:` list exits 1 with `ERROR: docs/memory/active_tasks/NNN-…md: tags list empty …`; fixing the working-tree file without `git add` still exits 1; after `git add` it exits 0. A pure `git mv` of a legacy task without frontmatter exits 0.
  - Test: `test_precommit_staged.py::test_staged_task_contract_error_blocks`, `::test_unstaged_fix_still_blocks`, `::test_pure_rename_of_legacy_task_is_not_checked`
- [ ] AC2 — Ledger checks block only on what the commit touches: a staged new entry without `summary:` exits 1; a staged entry without re-running `memory index` exits 1 with the `INDEX.md is stale` fix; staging the regenerated `INDEX.md` exits 0; an untouched legacy entry without `summary:` in the same folder does not block.
  - Test: `::test_changed_entry_without_summary_blocks`, `::test_stale_index_in_touched_folder_blocks`, `::test_untouched_entry_problems_do_not_block`
- [ ] AC3 — Budget and open-task problems print `WARNING:` lines and exit 0; a commit that stages no `docs/memory/` file exits 0 with no output; outside a git repository the command exits 1 with `ERROR:`.
  - Test: `::test_open_task_warning_does_not_block`, `::test_no_memory_files_staged_is_silent`, `::test_outside_git_repo_errors`
- [ ] AC4 — `install --with-pre-commit` writes the marked block to `<git rev-parse --git-path hooks>/pre-commit` (executable, `#!/bin/sh` when new), honours `core.hooksPath`, is idempotent, inserts the block right after the shebang of an existing sh/bash hook keeping its body, and leaves a non-sh hook untouched with a `NOTE:` naming the manual line.
  - Test: `test_precommit_hook.py::test_install_creates_executable_hook`, `::test_install_is_idempotent`, `::test_install_respects_core_hooks_path`, `::test_install_inserts_after_shebang_of_existing_hook`, `::test_non_shell_hook_is_left_untouched`
- [ ] AC5 — `--pre-commit-uninstall` and `spine.py uninstall` remove only the block (the file is deleted when nothing else remains); the TTY prompt appears only when the block is absent and no flag was given; `--dry-run` writes nothing.
  - Test: `::test_uninstall_removes_only_the_block`, `::test_uninstall_deletes_file_left_empty`, `::test_prompt_skipped_when_installed_or_not_tty`, `::test_dry_run_writes_nothing`
- [ ] AC6 — End to end in a temporary repo wired with `.spine` → this clone: `git commit` of a broken task fails with the validator's `ERROR:` line, fixed and staged it succeeds; with `.spine` absent the hook prints the skip note and the commit succeeds.
  - Test: `::test_git_commit_blocked_then_allowed`, `::test_missing_spine_skips_with_note`
- [ ] AC7 — Docs and dogfood: README section, AGENTS.md flags and paragraph, rule 01 `--no-verify` guard rail, `commands/spine-commit.md` rejection step; the hook is installed in the Spine repo and a real memory commit on the feature branch passes through it.
  - Test: `test_precommit_hook.py::test_docs_describe_pre_commit_check` (README, AGENTS.md and rule 01 mention `spine_validate.py staged` / `--with-pre-commit` / `--no-verify`); manual evidence in `## Execution evidence`.

## Test Strategy

- Positive: valid staged task / entry / regenerated `INDEX.md` → exit 0; hook created, replaced idempotently, removed cleanly.
- Negative: contract errors, missing summaries, stale index, unstaged fix → exit 1; non-sh hook untouched; missing `.spine` or python → skip note, commit allowed.
- Regression: existing `spine_validate.py` subcommands and install/update/uninstall tests unchanged; full suite green.
- Fixtures: real git repositories in `tmp_path` (`git init`, local `user.name`/`user.email`, minimal `docs/memory/` seeded from `templates/docs/memory/`); no mocking of git (LEARN-005).
- Command: `pytest -v tests/unit/test_precommit_staged.py tests/unit/test_precommit_hook.py`, then `pytest tests/ > /tmp/…/pytest.log 2>&1; echo $?` (no pipe hiding the exit code).

## Implementation Plan

### Task 1: `staged` — task contract on the staged snapshot (AC1, AC3)

**Files:**
- Modify: `scripts/spine_validate.py` (new section `# staged`, parser entry)
- Test: `tests/unit/test_precommit_staged.py`

**Step 1:** Write a `git_repo` fixture (init, config, seed `docs/memory/` with an empty `active_tasks/` and the three ledger folders + regenerated `INDEX.md`, initial commit) and the AC1/AC3 tests calling `spine_validate.main(["staged"])` with `monkeypatch.chdir`.

**Step 2:** Run — expect FAIL (`invalid choice: 'staged'`).

**Step 3:** Implement `_staged_changes(root)` (parse `--name-status -z -M` into `(status, score, path)`), `_snapshot(root, tmp)` (`ls-files` → `checkout-index`), `validate_staged(root, report)` for tasks + warnings, and `run_staged`.

**Step 4:** Run — expect PASS. Commit `feat: spine_validate.py staged checks the task contract on staged memory files`.

### Task 2: `staged` — ledger entries and INDEX.md (AC2)

**Files:**
- Modify: `scripts/spine_validate.py`
- Test: `tests/unit/test_precommit_staged.py`

**Step 1:** Write the AC2 tests (new entry without summary; entry staged without index; regenerated index staged; untouched legacy entry without summary).

**Step 2:** Run — expect FAIL.

**Step 3:** Add the per-folder ledger check reusing `collect_entries`, `render_index`, `index_path`, `ENTRY_SUMMARY_MAX_CHARS`.

**Step 4:** Run — expect PASS. Commit `feat: staged check blocks on changed ledger entries and stale INDEX.md`.

### Task 3: Hook block install / uninstall (AC4, AC5)

**Files:**
- Create: `scripts/spine_cli/precommit.py`
- Test: `tests/unit/test_precommit_hook.py`

**Step 1:** Write the AC4/AC5 file-level tests against `precommit.install_hook(project, log, dry_run)` / `uninstall_hook(...)` / `hook_installed(project)`.

**Step 2:** Run — expect FAIL (module missing).

**Step 3:** Implement: hooks dir via `git rev-parse --git-path hooks`, block constants, create / insert-after-shebang / replace / refuse-with-NOTE, uninstall, chmod 0755.

**Step 4:** Run — expect PASS. Commit `feat: precommit module installs the spine pre-commit block`.

### Task 4: Installer flags, prompt and uninstall (AC5)

**Files:**
- Modify: `scripts/spine.py`, `scripts/spine_cli/options.py`, `scripts/spine_cli/install.py`, `scripts/spine_cli/uninstall.py`
- Test: `tests/unit/test_precommit_hook.py`

**Step 1:** Write tests for `--with-pre-commit`, `--pre-commit-uninstall` (side command), prompt gating (`isatty` false / block present) and `spine.py uninstall` removing the block.

**Step 2:** Run — expect FAIL.

**Step 3:** Add `with_pre_commit` / `pre_commit_uninstall` options, parser flags on `install` and `update`, `_maybe_prompt_pre_commit`, dispatch next to MkDocs, call `uninstall_hook` from `uninstall_applied`.

**Step 4:** Run — expect PASS; run existing install/update/uninstall tests. Commit `feat: install --with-pre-commit wires the memory check`.

### Task 5: End-to-end hook (AC6)

**Files:**
- Test: `tests/unit/test_precommit_hook.py`

**Step 1:** Write the e2e tests: temp repo, `.spine` symlink to this clone, install block, `git commit` broken task → non-zero + `ERROR:` in stderr; fix + `git add` → commit succeeds; remove `.spine` → note + success.

**Step 2:** Run — fix whatever the real git run exposes. Commit `test: end-to-end pre-commit memory check`.

### Task 6: Docs and dogfood (AC7)

**Files:**
- Modify: `README.md`, `AGENTS.md`, `rules/01-core-protocol.md`, `commands/spine-commit.md`
- Test: `tests/unit/test_precommit_hook.py::test_docs_describe_pre_commit_check`

**Step 1:** Write the docs test. Run — expect FAIL.

**Step 2:** Write README § Optional: pre-commit memory check (what blocks, what warns, staged snapshot, install/uninstall, manual line for hook managers, vendor/Windows not covered); AGENTS.md flags + paragraph; rule 01 guard rail; spine-commit rejection step. Re-read `commands/spine-harvest.md` and `commands/spine-plan.md` commit steps against the new check (LEARN-002); record any change as an execution note.

**Step 3:** Run — expect PASS. Run `python3 scripts/spine.py install --with-pre-commit --project-root=.` in the Spine repo; commit the docs and task notes through the hook. Commit `docs: describe the pre-commit memory check`.

**Step 4:** Full suite with the real exit code; fill `## Execution notes` and `## Execution evidence`.

## Execution notes

- 2026-11-17 — deviation — Tasks 1 and 2 implemented in one pass: the ledger check was written with the task check, so the AC2 tests passed on first run. Their value was confirmed by disabling `_check_staged_ledger` (4 AC2 tests failed), then restoring it. No scope change. → no promotion
- 2026-11-17 — decision — Paths use `git diff --relative` and `rev-parse --show-prefix`, so a project in a subdirectory of a larger repository is checked at its own `docs/memory/` (extra test `test_project_in_subdirectory_of_repository`). Git subprocesses inherit `GIT_INDEX_FILE`, so `git commit <paths>` (temporary index) is checked on what is actually committed. → no promotion
- 2026-11-17 — decision — Extra tests beyond the plan: a modified (not renamed) legacy task is checked, an over-160-char summary blocks, a deleted entry needs a fresh `INDEX.md`. → no promotion
- 2026-11-17 — deviation — Task 3: `precommit.py` was written before its tests (TDD order inverted); the 13 tests were then written against the plan's AC4/AC5 wording, not the code. No scope change. → no promotion
- 2026-11-17 — incident — `StagedChange` as a `@dataclass` broke collection of `test_spine_validate.py`: it loads the script with `importlib` without registering it in `sys.modules`, and `dataclass` with postponed annotations looks the module up there. Fix: `typing.NamedTuple`, no test change. → LEARN-006
- 2026-11-17 — decision — `--pre-commit-uninstall` is an `install` flag only (like `--mkdocs-uninstall`); `update` accepts `--with-pre-commit` and passes it through to the install pass. The plan listed both flags on `update`; on `update` the side command would also pull Spine and sync `opencode.json`. Uninstall stays available via `install --pre-commit-uninstall` and `spine.py uninstall`. → no promotion
- 2026-11-17 — rework — Dropped an unplanned refresh of an installed block on every `update`: it called `git rev-parse` during `update --no-pull`, which `test_update_no_pull_does_not_call_git` forbids. The block is refreshed by re-running `install --with-pre-commit`. → LEARN-007
- 2026-11-17 — out-of-scope — No `--no-pre-commit-prompt` flag (MkDocs and Graphify have one): a pilot who declines the prompt is asked again on each interactive `install`/`update`. Add the flag if that proves annoying. → Known Opportunities
- 2026-11-17 — decision — LEARN-002 check: `/spine-harvest` runs `memory index` (step 4c.1) before its final commit (step 6) and `/spine-plan` runs `spine_validate.py task` before committing, so both already leave a valid staged snapshot; no reordering. A harvest that edits a legacy task without frontmatter (status DONE) would now be blocked, by design; legacy tasks are closed with a pure `git mv`. → DEC 2026-11-17-pre-commit-staged-memory-check
- 2026-11-17 — environment — Dogfood install of the hook into this repository (`python3 scripts/spine.py install --core --with-pre-commit --project-root=.`) was denied by the agent's permission classifier (writing `.git/hooks/pre-commit`). The pilot runs it. The dry run showed only `Would create .git/hooks/pre-commit with the spine pre-commit block`, with 0 conflicts and 0 warnings. → no promotion
- 2026-11-17 — resume — Done: Tasks 1–6 code, tests and docs committed on `feature/pre-commit-memory-validation`. Next: the pilot runs the dogfood install above, then makes one memory commit through the hook (e.g. moving this task to REVIEW) and records it under Manual / external evidence. Then set `status: REVIEW`. → no promotion
- 2026-11-17 — environment — Pilot ran the dogfood install; `.git/hooks/pre-commit` now holds the spine block (new `#!/bin/sh` hook, executable). The REVIEW commit went through it. Resume point above is closed. → no promotion

## Execution evidence

**Tests executed:**
- `pytest -v tests/unit/test_precommit_staged.py tests/unit/test_precommit_hook.py`
- `pytest tests/ > <scratchpad>/pytest.log 2>&1; echo $?` (exit code read directly, LEARN-005)
- Mutation check: `_check_staged_ledger` disabled → 4 AC2 tests failed; restored.

**Test results:**
- New tests: 14 in `test_precommit_staged.py` and 22 in `test_precommit_hook.py`, all passing (AC1–AC7 named tests included, plus extras: modified legacy task, over-long summary, deleted entry, monorepo subdirectory, outdated block refresh, husky/python/no-shebang hooks, outside git, missing python).
- Full suite: 414 passed, exit 0 (2026-11-17, branch `feature/pre-commit-memory-validation`).

**Manual / external evidence:**
- 2026-11-17, agent: `python3 scripts/spine_validate.py staged` on this repo's staged plan, task and docs commits → exit 0, one `WARNING:` (7 legacy tasks without `status:`), no errors.
- 2026-11-17, pilot: `python3 scripts/spine.py install --core --with-pre-commit --project-root=.` → `+ pre-commit memory check: .git/hooks/pre-commit`, 0 conflicts, 0 warnings (output in the session terminal).
- 2026-11-17, agent: the commit that sets this task to `status: REVIEW` on `feature/pre-commit-memory-validation` ran through the installed hook (plain `git commit`, no `--no-verify`): exit 0, one `WARNING:` for the 7 legacy tasks, no errors.

## Delivery summary

Delivered 2026-11-17 on `feature/pre-commit-memory-validation`: `spine_validate.py staged` (staged-snapshot memory check), `spine_cli/precommit.py` (marked hook block), installer flags, prompt and uninstall, docs (README, AGENTS.md, rule 01, `/spine-commit`). Evidence: 36 new tests; `pytest tests/` 414 passed, exit 0, at execution and harvest; hook installed by the pilot in this repo; the REVIEW and harvest commits ran through it. All AC1–AC7 met.

Execution notes promoted: incident → LEARN-006 (dataclass in an importlib-loaded script); rework → LEARN-007 (install pass runs on every update); LEARN-002 check → decision entry `2026-11-17-pre-commit-staged-memory-check`; out-of-scope → Known Opportunities (`--no-pre-commit-prompt`). Deviations (TDD order in Tasks 1–3) stay here. Delivery entry: `ledger/deliveries/2026-11-17-026-pre-commit-memory-validation.md`. Roadmap I8 → Done.
