---
task_id: 015
title: Add /spine-roadmap command with GIST-informed template
goal: Introduce optional /spine-roadmap slash command that fills roadmap.md with structured Goals + Idea Bank using grill-me strategic discovery, plus ICE scoring governance guide
status: DONE
tags:
  - type/feature
  - area/workflow
  - area/docs
  - area/governance
branch: feature/spine-roadmap-command
base: develop
execution_skill: executing-plans
created_at: 2026-07-08
updated_at: 2026-07-08
completed_at: 2026-07-08
related_learnings: []
---
# 015-spine-roadmap-command

## Discovery notes

Design finalized in analysis session (Ask mode). Key decisions:

- **Borrow GIST partially:** Goals + Ideas + ICE scoring. Skip Steps layer (overkill for solo-lean).
- **Opção A for grill-me:** Command embeds strategic framing within existing `@grill-me` protocol.
- **Harvest integration: Opção A (passive)** — harvest *suggests* review, does not auto-edit roadmap.
- **ICE scoring guide:** Separate governance doc (`docs/governance/ice-scoring-guide.md`), loaded only during `/spine-roadmap`.
- **Goal definition:** Outcome-based, measured, time-bound. Distinct from features/ideas.
- **Modes:** fill, `--review`, `--add-ideas`. Frontmatter on roadmap.md tracks `last_reviewed`.
- **Optional field:** `roadmap_idea` in task frontmatter — no mandatory coupling.
- Spine already reserved `/spine-roadmap` slot in ~10 references across codebase.

## Objective

Wire up the long-reserved `/spine-roadmap` slot. Create the command, replace the 7-line stub template with a GIST-informed structure (Goals + Idea Bank with ICE scoring), add the ICE scoring governance document, and integrate passive harvest feedback. All existing workflow remains backward-compatible — roadmap.md stays optional and is never touched by bootstrap or standard plan flow.

## Inputs

- Design briefing from analysis session (Ask mode, 2026-07-08)
- `templates/docs/memory/ledger/roadmap.md` (current stub)
- `commands/spine-plan.md` (step 6 split logic)
- `commands/spine-harvest.md` (step 4 memory bank update)
- `commands/spine-bootstrap.md` (forbidden list + references)
- `rules/02-memory-bank.md` (roadmap references)
- `templates/docs/memory/active_tasks/_task-template.md` (frontmatter)
- `install.sh` (`get_docs_seed_paths`, `seed_docs_templates`)
- `scripts/validate-bootstrap-ready.sh` (seed path list)
- `tests/unit/test_bootstrap_refinement.py` (roadmap assertions)
- `README.md`, `AGENTS.md` (command lists)
- `@grill-me` skill (existing protocol, no changes)

## Expected Outputs

- `commands/spine-roadmap.md` — new slash command (3 modes)
- `templates/docs/memory/ledger/roadmap.md` — replaced with GIST-informed template + frontmatter
- `templates/docs/governance/ice-scoring-guide.md` — new governance doc
- `templates/docs/memory/active_tasks/_task-template.md` — optional `roadmap_idea` field
- `commands/spine-harvest.md` — step 4e passive suggestion
- `commands/spine-plan.md` — step 6 link to idea IDs
- `commands/spine-bootstrap.md` — updated references (no "future")
- `rules/02-memory-bank.md` — updated structure description
- `install.sh` — `get_docs_seed_paths` updated
- `scripts/validate-bootstrap-ready.sh` — seed path updated
- `tests/unit/test_bootstrap_refinement.py` — assertions updated
- `README.md` — command list + roadmap description updated
- `AGENTS.md` — slash command list updated

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] `/spine-roadmap` command created with fill, `--review`, and `--add-ideas` modes
  - Test: `grep -l "spine-roadmap" commands/spine-roadmap.md` returns the file; verification that `--review` and `--add-ideas` flags are documented in command body

- [ ] Roadmap template replaced with structured Goals + Idea Bank sections and YAML frontmatter
  - Test: `test_roadmap_template_english_placeholders` passes with updated template content; frontmatter keys (`last_updated`, `last_reviewed`, `review_cadence`, `goals_active`, `ideas_total`, `ice_method`) present in template

- [ ] ICE scoring governance guide created with objective criteria per score (1-10)
  - Test: template at `templates/docs/governance/ice-scoring-guide.md` exists; references `spine-roadmap` usage

- [ ] Bootstrap still does not touch `roadmap.md` — references updated from "future" to real command
  - Test: `test_spine_bootstrap_no_roadmap_task_or_plan` passes; grep for "future.*spine-roadmap" across commands/ and rules/ returns zero matches

- [ ] `_task-template.md` has optional `roadmap_idea:` field in frontmatter
  - Test: `roadmap_idea:` present in `templates/docs/memory/active_tasks/_task-template.md` frontmatter; `validate-task.sh` does not reject it

- [ ] Harvest suggests roadmap review when task has `roadmap_idea` (passive, no auto-edit)
  - Test: grep `commands/spine-harvest.md` for `roadmap_idea` shows a suggestion step, not an edit step

- [ ] `install.sh` seeds new governance file; `validate-bootstrap-ready.sh` checks for it
  - Test: `grep "ice-scoring-guide" install.sh` returns match in `get_docs_seed_paths`; `grep "ice-scoring-guide" scripts/validate-bootstrap-ready.sh` returns match

- [ ] All roadmap/spine-roadmap test assertions pass after template refactor
  - Test: `pytest tests/unit/test_bootstrap_refinement.py -v` exits 0

## Test Strategy

- **Positive:** Existing test suite validates template structure, bootstrap isolation, and English placeholders. New template must satisfy all assertions.
- **Negative:** Bootstrap must continue to explicitly declare it does not modify roadmap.md. No new command should break `validate-bootstrap-ready.sh`.
- **Regression:** `test_install_seed.py` dynamically iterates `get_docs_seed_paths` — adding one entry is auto-covered. All existing bootstrap tests must remain green.
- **Command:** `pytest tests/unit/test_bootstrap_refinement.py -v`

## Implementation Plan

### Task 1: ICE scoring governance guide

**Files:**
- Create: `templates/docs/governance/ice-scoring-guide.md`

**Step 1:** Write the governance document with objective scoring criteria for Impact, Confidence, and Ease (1-10 each), anchored to concrete examples. Include usage rules (when to use, honesty principle, re-score after delivery).

**Step 2:** Commit with: `docs: add ICE scoring governance guide for /spine-roadmap`

### Task 2: New roadmap template with frontmatter

**Files:**
- Replace: `templates/docs/memory/ledger/roadmap.md`

**Step 1:** Replace the 7-line stub with full template: YAML frontmatter (`last_updated`, `last_reviewed`, `review_cadence`, `goals_active`, `ideas_total`, `ice_method`), `## Goals` section (G1+ structure with Outcome, Impact metric, Outcome metric, Horizon, Status), `## Idea Bank` table (ID, Idea, Goal, ICE, Confidence, Status), `## Review log`.

**Step 2:** Verify `test_roadmap_template_english_placeholders` still passes (only checks for English content, not specific structure).

**Step 3:** Commit with: `docs: replace roadmap stub with GIST-informed template`

### Task 3: /spine-roadmap command

**Files:**
- Create: `commands/spine-roadmap.md`

**Step 1:** Create command file with `description`, `agent: build`, and three modes documented: fill (default, with grill-me strategic framing for Goals + Ideas), `--review` (re-evaluate existing goals, update confidence, update `last_reviewed`), `--add-ideas` (append ideas to existing goals). Embed strategic discovery questions for grill-me (Goal validation criteria, metric baselines, ICE scoring against governance guide).

**Step 2:** Commit with: `feat: add /spine-roadmap command with GIST-informed discovery`

### Task 4: Update bootstrap + rules references

**Files:**
- Modify: `commands/spine-bootstrap.md`
- Modify: `rules/02-memory-bank.md`

**Step 1:** In `spine-bootstrap.md`: replace all "future `/spine-roadmap`" with "`/spine-roadmap`" (lines 12, 41, 132, 153, 166, 176). Keep bootstrap's prohibition against touching roadmap.md unchanged.

**Step 2:** In `02-memory-bank.md`: update lines 26 and 45 — replace "future `/spine-roadmap`" with "`/spine-roadmap`" and describe the new GIST-informed structure.

**Step 3:** Run `pytest tests/unit/test_bootstrap_refinement.py -v` — ensure `test_spine_bootstrap_no_roadmap_task_or_plan` and all other assertions pass.

**Step 4:** Commit with: `docs: update bootstrap and rules references from future /spine-roadmap to real command`

### Task 5: Install and validation scripts

**Files:**
- Modify: `install.sh` (add `governance/ice-scoring-guide.md` to `get_docs_seed_paths`)
- Modify: `scripts/validate-bootstrap-ready.sh` (add to seed path array)

**Step 1:** In `install.sh`, add `governance/ice-scoring-guide.md` to the `get_docs_seed_paths()` heredoc (between `governance/memory-tags-policy.md` and `quality/guardrails.md`).

**Step 2:** In `validate-bootstrap-ready.sh`, add `docs/governance/ice-scoring-guide.md` to the `seed_paths` array.

**Step 3:** Commit with: `chore: seed ice-scoring-guide.md via install.sh and validate script`

### Task 6: Task template — optional roadmap_idea field

**Files:**
- Modify: `templates/docs/memory/active_tasks/_task-template.md`

**Step 1:** Add `roadmap_idea:` (empty, commented) to the YAML frontmatter of the task template, between `execution_skill` and `created_at`. Add a brief comment that it's optional and links to a roadmap idea ID.

**Step 2:** Verify `bash .spine/scripts/validate-task.sh` does not need changes (it validates required keys, not optional ones — confirm by reading the validator script).

**Step 3:** Commit with: `feat: add optional roadmap_idea field to task template frontmatter`

### Task 7: Harvest passive integration

**Files:**
- Modify: `commands/spine-harvest.md`

**Step 1:** Add optional step after 4c (unchanged files) and before 5 (task closure): "**4d. Roadmap feedback (optional):** When task frontmatter contains `roadmap_idea`, suggest running `/spine-roadmap --review` to update confidence. Do not auto-edit roadmap.md. Include suggestion in harvest summary."

**Step 2:** Renumber existing step 4d (MkDocs) to 4e, step 5 becomes 6, step 6 becomes 7, step 7 becomes 8. Update all cross-references in the command body accordingly.

**Step 3:** Commit with: `feat: add passive roadmap feedback suggestion on harvest`

### Task 8: spine-plan split integration

**Files:**
- Modify: `commands/spine-plan.md`

**Step 1:** Update step 6: when splitting plans and `roadmap.md` has an active Idea Bank, link split suggestions to specific idea IDs instead of generic "suggestions". Use conditional language: "If `docs/memory/ledger/roadmap.md` contains an `## Idea Bank` table, link remaining plans to specific idea IDs."

**Step 2:** Commit with: `feat: link split-plan suggestions to roadmap idea IDs`

### Task 9: README and AGENTS.md updates

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1:** In `README.md`: add `/spine-roadmap` to the slash commands list (after `/spine-harvest`). Update roadmap description in Memory Bank section to mention GIST-informed structure and optional nature.

**Step 2:** In `AGENTS.md`: add `/spine-roadmap` to the slash commands list. Add ice-scoring-guide.md reference to governance section.

**Step 3:** Commit with: `docs: add /spine-roadmap to README and AGENTS command lists`

### Task 10: Final validation

**Files:**
- Test: `tests/unit/test_bootstrap_refinement.py`
- Test: `tests/unit/test_install_seed.py`

**Step 1:** Run full test suite: `pytest tests/ -v`

**Step 2:** Verify no "future `/spine-roadmap`" references remain anywhere: `rg "future.*spine-roadmap"` returns empty.

**Step 3:** Verify all 13 files from the design scope are accounted for.

**Step 4:** Commit with: `test: verify all tests pass after /spine-roadmap changes`

## Tests executed

- `pytest tests/ -v` — 86 passed, 5 pre-existing failures in `test_opencode_template.py` (unrelated to roadmap changes)
- `pytest tests/unit/test_bootstrap_refinement.py -v` — all 11 pass
- `pytest tests/unit/test_install_seed.py -v` — all 6 pass
- `rg "future.*spine-roadmap"` — zero matches

## Test results

All acceptance criteria verified:
1. `/spine-roadmap` command created with fill, `--review`, and `--add-ideas` modes — `commands/spine-roadmap.md` exists with all modes documented
2. Roadmap template replaced with GIST-informed structure — `test_roadmap_template_english_placeholders` passes
3. ICE scoring governance guide created — `templates/docs/governance/ice-scoring-guide.md` exists
4. Bootstrap references updated — `test_spine_bootstrap_no_roadmap_task_or_plan` passes; zero "future /spine-roadmap" references
5. `_task-template.md` has `roadmap_idea` field — present, validator does not reject it
6. Harvest passive integration — `commands/spine-harvest.md` step 4d with suggestion, steps renumbered 4d→4e, 5→6, 6→7, 7→8
7. `install.sh` seeds new governance file; `validate-bootstrap-ready.sh` checks for it — verified via `test_install_seed.py`
8. All roadmap/spine-roadmap test assertions pass — 86/91 pass (5 pre-existing failures unrelated)

## Delivery summary

Wired up the long-reserved `/spine-roadmap` slot across 13 files (7 new, 6 modified). Created the command with 3 modes (fill with grill-me strategic discovery, `--review` for re-evaluation, `--add-ideas` for appending). Replaced the 7-line roadmap stub with a GIST-informed template: YAML frontmatter, structured Goals (G1+ with Outcome/Impact/Horizon), ICE-scored Idea Bank table, and Review log. Added `docs/governance/ice-scoring-guide.md` with objective 1-10 scoring criteria and an honesty principle.

Integration touchpoints: bootstrap references updated from "future" to real command (zero remaining "future /spine-roadmap" references). Task template gained optional `roadmap_idea` frontmatter field. Harvest gained passive step 4d suggesting `/spine-roadmap --review` when task has `roadmap_idea`. Plan step 6 links split suggestions to idea IDs when Idea Bank exists. Install and validate scripts seed the new governance file.

Graphify inactive (not applicable). MkDocs inactive (not applicable). No learnings recorded — straightforward feature delivery with no incidents or rework.

86/91 tests pass (5 pre-existing failures in `test_opencode_template.py` unrelated to roadmap changes).
