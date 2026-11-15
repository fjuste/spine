---
task_id: 019
title: Self-install keeps IDE trees ignored in the Spine repository
goal: Running spine.py install or update with the Spine repository as the project wires rules, commands and skills for dogfooding without removing any .gitignore entry
status: DONE
tags:
  - type/bug
  - area/infra
  - stack/python
branch: feature/self-install-gitignore
base: develop
execution_skill: executing-plans
roadmap_idea:
created_at: 2026-11-12
updated_at: 2026-11-12
completed_at: 2026-11-12
related_learnings: []
---

# 019-self-install-gitignore

## Discovery notes

Drafted 2026-11-12 from a dry run, not from `@grill-me`. Context: this repository is both the Spine code base and a Spine consumer (its local `docs/memory/` is gitignored), but it had no Spine wiring. The agent only followed Spine because `AGENTS.md` was loaded and the command/rule sources sit in the repo. Task 018 made Core SYNC digest-first, which only takes effect when `rules/02-memory-bank.md` is loaded, so the repo should run on its own install.

**Dry run** (`python3 scripts/spine.py install --dry-run --core --project-root=.`, 2026-11-12):

- `Would remove ignore entry: .cursor/`, `.claude/`, `.opencode/`. Right for consumers (they commit IDE trees), wrong here: the links would show up as untracked files in the framework repo and could be committed and shipped.
- `Would add '.spine'`: already fixed by commit `1b85e7e` (`.spine` untracked and ignored).
- 8 conflicts on `.opencode/commands/spine-*.md`: caused by a local whole-directory link `.opencode/commands -> ../commands`, removed by hand on 2026-11-12. Not a code change.
- Default skill profile is `all` (50 skills): use `--core` (+ `--add-skill=grill-me`) for this repo. Documentation only.

**Resolved decisions (proposed, confirm at approval):**

1. **Detection:** a self-install is `same_path(project, spine)` (project root resolves to the Spine clone the script runs from). No new flag.
2. **Behavior:** on a self-install, `adjust_install_gitignore` removes nothing and ensures the local-only entries are present (`.spine`, `.agents/`, `.cursor/`, `.claude/`, `.opencode/`), printing one `i` line that says why. Every other install step is unchanged.
3. **Update path is covered** because `update` calls `run_install`.

**Out of scope:**

- `vendor` with the Spine repo as project (it would strip ignores and copy `.spine/` into itself). Candidate follow-up: refuse with a clear error. Decide at approval whether to fold it in.
- Detecting a whole-directory `.opencode/commands` link as "already wired" instead of 8 conflicts. Only this repo had it.

## Objective

Make the Spine repository installable into itself so its sessions load the three rules, the `/spine-*` commands and the core skills, while its `.gitignore` keeps every IDE tree local. Document the self-install for maintainers.

## Inputs

- `scripts/spine_cli/gitignore.py` (`adjust_install_gitignore`)
- `scripts/spine_cli/install.py` (`run_install`, call at the `adjust_install_gitignore` line), `scripts/spine_cli/paths.py` (`same_path`)
- `scripts/spine_cli/constants.py` (`SYMLINK_GITIGNORE_*`, `COPY_GITIGNORE_*`)
- `tests/unit/test_spine_cli.py` (`_spine_fixture`, `_install`, gitignore assertions)
- `AGENTS.md` § 6 Development vs Consumer Installation
- Dry-run output above

## Expected Outputs

- `scripts/spine_cli/constants.py`: `SELF_INSTALL_GITIGNORE_KEEP` tuple
- `scripts/spine_cli/gitignore.py`: `adjust_install_gitignore(..., self_install: bool)` branch
- `scripts/spine_cli/install.py`: pass `self_install=same_path(project, spine)`
- `tests/unit/test_spine_cli.py`: self-install tests
- `AGENTS.md`: short "Dogfooding: install Spine into this repo" block (command, `--core`, what stays ignored, working-tree caveat)

## Acceptance Criteria (verifiable, TDD-ready)

- [x] Installing with the project equal to the Spine clone keeps every existing `.gitignore` line, including `.cursor/`, `.claude/` and `.opencode/`, in symlink and `--copy` modes.
  - Test: `test_self_install_keeps_ide_tree_ignores` (parametrized over `[]` and `["--copy"]`)
- [x] A self-install adds any missing local-only entry (`.spine`, `.agents/`, `.cursor/`, `.claude/`, `.opencode/`) and prints an info line naming the self-install.
  - Test: `test_self_install_adds_missing_local_only_entries`
- [x] A self-install still wires rules, commands and skills (`.claude/rules/01-core-protocol.md`, `.cursor/commands/spine-execute.md`, `.agents/skills/writing-plans` exist) and exits 0.
  - Test: `test_self_install_wires_ide_trees`
- [x] Consumer installs are unchanged: obsolete IDE-tree ignores are still removed when project ≠ Spine clone.
  - Test: existing `test_install_creates_spine_symlink_and_skill_hub` plus `test_consumer_install_still_strips_ide_tree_ignores`
- [x] `AGENTS.md` documents the self-install command with `--core` and the working-tree caveat.
  - Test: `test_agents_md_documents_self_install`

## Test Strategy

- **Positive:** `_spine_fixture(tmp)` installed into itself (`--project-root=tmp --spine-dir=tmp`) with a pre-existing `.gitignore` holding the IDE-tree lines; same with `--copy`.
- **Negative:** self-install with no `.gitignore` creates one with the local-only entries; consumer install with the same `.gitignore` still strips the IDE-tree lines.
- **Regression:** full suite, especially `test_spine_cli.py`, `test_install_vendor.py`, `test_rsync_mode.py`.
- **Manual evidence:** `python3 scripts/spine.py install --dry-run --core --project-root=.` in this repo shows no `Would remove ignore entry` line; then a real `install --core` leaves `git status --short` with no new untracked IDE trees.
- **Command:** `pytest -v tests/`

## Implementation Plan

### Task 1: Self-install gitignore policy

**Files:**
- Modify: `scripts/spine_cli/constants.py`, `scripts/spine_cli/gitignore.py`
- Test: `tests/unit/test_spine_cli.py`

**Step 1:** Write failing tests for the first two criteria and the consumer regression.
**Step 2:** Add `SELF_INSTALL_GITIGNORE_KEEP = (".spine", ".agents/", ".cursor/", ".claude/", ".opencode/")`; in `adjust_install_gitignore`, when `self_install` is true use it as `to_add` and an empty `to_remove`, and log `i Spine repository self-install: IDE trees stay ignored`.
**Step 3:** Commit `fix(install): keep IDE-tree ignores when installing Spine into itself`.

### Task 2: Wire detection into install

**Files:**
- Modify: `scripts/spine_cli/install.py`
- Test: `tests/unit/test_spine_cli.py`

**Step 1:** Failing test `test_self_install_wires_ide_trees`.
**Step 2:** Pass `self_install=same_path(project, spine)` at the `adjust_install_gitignore` call. Fix any other step that breaks when project and Spine clone are the same directory; record each as a `deviation` note.
**Step 3:** Commit `feat(install): detect Spine self-install`.

### Task 3: Maintainer docs and manual run

**Files:**
- Modify: `AGENTS.md`
- Test: `tests/unit/test_spine_cli.py` (or a docs test module)

**Step 1:** Failing `test_agents_md_documents_self_install`.
**Step 2:** Add the dogfooding block to `AGENTS.md` § 6: `python3 scripts/spine.py install --core --project-root=.` (+ `--add-skill=grill-me`), IDE trees stay ignored, rules follow the checked-out branch.
**Step 3:** Run the dry run, then the real install in this repo; record output location in `## Execution evidence`.
**Step 4:** Run full suite; commit `docs: document Spine self-install for maintainers`.

## Execution notes

- 2026-11-12 — decision — The `vendor` self-install refusal stays out of scope: the human ran `/spine-execute` without folding it in, so the draft's default applies. Candidate follow-up. → suggested task
- 2026-11-12 — deviation — Tasks 1 and 2 landed in one commit (`ab0c327`). The criteria tests run through `install`, so they could only pass once `same_path(project, spine)` was passed to `adjust_install_gitignore`. Scope and approach unchanged. → no promotion
- 2026-11-12 — decision — `test_self_install_wires_ide_trees` passed before any change: install already worked with project equal to the Spine clone; only the `.gitignore` step was wrong. No other install step needed a fix. The test checks `spine-plan.md` instead of the plan's `spine-execute.md` because the test fixture ships only that command. → no promotion
- 2026-11-12 — environment — Spine's own memory bank now holds seeded `domain-glossary.md`, `learnings.md` and `_task-template.md` (install seed), and `memory digest` flags a `SETUP:` block for its 5 narrative files: the next session writes those summaries. → no promotion

## Execution evidence

**Tests executed:**
- `python3 -m pytest -q tests/unit/test_spine_cli.py -k "self_install or consumer_install_still or agents_md_documents"` (red, then green)
- `python3 -m pytest -q tests/` (full suite)

**Test results:** 229 passed, 0 failed (7 new in `test_spine_cli.py`).

**Manual / external evidence:**
- Who ran it: agent (Claude Code) | When: 2026-11-12 | Commit/branch: `feature/self-install-gitignore` at `ab0c327`
  - Command: `python3 scripts/spine.py install --dry-run --core --project-root=.`
  - Summary: exit 0; `i Spine repository self-install: IDE trees stay ignored`; 0 `Would remove ignore entry` lines; all five local-only entries already present; Conflicts 0, Warnings 0.
  - Raw output: session scratchpad `/tmp/claude-1000/-home-juste-Workspace-ide-spine/96cdb8fd-63dd-4c8d-b1c8-a8f62492b50c/scratchpad/019-dry-run.txt` (temporary; rerun to reproduce)
- Who ran it: agent (Claude Code) | When: 2026-11-12 | Commit/branch: `feature/self-install-gitignore` at `ab0c327`
  - Command: `python3 scripts/spine.py install --core --project-root=.`
  - Summary: exit 0; 5 core skills, 8 workflow skills, 3 rules and the `/spine-*` commands wired for Cursor, OpenCode, Claude Code and Antigravity; docs seed 5 copied, 11 skipped; Conflicts 0, Warnings 0. Afterwards `.gitignore` unchanged and `git status --short` shows no new untracked IDE trees.
  - Raw output: session scratchpad `.../scratchpad/019-install.txt` (same folder, temporary)

## Delivery summary

Delivered 2026-11-12 on `feature/self-install-gitignore` (commits `ab0c327`, `86d7fcc`, plus the harvest commit). Preceded by `1b85e7e` on `develop` (stop tracking the absolute `.spine` symlink).

- **What shipped:** self-install detection in `install`/`update`; on a self-install `.gitignore` loses nothing and keeps `.spine`, `.agents/`, `.cursor/`, `.claude/`, `.opencode/`; consumer behavior unchanged; `AGENTS.md` self-install section.
- **Evidence (from § Execution evidence):** `pytest -q tests/` 229 passed (7 new). Dry run: 0 ignore removals, 0 conflicts. Real `install --core` on this repo: exit 0, 0 conflicts, 0 warnings, `.gitignore` unchanged, no new untracked trees. First proof in use: this harvest ran through the installed `/spine-harvest` skill.
- **Execution notes routing:** 1 `decision` (vendor refusal) → suggested task, not created; 1 `deviation` (Tasks 1–2 in one commit) → no promotion; 1 `decision` (no other install step needed a fix) → no promotion; 1 `environment` (seeded memory files, pending SETUP) → no promotion.
- **Decision log:** no entry; the self-install behavior is reversible and documented in `AGENTS.md`, so it misses the hard-to-reverse criterion.
- **Learnings:** no incident or rework; no `LEARN-NNN` entry.
- **Roadmap:** no `roadmap_idea`; not applicable.
