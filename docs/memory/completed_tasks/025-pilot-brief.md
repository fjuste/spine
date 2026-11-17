---
task_id: 025
title: Pilot brief — where the project is and what to do next, without asking the agent
goal: "`spine.py brief` prints project state, recent story with why, what waits on the human and the next command; any agent shows it verbatim when the pilot asks"
status: DONE
tags:
  - type/feature
  - area/memory
  - area/workflow
  - stack/python
branch: feature/pilot-brief
base: develop
execution_skill: executing-plans
roadmap_idea: I15
created_at: 2026-11-16
updated_at: 2026-11-16
completed_at: 2026-11-16
related_learnings: []
---

# 025-pilot-brief

## Discovery notes

Discovery session with the pilot on 2026-11-16 (topic 5 of the personal idea list "session start, help for the pilot").

- **Problem:** at every session start or project resume the pilot asks the agent "where are we and what is next?". That costs a round of tokens and time. The roadmap holds the plan, not the story.
- **Diagnosis:** the facts already exist but are spread and written for agents. `progress.md` Current state uses agent shorthand (idea IDs, ICE scores) and `Next:` lists about 8 items with no single recommendation. The timeline lives in `ledger/deliveries/INDEX.md`. Live state (branch, uncommitted changes, task waiting in REVIEW) lives in no file.
- **Resolved with the pilot:**
  1. Format: terminal output (script), not a committed file. A committed file goes stale when someone commits without harvest and creates merge noise.
  2. Story: timeline of recent deliveries plus a minimal why per delivery, with links to the files to dig deeper.
  3. Session start: first considered a Claude Code `SessionStart` hook. **Replaced by a rule instruction** (pilot's call, 2026-11-16): agents run `spine.py brief` and show its output verbatim when the pilot asks where the project stands or what to do next. Works in every agent (Cursor, OpenCode, Claude Code, Antigravity), needs no installer change, and avoids the unconfirmed hook display (below). The pilot can still run the script in the terminal for zero tokens.
  4. Language: memory and documentation stay in English. The pilot's communication language belongs to the separate config-file idea; the brief labels stay English until then.
- **Roadmap:** folded into I15 (rescoped from a chat-only summary block; re-scored 216).
- **Why not a hook** (Claude Code hooks reference, code.claude.com/docs/en/hooks.md, checked 2026-11-16): plain stdout of a `SessionStart` hook goes to Claude's context and is not documented as shown to the user; `systemMessage` is "shown to the user" but not confirmed for `SessionStart`. A hook would also be Claude-only. Revisit with I12 (hook runtime) if the pilot wants the brief without asking.
- **Out of scope (v1):** session hooks in any agent (I12), injecting the digest at session start (I11), localized labels (config-file idea), detecting unresolved `deviation` notes in IN_PROGRESS tasks, `why:` backfill for existing deliveries.

## Objective

Give the human pilot a zero-token view of the project before calling the agent. `python3 .spine/scripts/spine.py brief` reads `docs/memory/` and git and prints four sections:

- **Where we are:** project, branch, clean or dirty tree, active goal (arc), open IN_PROGRESS tasks.
- **Recent story:** newest deliveries with date, title, an optional one-line `why:` and a link to the entry.
- **Waiting on you:** REVIEW tasks (run `/spine-harvest`) and the open-task warnings of `check_open_tasks`.
- **Next step:** one recommended action and the exact command to type, plus alternatives.

The recommendation is written by the agent once per cycle as structured fields in `progress.md` frontmatter (`/spine-harvest`, `/spine-plan`); everything else is computed. Rule 01 tells every agent to run the brief and show it verbatim when the pilot asks where the project stands or what is next, instead of composing that answer from memory files.

## Inputs

- `scripts/spine_cli/memory.py` (`read_frontmatter`, `collect_entries`, `LedgerEntry`, `check_open_tasks`, `open_tasks`, `_section`)
- `scripts/spine.py` (subcommand registration)
- `rules/01-core-protocol.md`
- `templates/docs/memory/ledger/progress.md`, `templates/docs/memory/ledger/deliveries/_template.md`
- `commands/spine-harvest.md` (step 4a), `commands/spine-plan.md`
- `docs/memory/ledger/roadmap.md` (Goals, Idea Bank `Goal` column)

## Expected Outputs

- New module `scripts/spine_cli/brief.py` and subcommand `spine.py brief`
- Optional `why:` in delivery entries (template + `LedgerEntry`)
- `progress.md` frontmatter fields `next_step`, `next_command`, `next_alternatives` (template + digest)
- Pilot-brief instruction in `rules/01-core-protocol.md`
- Updated `commands/spine-harvest.md`, `commands/spine-plan.md`, `rules/02-memory-bank.md`, `README.md`, `AGENTS.md`
- Spine's own `progress.md` carries the new fields (dogfooding)
- Tests under `tests/unit/test_pilot_brief.py`

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] **AC1 — Brief sections.** `spine.py brief [--project-root=PATH]` prints, in order, a header (project directory name, branch, `clean tree` or `N uncommitted changes`, today), `WHERE WE ARE`, `RECENT STORY` (newest 5 deliveries: `MM-DD  title`), `WAITING ON YOU` and `NEXT STEP`, and exits 0. Without git the header says `no git`; an empty section prints `nothing` instead of disappearing; a missing `docs/memory/` exits 1 with a hint to run `spine.py install`.
  - Test: fixture bank with 7 deliveries, one IN_PROGRESS, one REVIEW and one statusless task → the five sections in order, 5 story lines newest first, REVIEW task under WAITING with `/spine-harvest`, statusless warning under WAITING; separate tests for a non-git root and a missing memory dir.
- [ ] **AC2 — Arc.** `WHERE WE ARE` shows the active arc: the `roadmap_idea` of the newest IN_PROGRESS task, else of the newest delivered task, mapped through the Idea Bank `Goal` column to the goal heading in `roadmap.md` (`G1: Lean context`). When any link is missing (no roadmap, no `roadmap_idea`, unknown ID), the arc line is omitted, never guessed.
  - Test: fixture roadmap with G1/G2 and I3→G1; task with `roadmap_idea: I3` → `Arc: G1 — Lean context`; tests for each missing link → no arc line.
- [ ] **AC3 — Why per delivery.** Delivery entries accept an optional one-line `why:` frontmatter field (template documents it, at most 120 chars). The story prints it under its delivery as `why: …`, capped at 120 chars with `…`; entries without `why:` print only the title line.
  - Test: one entry with `why:`, one without, one with a 200-char `why:` → indented why line, no why line, capped line.
- [ ] **AC4 — Links.** When stdout is a terminal, each delivery title, task and the roadmap goal are OSC 8 hyperlinks to the absolute file path; otherwise (pipe, agent tool call) a plain relative path follows the item (`→ docs/memory/ledger/deliveries/….md`). No escape sequence ever appears in non-terminal output.
  - Test: render with `is_tty=True` → `\x1b]8;;file://…` present; `is_tty=False` → no `\x1b`, relative paths present.
- [ ] **AC5 — Structured next step.** `progress.md` frontmatter holds `next_step` (one line), `next_command` (what the pilot types) and `next_alternatives` (YAML list). `NEXT STEP` prints them as step, `→ type:  <command>` and `Alternatives: a · b`. When the fields are missing it prints the `Next:` bullet of Current state and the hint `ask the agent to run /spine-harvest to record a next step`. The digest prints `Next step: <next_step> — <next_command>` as the first line of its Current state section when set. The `progress.md` template seeds the fields; `/spine-harvest` step 4a and `/spine-plan` (after the approval gate is answered) write them; rule 02 documents them.
  - Test: progress with fields → three lines; without fields → `Next:` bullet + hint; digest test for the first Current state line; a test that harvest and plan command texts name the three fields.
- [ ] **AC6 — Agents show the brief on request.** `rules/01-core-protocol.md` instructs: when the pilot asks where the project stands, what is next, or resumes after a break, run `python3 .spine/scripts/spine.py brief` and show its output verbatim (as a code block), then add at most two lines of the agent's own; do not rebuild that answer from memory files. If the command fails, fall back to the digest's Current state and suggest `spine.py update`. Agent-invoked output is non-terminal, so it carries plain relative paths the agent can open (AC4).
  - Test: rule text test (instruction, command, verbatim, fallback present); `brief` output through a pipe has no `\x1b`.
- [ ] **AC7 — Docs and dogfooding.** `README.md`, `AGENTS.md` and `rules/02-memory-bank.md` describe `spine.py brief`, the `why:` field, the next-step fields and the agent instruction; Spine's own `progress.md` carries the three fields and `spine.py brief` runs clean on this repo; `pytest tests/` passes.
  - Test: doc-presence tests in the style of existing `test_memory_*` doc checks; manual run recorded in `## Execution evidence`.

## Test Strategy

- Positive: fixture memory banks built in `tmp_path` (pattern from `tests/unit/test_memory_open_tasks.py` and `test_memory_digest.py`); git state via a temp `git init` repo.
- Negative: no git, no `docs/memory/`, no roadmap, missing frontmatter fields, unknown idea IDs, non-terminal output.
- Regression: existing digest, budget and open-task tests stay green; `progress.md` frontmatter must not break `_section` Current state extraction or the progress budget check.
- Manual: final run of `spine.py brief` on this repo and in one local consumer bank; one agent session asking "where are we?" to confirm the rule is followed.
- Command: `pytest tests/`

## Implementation Plan

### Task 1: Brief core (AC1, AC2, AC3)

**Files:** Create `scripts/spine_cli/brief.py`; modify `scripts/spine_cli/memory.py` (`LedgerEntry.why`), `scripts/spine.py`, `templates/docs/memory/ledger/deliveries/_template.md`; test `tests/unit/test_pilot_brief.py`.

**Step 1:** Failing tests for sections, arc, why. **Step 2:** Implement reusing `collect_entries`, `open_tasks`, `check_open_tasks`, `read_frontmatter`. **Step 3:** Commit.

### Task 2: Links (AC4)

**Files:** `scripts/spine_cli/brief.py`; tests in `test_pilot_brief.py`.

**Step 1:** Failing tests for tty and non-tty rendering. **Step 2:** Implement an `is_tty` render switch. **Step 3:** Commit.

### Task 3: Structured next step (AC5)

**Files:** `templates/docs/memory/ledger/progress.md`, `scripts/spine_cli/memory.py` (digest), `scripts/spine_cli/brief.py`, `commands/spine-harvest.md`, `commands/spine-plan.md`, `rules/02-memory-bank.md`.

**Step 1:** Failing tests. **Step 2:** Implement and edit commands. **Step 3:** Commit.

### Task 4: Agent instruction (AC6)

**Files:** `rules/01-core-protocol.md`; tests in `test_pilot_brief.py`.

**Step 1:** Failing rule-text test. **Step 2:** Add the instruction (short; rules load every session). **Step 3:** Commit.

### Task 5: Docs and dogfooding (AC7)

**Files:** `README.md`, `AGENTS.md`, `rules/02-memory-bank.md`, `docs/memory/ledger/progress.md`.

**Step 1:** Doc tests. **Step 2:** Write docs; add the fields to Spine's `progress.md`; run `spine.py brief` here and on one consumer bank; record evidence. **Step 3:** `pytest tests/`; commit.

## Execution notes
- 2026-11-16 — deviation — AC4 link rendering (`is_tty` switch, OSC 8 vs trailing relative path) landed in the Task 1 commit because `build_brief` needs the render mode in its signature; Task 2 tests were written afterwards and passed on first run (not red first). Scope unchanged. → no promotion
- 2026-11-16 — decision — `/spine-harvest` step 4a also asks for the delivery `why:` (not only the template): without it no new delivery would ever carry the field the brief prints. `read_next_step` lives in `memory.py` because both the digest and the brief read it. → no promotion
- 2026-11-16 — out-of-scope — RECENT STORY reads only `ledger/deliveries/` entries: a consumer bank that still keeps its delivery history in the legacy `progress.md` delivery log shows `nothing` there until `spine.py memory migrate --apply`. A one-line hint in the story (legacy log present → run migrate) would help those banks; not done. → Known Opportunities
- 2026-11-16 — out-of-scope — the 7 legacy tasks 008–014 without `status:` fill WAITING ON YOU on this repo (from `check_open_tasks`); closing them is the pilot's decision, already in Current state Next. → no promotion

## Execution evidence
**Tests executed:**
- `pytest tests/` (full suite)
- `pytest -q tests/unit/test_pilot_brief.py` (37 tests: AC1–AC7)
- `python3 scripts/spine_validate.py memory` and `python3 scripts/spine_validate.py task docs/memory/active_tasks/025-pilot-brief.md`

**Test results:** 379 passed (full suite, was 361 before the task); pilot-brief tests 37 passed; memory validator exit 0 with the one pre-existing warning (7 legacy tasks 008–014 without status); task contract OK.

**Manual / external evidence:** run by the agent on 2026-11-16, branch `feature/pilot-brief` (commits a882173…25cbc50):
- `python3 scripts/spine.py brief` on this repo: exit 0; arc `G5 — Lower review load`, task 025 in progress, 5 deliveries, the legacy-task warning, NEXT STEP from the new `progress.md` fields. The digest prints `Next step: … — …` as the first Current state line.
- Same command under a pseudo-terminal (`script -qc`): delivery, task and roadmap items are OSC 8 `file://` links; through a pipe, plain `→ docs/memory/…` paths and no escape bytes.
- `spine.py brief --project-root=<a local consumer project>` (read-only): exit 0; no per-entry deliveries yet (legacy delivery log), so the story prints `nothing`, WAITING ON YOU lists 2 DONE tasks left in `active_tasks/`, NEXT STEP falls back to the `Next:` bullet plus the hint. Raw output was not kept (it names a private project).
- Pending for the pilot: one fresh agent session asking "where are we?" to confirm rule 01 is followed (the rule is wired from this working tree).

## Delivery summary

- **Delivered:** `spine.py brief` (header, WHERE WE ARE with arc, RECENT STORY with `why:`, WAITING ON YOU, NEXT STEP; OSC 8 links on a terminal, relative paths otherwise); `next_step` / `next_command` / `next_alternatives` in `progress.md` frontmatter, written by harvest and plan and shown first in the digest's Current state; delivery `why:` field; rule 01 instruction to show the brief verbatim; README, AGENTS.md and rule 02 docs. Delivery entry: `ledger/deliveries/2026-11-16-025-pilot-brief.md`.
- **Evidence:** `pytest tests/` 379 passed (37 new tests) at execution and at harvest; manual runs on this repo, a pseudo-terminal and a local consumer bank (see Execution evidence). Pending: a fresh agent session asking "where are we?" to confirm rule 01.
- **Execution notes routing:** `deviation` (links landed with Task 1) → no promotion (one-off ordering, no planning gap); `decision` (harvest asks for `why:`; `read_next_step` in `memory.py`) → no promotion (easy to reverse); `out-of-scope` legacy delivery log hint → Known Opportunities; `out-of-scope` legacy tasks 008–014 → no promotion (already in Current state). Discovery decision (on-demand script + rule, not a committed file or hook) → `DEC 2026-11-16-pilot-brief-on-demand-script`.
- **Learning:** no incident or rework; no learning entry.
- **Roadmap:** I15 Done.
