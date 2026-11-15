---
task_id: 018
title: Memory digest — summary-first Core SYNC for growing memory banks
goal: Core SYNC loads a generated digest of a few thousand tokens instead of every global file, the whole progress.md and every open task body, with a transparent one-time setup for existing projects
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/memory-digest
base: develop
execution_skill: executing-plans
roadmap_idea: I3
created_at: 2026-11-11
updated_at: 2026-11-12
completed_at: 2026-11-12
related_learnings: []
---

# 018-memory-digest

## Discovery notes

`@grill-me` ran on 2026-11-11. Sources: `docs/documentation/evolucao/hooks-and-summaries.md` §2, roadmap I1–I3.

**Baseline (measured 2026-11-11, chars loaded by today's Core SYNC):**

| Project | global/ + progress.md | Open task bodies | Total | ≈ tokens |
|---|---|---|---|---|
| onboarding-hub (worst case) | ~263k (decision-log 108k, progress 80k) | 166k (19 tasks, 18 `PLANNING`) | ~429k | ~107k |
| intelligence-engine | ~201k | 11k | ~212k | ~53k |
| agenthub | ~95k | 36k | ~131k | ~33k |

"Read only Current state" is not enforceable: the agent opens the whole `progress.md` (80k) to get a 4.8k section.

**Resolved decisions:**

1. **Scope = digest core.** This task folds in I1 (repeatable baseline via `memory stats`) and I2 (summary frontmatter). Budgets (I4), indexes (I5) and archive (I6) are follow-up tasks.
2. **Transparent setup.** No separate migration step. The first session after a Spine update finds missing summaries through the digest and writes them itself. If the script is missing (old `.spine`), the agent falls back to the legacy Core SYNC and suggests `python3 .spine/scripts/spine.py update`.
3. **Paced setup.** Missing summaries are flagged largest-first, up to a source budget of 60,000 chars per session; the rest are deferred to the next sessions.
4. **Two file kinds** (keeps setup inside the budget and avoids summarizing 108k logs):
   - *Narrative files* (`global/*.md` except `decision-log.md`; unknown `ledger/*.md`): agent-written `summary:` frontmatter, outline fallback when missing.
   - *Log files* (`decision-log.md`, `progress.md`, `learnings.md`): deterministic — entry count + newest 5 entry titles; `progress.md` also contributes its `## Current state` block. No agent summary needed. `roadmap.md` stays Extended tier (one line in the digest).
5. **Tasks use existing frontmatter** (`task_id`, `status`, `title`, `goal`). No new task `summary:` field (YAGNI).
6. **Digest goes to stdout only.** No committed `digest.md`: no staleness, no merge conflicts (G4), no gitignore entry. Hooks (I11) will call the same command later.

**Out of scope (review comment, 2026-11-11):** automatic ingestion of the digest at session start and before compaction, so the agent no longer decides whether to run it, belongs to I11 (hook runtime I12). In this task the *content* is already deterministic (the script chooses what goes into the digest and which summaries are missing); only *triggering* it is still a rule the agent follows. Writing a missing summary stays with the agent: it is semantic work no script can do.

## Objective

Add a stdlib-only `memory` subcommand to `scripts/spine.py` (module `scripts/spine_cli/memory.py`) with two actions:

- `memory stats`: per-file char counts, today's Core SYNC total and the digest size, so the gain is measurable on any project.
- `memory digest`: prints a compact, deterministic view of the memory bank (Current state, one line per open task, narrative summaries or outline fallback, log counts and newest titles) plus a `SETUP:` block listing missing summaries within the session budget.

Change the Core SYNC contract in `rules/02-memory-bank.md` to digest-first: run the digest, open full files only when the task needs them, do the SETUP work when flagged, and keep `summary:` current when editing a narrative file. Seed `summary:` frontmatter in the narrative global templates and have `/spine-bootstrap` fill it.

## Inputs

- `docs/documentation/evolucao/hooks-and-summaries.md` §2
- `scripts/spine.py`, `scripts/spine_cli/` (CLI patterns, `Options`, `log.py`)
- `scripts/spine_validate.py` (`read_text`, frontmatter regex style)
- `rules/02-memory-bank.md` (Tiered SYNC), `rules/01-core-protocol.md`
- `templates/docs/memory/global/*.md`, `commands/spine-bootstrap.md`
- Worst-case fixture shape: onboarding-hub `docs/memory/` (read-only)

## Expected Outputs

- `scripts/spine_cli/memory.py` (new): frontmatter reader, file classification, stats, digest, setup selection
- `scripts/spine.py`: `memory` subparser (`stats`, `digest`; `--project-root`, `--budget`)
- `templates/docs/memory/global/{project-brief,product-context,domain-glossary,system-patterns,tech-context}.md`: `summary:` frontmatter placeholder
- `rules/02-memory-bank.md`: Core tier rewritten digest-first with legacy fallback; summary maintenance rule
- `rules/01-core-protocol.md`: step 1 points to the digest
- `commands/spine-bootstrap.md`: fill `summary:` for each narrative file it writes
- `tests/unit/test_memory_digest.py` (new); updates to template/rule text tests if they assert old Core wording
- `README.md` + `AGENTS.md`: `memory stats|digest` usage, one short section

## Acceptance Criteria (verifiable, TDD-ready)

- [x] `spine.py memory stats` prints chars per memory file, the legacy Core SYNC total (global + whole `progress.md` + open task bodies) and the digest size, and exits 0.
  - Test: `test_stats_reports_legacy_core_total_and_digest_size` on a `tmp_path` fixture with known file sizes.
- [x] `spine.py memory digest` prints, in order: `## Current state` (from `progress.md`), `## Open tasks` with one line per task `NNN | STATUS | title — goal` (`IN_PROGRESS`/`REVIEW` first, then by id), narrative file summaries, and log lines (entry count + newest 5 titles for `decision-log`, `progress` delivery log and `learnings`). No task body text appears.
  - Test: `test_digest_sections_order_and_one_line_per_task`, `test_digest_never_includes_task_body`, `test_log_files_show_count_and_newest_five_titles` (covers `### ` heading logs and Spine's table-row decision log).
- [x] A narrative file without `summary:` shows a capped outline (its `##` headings, ≤ 600 chars) marked `summary missing`; a file with `summary:` (plain or `>-` folded block) shows the summary.
  - Test: `test_missing_summary_falls_back_to_capped_outline`, `test_folded_block_summary_is_parsed`.
- [x] When summaries are missing, the digest ends with a `SETUP:` block listing files largest-first whose cumulative size fits `--budget` (default 60,000 chars), states how many files are deferred, and tells the agent to write `summary:` (≤ 5 lines) for the listed files only. No block when nothing is missing.
  - Test: `test_setup_block_respects_budget_largest_first`, `test_no_setup_block_when_all_summaries_present`.
- [x] Missing `docs/memory/`, missing files, empty dirs, BOM/CRLF content and `_task-template.md` are handled without a traceback (stdlib only, Python 3.9+).
  - Test: `test_digest_tolerates_missing_and_legacy_files`, `test_task_template_is_ignored`.
- [x] Narrative global templates carry a `summary:` frontmatter placeholder; `rules/02-memory-bank.md` Core tier is digest-first with the legacy list kept as the fallback when the script is unavailable, includes the SETUP and summary-maintenance rules; `rules/01-core-protocol.md` and `commands/spine-bootstrap.md` reference them.
  - Test: `test_narrative_templates_have_summary_frontmatter`, `test_memory_bank_rule_core_tier_is_digest_first`, plus existing `test_memory_bank_v21.py` / `test_task_contract_alignment.py` still green.
- [x] On the worst-case project the digest is ≤ 20,000 chars (vs ~429k legacy) before any summary is written, and `memory stats` numbers are recorded as manual evidence.
  - Test: manual run `python3 scripts/spine.py memory stats --project-root=<onboarding-hub>` (read-only; nothing written to that repo).

## Test Strategy

- **Positive:** fixture memory bank in `tmp_path` with narrative files (with and without `summary:`), log files in both heading and table formats, open tasks in mixed statuses.
- **Negative:** no `docs/memory/`; empty `active_tasks/`; malformed frontmatter (no closing `---`); task file without `goal`.
- **Regression:** full suite — `test_memory_bank_v21.py`, `test_task_contract_alignment.py`, `test_install_seed.py`, `test_spine_cli.py` must stay green (template frontmatter must not break seed/bootstrap checks).
- **Manual evidence:** `memory stats` and `memory digest | wc -c` on onboarding-hub, agenthub and intelligence-engine (read-only).
- **Command:** `pytest -v tests/`

## Implementation Plan

### Task 1: Frontmatter reader and file classification

**Files:**
- Create: `scripts/spine_cli/memory.py`
- Test: `tests/unit/test_memory_digest.py`

**Step 1:** Write failing tests for `read_frontmatter` (plain value, `>-`/`|` block, no frontmatter, unclosed frontmatter) and `classify(path)` → `narrative | log | task | ignored`.
**Step 2:** Implement with `re` only; reuse the `read_text` behavior (BOM, CRLF) — import from `spine_validate` only if it does not create a circular import, otherwise a local helper.
**Step 3:** Commit `feat(memory): frontmatter reader and memory file classification`.

### Task 2: Digest sections

**Files:**
- Modify: `scripts/spine_cli/memory.py`
- Test: `tests/unit/test_memory_digest.py`

**Step 1:** Failing tests for section order, one line per task (status ordering), Current state extraction, log count + newest 5 (heading and table formats), outline fallback cap.
**Step 2:** Implement `build_digest(root) -> str` with named constants (`NEWEST_LOG_TITLES = 5`, `OUTLINE_MAX_CHARS = 600`).
**Step 3:** Commit `feat(memory): generate summary-first digest`.

### Task 3: Paced SETUP block

**Step 1:** Failing tests for budget selection largest-first, deferred count, no block when complete.
**Step 2:** Implement `select_setup(files, budget)`; `DEFAULT_SETUP_BUDGET_CHARS = 60_000`.
**Step 3:** Commit `feat(memory): paced one-time summary setup`.

### Task 4: Stats and CLI wiring

**Files:**
- Modify: `scripts/spine.py`
- Test: `tests/unit/test_memory_digest.py`, `tests/unit/test_spine_cli.py`

**Step 1:** Failing tests for `memory stats` totals and `main(["memory", "digest", "--project-root", ...])` exit 0.
**Step 2:** Add `memory` subparser with `stats`/`digest`, `--project-root`, `--budget`.
**Step 3:** Commit `feat(memory): spine.py memory stats and digest commands`.

### Task 5: Templates, rules, bootstrap, docs

**Files:**
- Modify: 5 narrative templates under `templates/docs/memory/global/`, `rules/02-memory-bank.md`, `rules/01-core-protocol.md`, `commands/spine-bootstrap.md`, `README.md`, `AGENTS.md`

**Step 1:** Failing text tests (template frontmatter, digest-first Core tier, fallback wording).
**Step 2:** Edit files. Core tier text: run `python3 .spine/scripts/spine.py memory digest`; open full files only when the task touches them; if `SETUP:` appears, write those summaries first; if the command fails, use the legacy list and suggest `spine.py update`. Summary rule: when editing a narrative file, update its `summary:` (≤ 5 lines).
**Step 3:** Run full suite; commit `docs(memory): digest-first Core SYNC and summary frontmatter`.

### Task 6: Worst-case evidence

**Step 1:** Run `memory stats` and `memory digest` against onboarding-hub, agenthub, intelligence-engine (`--project-root`, read-only).
**Step 2:** Record numbers in `## Execution evidence`; confirm digest ≤ 20,000 chars on onboarding-hub.

## Execution notes

- 2026-11-11 — decision — `classify()` returns a fifth kind, `extended`, for `ledger/roadmap.md` (plan listed four). The digest prints roadmap as one Extended-tier line and stats keep it out of the legacy Core total; a separate kind makes that explicit instead of overloading `ignored`. → no promotion
- 2026-11-11 — decision — Local `read_text` helper in `memory.py` instead of importing `spine_validate`: avoids coupling the installer package to the validator script for a three-line function. → no promotion
- 2026-11-11 — decision — `select_setup` skips a file that would overflow the budget and keeps trying smaller ones; when no file fits (one narrative file larger than the budget), it selects the largest alone so setup never stalls. → no promotion
- 2026-11-11 — decision — A `summary:` value starting with `[Fill in` counts as missing, so the seeded template placeholder triggers SETUP like an absent field. Summaries are capped at 800 chars in the digest so one oversized summary cannot inflate every session. → no promotion
- 2026-11-11 — decision — Tasks 2 and 3 landed in one commit (`feat(memory): generate summary-first digest with paced one-time setup`): `build_digest` renders the SETUP block, so the two shared one test/implementation cycle. → no promotion
- 2026-11-11 — decision — `memory` takes the action as a positional choice (`stats` | `digest`) rather than nested subparsers; the command line is the same (`spine.py memory stats`) with less parser code. Project root resolves like the other commands (`--project-root`, else git toplevel); a missing root exits 1. → no promotion
- 2026-11-11 — decision — Open tasks are files under `active_tasks/` matching `^\d{3}-` whose status is not `DONE`; a `DONE` file left behind is neither listed nor counted in the legacy total. Log entries are ordered by the ISO date (or `LEARN-NNN`) in their title, so the newest-first heading logs and Spine's chronological table-row decision log both show their newest five. → no promotion
- 2026-11-11 — environment — The plan's commands assumed `intelligence-engine` and `agenthub` were siblings of the worst-case project; they live in other workspace folders. → no promotion
- 2026-11-11 — out-of-scope — The Spine repo's own `docs/memory/ledger/progress.md` still uses the pre-v2.1 layout (no `## Current state`), so its digest reports that section as missing. Restructuring it belongs to Spine memory maintenance, not this task. → no promotion (resolved at harvest: `## Current state` added to progress.md)

## Execution evidence

**Tests executed:**
- `python3 -m pytest -q tests/unit/test_memory_digest.py` (after each task, red then green)
- `python3 -m pytest -q tests/` (full suite after Tasks 4 and 5)

**Test results:** 222 passed, 0 failed (`tests/unit/test_memory_digest.py`: 52 tests). `test_memory_bank_v21.py`, `test_task_contract_alignment.py`, `test_install_seed.py` and `test_spine_cli.py` still pass.

**Manual / external evidence:** run by the agent (Claude Code) on 2026-11-11, branch `feature/memory-digest` at `b1ea53f`, read-only (`git status docs/memory` clean in every target repo afterwards). Commands: `python3 scripts/spine.py memory stats --project-root=<repo>` and `python3 scripts/spine.py memory digest --project-root=<repo> | wc -c`. No summaries written yet in any project.

| Project | Legacy Core SYNC (chars) | Digest (chars) | Reduction | SETUP this session |
|---|---|---|---|---|
| onboarding-hub | 421,762 (≈ 105k tokens) | 13,039 | 97% | 3 files listed, 3 deferred |
| intelligence-engine | 209,066 (≈ 52k tokens) | 5,076 | 98% | 4 listed, 3 deferred |
| agenthub | 129,093 (≈ 32k tokens) | 10,522 | 92% | 5 listed, 0 deferred |

Acceptance target met: onboarding-hub digest 13,039 chars ≤ 20,000. Raw output was saved to the session scratchpad (`/tmp/claude-1000/-home-juste-Workspace-ide-spine/96cdb8fd-63dd-4c8d-b1c8-a8f62492b50c/scratchpad/<project>-{stats,digest}.txt`, temporary); rerun the commands above to reproduce.

## Delivery summary

Delivered 2026-11-12 on `feature/memory-digest` (commits `8a3f955`, `bf51c83`, `31a856e`, `b1ea53f`, plus the harvest commit).

- **What shipped:** `spine.py memory stats|digest` (`scripts/spine_cli/memory.py`); digest-first Core tier with legacy fallback and § Narrative summaries in `rules/02-memory-bank.md`; `01-core-protocol.md` step 1; `/spine-bootstrap` fills `summary:`; `summary:` placeholder in the 5 narrative templates; README/AGENTS.md usage.
- **Evidence (from § Execution evidence):** `pytest -q tests/` 222 passed (52 new). Read-only manual runs on 2026-11-11 at `b1ea53f`: onboarding-hub 421,762 → 13,039 chars (97%), intelligence-engine 209,066 → 5,076 (98%), agenthub 129,093 → 10,522 (92%). Acceptance target (≤ 20,000 on the worst case) met.
- **Execution notes routing:** 7 `decision` notes → no promotion (implementation-level, documented in code and rules); 1 `environment` → no promotion (machine-specific paths, not a risk); 1 `out-of-scope` → resolved at harvest (`## Current state` added to Spine's `progress.md`). The discovery-level architectural decision (stdout digest + narrative `summary:` + deterministic logs) → decision-log 2026-11-12.
- **Learnings:** no incident or rework recorded; no `LEARN-NNN` entry.
- **Roadmap:** I3 → Done (Review Log 2026-11-12). I1 and I2 were folded in but their rows were left as is (harvest updates only the linked idea); I2 shipped narrower than its row (no `entries`/`last_entry`/`budget_chars`, no task `summary`). Suggested: `/spine-roadmap --review`.
- **Open toward G1:** Core SYNC ≤ 8,000 chars is not yet met on the worst case (13,039 before summaries); follow-ups I4 (budgets), I5 (indexes), I6 (archive), I11 (hook injection, needs I12).
