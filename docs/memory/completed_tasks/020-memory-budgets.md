---
task_id: 020
title: Memory budgets — digest-first limits in the validator and Current state compaction at harvest
goal: spine_validate.py memory warns when the Core SYNC digest, the Current state block or an on-demand memory file exceeds its budget, and /spine-harvest compacts Current state and reports the remaining warnings as follow-ups
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/memory-budgets
base: develop
execution_skill: executing-plans
roadmap_idea: I4
created_at: 2026-11-13
updated_at: 2026-11-14
completed_at: 2026-11-14
related_learnings: []
---

# 020-memory-budgets

## Discovery notes

Discovery (grill-me protocol) ran on 2026-11-13. Sources: roadmap I4, `docs/documentation/evolucao/hooks-and-summaries.md` §2.5–2.6, task 018 delivery.

**Measured 2026-11-13 (read-only, `memory digest` split by section):**

| Project | Digest | Current state | Open tasks | Narrative | Logs |
|---|---|---|---|---|---|
| onboarding-hub | 13,253 | 4,970 | 5,150 (19 tasks) | 1,159 | 1,525 |
| agenthub | 10,522 | 6,729 | 342 | 1,155 | 1,820 |

The global file bodies no longer reach Core SYNC. G1 (≤ 8,000) is missed because of `progress.md` **Current state** and the open-task list.

**Resolved decisions:**

1. **Digest-first budgets.** Budgets cover what Core SYNC loads (digest total ≤ 8,000 = G1; Current state block ≤ 1,500). Soft per-file budgets cover the files agents open on demand: narrative body ≤ 3,000, `decision-log.md` ≤ 5,000, `progress.md` ≤ 6,000, `learnings.md` ≤ 6,000. Task files, `roadmap.md` and `completed_tasks/` have no budget (I5/I6 territory).
2. **Constants only.** Limits are named constants in `scripts/spine_cli/memory.py`. There is no `budget_chars:` frontmatter override (nobody asked for that configurability). Values follow the design doc and get recalibrated later. Today all three real projects warn on their log files, and those warnings are the input for I6.
3. **Warnings, never failures.** An over-budget file is a `WARNING:`; exit code stays 0. Only a missing `docs/memory/` is an `ERROR:` (exit 1).
4. **Harvest compacts only what it owns.** `/spine-harvest` runs `spine_validate.py memory` after refreshing `progress.md`. When Current state is over budget, harvest rewrites that block to fit, which it already owns. Every other warning is listed in the harvest summary as a follow-up pointing to I5/I6 or to the human. Harvest never edits `global/` to meet a budget without showing the diff to the human.
5. **The digest stays unchanged.** It gets no budget line, which keeps it lean and stops agents from compacting memory off-task mid-session. The validator and harvest are the only places budgets show up.
6. **I6 stays out.** `spine.py memory compact` (rolling window + archive) is not built here.
7. **Over-budget digest names its causes.** The digest-total warning lists each digest section's size, largest first. The human sees, for example, that 18 stale `PLANNING` tasks cost 5k chars, and no separate open-task budget is needed.

No decision-log entry: all choices are reversible constants and command text.

## Objective

Add a `memory` subcommand to `scripts/spine_validate.py` that measures the memory bank against fixed budgets and prints `OK`/`WARNING:` lines. The budget logic lives in `scripts/spine_cli/memory.py` and reuses the digest machinery (`collect_files`, `_section`, `build_digest`). Add a budget step to `/spine-harvest`: run the validator, compact an over-budget Current state, and route every other warning to the harvest summary. Document the budgets in `rules/02-memory-bank.md`, `README.md` and `AGENTS.md`.

## Inputs

- `scripts/spine_cli/memory.py` (task 018: `collect_files`, `_section`, `build_digest`, `classify`, `strip_frontmatter`)
- `scripts/spine_validate.py` (`Report`, subcommand pattern, `--dry-run`, exit-code contract)
- `commands/spine-harvest.md` (step 4a refreshes Current state)
- `rules/02-memory-bank.md` (Tiered SYNC, Narrative summaries)
- `docs/documentation/evolucao/hooks-and-summaries.md` §2.5–2.6
- Real projects for evidence (read-only): onboarding-hub, agenthub, intelligence-engine

## Expected Outputs

- `scripts/spine_cli/memory.py`: budget constants, `BudgetCheck` result type, `check_budgets(root) -> list[BudgetCheck]`, digest section sizes
- `scripts/spine_validate.py`: `memory` subparser (`--project-root`, `--dry-run`) → `validate_memory` / `run_memory`
- `commands/spine-harvest.md`: memory budget step (after 4a) + summary reporting in step 7
- `rules/02-memory-bank.md`: short § Memory budgets
- `README.md`, `AGENTS.md`: `spine_validate.py memory` in the validator list
- `tests/unit/test_memory_budgets.py` (new)

## Acceptance Criteria (verifiable, TDD-ready)

- [x] `check_budgets` measures each budgeted scope against its constant: digest total ≤ 8,000, Current state block ≤ 1,500, each narrative file body (frontmatter excluded) ≤ 3,000, `decision-log.md` ≤ 5,000, `progress.md` ≤ 6,000, `learnings.md` ≤ 6,000. Task files, `roadmap.md` and `completed_tasks/` are not budgeted, and missing files are skipped.
  - Test: `test_check_budgets_flags_each_scope_over_limit`, `test_unbudgeted_files_are_ignored`, `test_narrative_budget_excludes_frontmatter`, `test_missing_files_are_skipped`.
- [x] When the digest total is over budget, its result lists the digest section sizes largest first (e.g. `Open tasks 5,150; Current state 4,970; …`).
  - Test: `test_digest_over_budget_names_largest_sections`.
- [x] `spine_validate.py memory` prints one `OK` line per scope within budget (stdout) and one `WARNING:` line per scope over budget (stderr) with path, actual chars, limit and a remedy hint, and exits 0 when only warnings occur. A missing `docs/memory/` prints `ERROR:` and exits 1. `--project-root` and `--dry-run` are accepted.
  - Test: `test_validate_memory_within_budget_prints_ok_exit_0`, `test_validate_memory_over_budget_warns_exit_0`, `test_validate_memory_without_memory_dir_fails`, `test_validate_memory_cli_project_root`.
- [x] `spine.py memory digest` output is unchanged by this task: no budget line, even when limits are exceeded.
  - Test: `test_digest_has_no_budget_line_when_over_budget`, plus the existing `tests/unit/test_memory_digest.py` stays green.
- [x] `commands/spine-harvest.md` has a memory-budget step after 4a: it runs `python3 .spine/scripts/spine_validate.py memory`, rewrites an over-budget Current state to fit, lists every other warning in the step 7 summary as a follow-up, and forbids editing `global/` for budgets without showing the diff to the human. `rules/02-memory-bank.md` has a § Memory budgets, and `README.md`/`AGENTS.md` list the `memory` validator.
  - Test: `test_harvest_runs_memory_budget_step`, `test_memory_bank_rule_documents_budgets`, `test_docs_list_memory_validator`.
- [x] Manual evidence: `spine_validate.py memory --project-root=<repo>` on onboarding-hub, agenthub, intelligence-engine and Spine itself (read-only), with warnings recorded in `## Execution evidence`.
  - Test: manual run; `git status docs/memory` clean in each target afterwards.

## Test Strategy

- **Unit (new `tests/unit/test_memory_budgets.py`):** `tmp_path` memory banks built just under and just over each limit, using the named constants, never hard-coded numbers. Covers frontmatter exclusion, missing files, unbudgeted kinds, section-size ordering, and digest output parity.
- **CLI:** load `spine_validate.py` the same way as `tests/unit/test_spine_validate.py`. Assert exit codes and the `OK`/`WARNING:`/`ERROR:` prefixes on stdout/stderr.
- **Text contract:** assert the harvest step, the rule section and the README/AGENTS.md mentions by key phrases.
- **Regression:** full suite, especially `test_memory_digest.py`, `test_spine_validate.py`, `test_memory_bank_v21.py` and `test_task_contract_alignment.py`.
- **Command:** `pytest -v tests/`

## Implementation Plan

### Task 1: Budget model in `memory.py`

**Files:**
- Modify: `scripts/spine_cli/memory.py`
- Test: `tests/unit/test_memory_budgets.py`

**Step 1:** Write failing tests for `check_budgets` (each scope over/under, frontmatter excluded, unbudgeted kinds ignored, missing files skipped) and for digest section sizes ordered largest first.
**Step 2:** Add constants (`DIGEST_BUDGET_CHARS = 8_000`, `CURRENT_STATE_BUDGET_CHARS = 1_500`, `NARRATIVE_BODY_BUDGET_CHARS = 3_000`, `LOG_BUDGET_CHARS = {...}`), a frozen `BudgetCheck(scope, chars, limit, detail)` dataclass with an `over` property, `digest_section_sizes(digest)` and `check_budgets(root)`. Reuse `collect_files`, `_section`, `strip_frontmatter` and `build_digest`.
**Step 3:** Commit `feat(memory): measure memory bank against digest-first budgets`.

### Task 2: `spine_validate.py memory`

**Files:**
- Modify: `scripts/spine_validate.py`
- Test: `tests/unit/test_memory_budgets.py`

**Step 1:** Write failing CLI tests (OK/WARNING/ERROR prefixes, exit codes, `--project-root`, `--dry-run`).
**Step 2:** Add `validate_memory(root, report)` and `run_memory(args)`, plus the `memory` subparser and module docstring usage line. Write each warning as `<scope>: <chars> chars > <limit> — <hint>`. Hints: Current state → "compact at harvest"; log files → "archive (roadmap I6)"; narrative → "split or trim with human approval"; digest → largest sections.
**Step 3:** Commit `feat(validate): spine_validate.py memory reports budget warnings`.

### Task 3: Harvest step, rule and docs

**Files:**
- Modify: `commands/spine-harvest.md`, `rules/02-memory-bank.md`, `README.md`, `AGENTS.md`
- Test: `tests/unit/test_memory_budgets.py`

**Step 1:** Write failing text tests.
**Step 2:** Add harvest step **4a.1 Memory budgets** and a step 7 summary bullet; add § Memory budgets to the rule (limits table, warnings ≠ failures, harvest compacts Current state only, `global/` needs a human-approved diff); add the validator to README/AGENTS.md.
**Step 3:** Run the full suite; commit `docs(memory): memory budgets in harvest and memory-bank rule`.

### Task 4: Evidence

**Step 1:** Run `python3 scripts/spine_validate.py memory --project-root=<repo>` on onboarding-hub, agenthub, intelligence-engine and this repo.
**Step 2:** Record the warnings per project in `## Execution evidence`; confirm `git status docs/memory` is clean in the external repos.

## Execution notes
- 2026-11-13 — environment — `/spine-execute` was invoked with `docs/documentation/active_tasks/020`, a path that does not exist; executed `docs/memory/active_tasks/020-memory-budgets.md`, the only task 020. Pre-existing uncommitted edits (`docs/memory/global/*`, `ledger/roadmap.md`, `skills/synced/`) carried onto `feature/memory-budgets` and stay out of this task's commits. → no promotion
- 2026-11-13 — decision — Remedy hints live in `BudgetCheck.detail` (set by `check_budgets` in `memory.py`) instead of the validator, so `spine_validate.py memory` only formats lines. The Current state check is emitted alongside the `progress.md` file check. → no promotion
- 2026-11-13 — out-of-scope — The 3,000-char narrative budget flags nearly every `global/` file in the three real projects (onboarding-hub 6, agenthub 5, intelligence-engine 7 incl. `ledger/okf-integration-design.md`). That adds 5–7 warnings per harvest. Discovery decision 2 already defers recalibration, so I did not change the constant. Input for the next `/spine-roadmap --review` of I4/I5. → suggested task

## Execution evidence
**Tests executed:** `python3 -m pytest -v tests/` (full suite); focused: `python3 -m pytest tests/unit/test_memory_budgets.py tests/unit/test_memory_digest.py tests/unit/test_spine_validate.py`
**Test results:** 248 passed (full suite, 2026-11-13, `feature/memory-budgets@e4abadb`). New `tests/unit/test_memory_budgets.py`: 19 tests. `test_memory_digest.py` stays green, so digest output is unchanged.

**Manual / external evidence:** Run by the executing agent on 2026-11-13 from `feature/memory-budgets@e4abadb`: `python3 scripts/spine_validate.py memory --project-root=<repo>`. Read-only: `git status --porcelain docs/memory` was identical before and after in every repo. Raw output: `/tmp/claude-1000/-home-juste-Workspace-ide-spine/771b6fdf-4098-4ff7-addd-151b0f91a89d/scratchpad/budgets/<repo>.txt` (session scratchpad).

| Project (branch@commit) | Exit | Warnings | Digest | Current state | Other warnings |
|---|---|---|---|---|---|
| onboarding-hub (develop@d8ba34f) | 0 | 10 | 13,553 > 8,000 (Current state 5,451; Open tasks 4,669; Logs 1,510; …) | 5,434 > 1,500 | decision-log 113,292; progress 82,399; learnings 45,333; narrative: domain-glossary 26,274, system-patterns 23,655, tech-context 12,793, design-system 7,262, product-context 5,014 |
| agenthub (develop@fc40bad) | 0 | 9 | 10,522 > 8,000 (Current state 6,580; Logs 1,747; …) | 6,563 > 1,500 | decision-log 13,112; progress 43,347; learnings 24,956; narrative: system-patterns 16,572, domain-glossary 8,339, tech-context 6,619, product-context 3,641 |
| intelligence-engine (feature/cloudflare-frontend-deploy@d788763) | 0 | 10 | OK 5,076 | OK 1,117 | decision-log 67,842; progress 66,074; learnings 16,315; narrative: system-patterns 16,574, domain-glossary 18,290, ledger/okf-integration-design 16,334, design-system 11,268, product-context 7,534, tech-context 6,815, project-brief 3,492 |
| spine (feature/memory-budgets@e4abadb) | 0 | 1 | OK 4,021 | OK 700 | progress 9,370 > 6,000 |

## Delivery summary
Harvested 2026-11-14. Delivered `spine_validate.py memory` with digest-first budgets (constants in `spine_cli/memory.py`), harvest step 4a.1, and § Memory budgets in `02-memory-bank.md`, README and AGENTS.md. Commits `2f54d3f`, `2cd6e2a`, `e4abadb`.

- **Evidence:** `pytest tests/` 248 passed (19 new). Manual read-only runs on onboarding-hub, agenthub, intelligence-engine and Spine are in the table above; `git status docs/memory` was unchanged in each.
- **Execution notes:** 3 entries. `environment` → no promotion. `decision` (hints in `BudgetCheck.detail`) → no promotion: reversible implementation detail. `out-of-scope` (3,000-char narrative budget too tight for real projects) → suggested task, folded into the per-entry ledger plan agreed with the human on 2026-11-14.
- **Learning:** none recorded (no incident or rework). Root cause / prevention / regression test: not applicable.
- **Roadmap:** I4 → Done; `/spine-roadmap --review` suggested to re-score I5/I6 against the per-entry ledger plan.
- **Memory budgets at harvest (step 4a.1):** Current state 840 / 1,500 (no compaction needed). Follow-up: `ledger/progress.md` 10,941 > 6,000, owner: the per-entry ledger task (deliveries move out of `progress.md`).
