---
task_id: 022
title: Memory migrate — split legacy decision-log, learnings and delivery log into ledger entries
goal: spine.py memory migrate splits the frozen legacy log files into per-entry ledger files without losing entry text, dry run by default and --apply to write
status: DONE
tags:
  - type/feature
  - area/memory
  - stack/python
branch: feature/memory-migrate
base: develop
execution_skill: executing-plans
roadmap_idea: I25
created_at: 2026-11-14
updated_at: 2026-11-14
completed_at: 2026-11-14
related_learnings: [LEARN-003, LEARN-004, LEARN-005]
---

# 022-memory-migrate

## Discovery notes

Discovery (grill-me protocol) ran on 2026-11-14. Sources: digest Current state ("plan the migrate task"), task 021 (entry format, decisions 6 and 10), roadmap I25, and a read-only survey of the legacy files in 11 consumer projects under `~/Workspace`.

**Formats found (survey 2026-11-14, read-only):**

| Legacy file | Shapes seen | Projects |
|---|---|---|
| `global/decision-log.md` | `### YYYY-MM-DD - Title` or `### YYYY-MM-DD — Title` (one `### 2026-09-22-single-node - Title`), body `**Context:**` / `**Decision:**` / `**Consequences:**`, entries split by `---` | intelligence-engine, onboarding-hub (70) and 6 smaller banks |
| `global/decision-log.md` | 4-column table `Data \| Decisão \| Porquê \| Alternativas` (header in Portuguese, same column order everywhere) | spine, agenthub (35), juste (50, decision cell starts with `**bold**`) |
| `ledger/learnings.md` | `## LEARN-NNN — Title` or `### LEARN-NNN — Title`; `**First seen:** DATE \| **Task:** NNN-slug`, `**Tags:** a, b`; sub-headings (`### Sintomas`) inside an entry in juste; IDs out of order in agenthub | all with learnings |
| `ledger/progress.md` § `Delivery log (newest first)` | `### YYYY-MM-DD — Title`, `**Task:** NNN-slug \| **Branch:** …`, `**Tags:** a, b`, `**Description:** …`; other `##` sections may follow the log (agenthub) | 8 projects; 2 surveyed projects (juste included) have no delivery log |

Placeholders seen: `### YYYY-MM-DD - TITLE`, `### [DATA] - [TITULO]`, `### YYYY-MM-DD — Title`, `## LEARN-001 — Example incident slug`. Every non-placeholder entry heading carries a date or a `LEARN-NNN` ID. Text before the first entry is template boilerplate (file title, `## Architectural Decisions`, intro line, tag-policy line, `---`).

**Resolved decisions (user, 2026-11-14):**

1. **`--apply` removes the legacy files.** It deletes `global/decision-log.md` and `ledger/learnings.md` and cuts only the `## Delivery log` section from `progress.md`. Git history keeps the originals; the dry run (default) shows exactly what goes.
2. **Mechanical `summary:` = the entry title**, capped at 160 chars with an ellipsis. Agents can improve a summary later when they touch the entry.
3. **`spine.py update` prints a hint only** when legacy files exist; migration stays an explicit, reviewable step per project.

**Planner's choices (reversible, no question needed):**

- **Bodies are copied verbatim** (everything under the entry heading up to the next entry, trailing `---` separators and blank lines trimmed), metadata lines included. Table rows become `**Decision:**`, `**Why:**`, `**Alternatives considered:**` fields from cells 2–4. Nothing inside an entry is rewritten, so no entry text is lost.
- **Frontmatter is read from the legacy metadata lines when present:** `**Task:**` → `task:`, `**Tags:**` → `tags:`, `**First seen:**` → learning `date:`. Absent fields stay empty (`tags: []`, `task:`). Decisions get `superseded_by:` empty.
- **Titles:** heading text after the date/ID and its separator (`-`, `—`, `–`, `:`). Table rows: the leading `**bold**` part of the decision cell when it has one, else the cell, both capped at 160.
- **IDs and file names** follow task 021: decisions `YYYY-MM-DD-slug`, deliveries `YYYY-MM-DD-NNN-task-slug` when a `**Task:**` line exists (else `YYYY-MM-DD-slug`), learnings `LEARN-NNN` in `LEARN-NNN-slug.md`. Slugs are ASCII (accents folded), lowercase, hyphenated, at most 60 chars cut at a hyphen. Two entries of one run with the same ID get `-2`, `-3`, … in file order; the report lists every suffix.
- **Unparsed text:** text before the first entry (preamble) is dropped and listed in the report. Non-blank text after the first entry that belongs to no entry (lines after a decision table, a non-entry heading at entry level or above) is *unparsed*: `--apply` refuses and writes nothing until it is fixed by hand.
- **Conflicts:** an entry whose ID already exists as a file in its folder (projects that harvested into the new layout before migrating, like Spine itself) is a conflict; `--apply` refuses and writes nothing. Placeholder entries are skipped and reported.
- **All-or-nothing:** `--apply` computes the whole plan first; it writes only when there are no conflicts and no unparsed text, then removes the legacy parts and runs `write_indexes`. After a successful apply a second run prints "nothing to migrate".
- Code lives in a new module `scripts/spine_cli/migrate.py` (`memory.py` is already 1,088 lines); `spine.py memory migrate [--apply]` dispatches to it.

**Out of scope:**

- Legacy pre-v2.1 sections in `progress.md` (`O que funciona`, `Em andamento`, `Concluído recentemente`, …): untouched.
- Rewriting summaries or bodies with an LLM; reshaping bodies into the new templates.
- Resolving `(task NNN)` mentions in decision headings into `task:` slugs.
- `LEARN-NNN` collisions across parallel branches (RFC-001 SPN-22-01).
- Running migrate from `spine.py update`.

## Objective

Ship `python3 .spine/scripts/spine.py memory migrate [--apply] [--project-root=PATH]`, the last piece of roadmap I25. The command reads the three frozen legacy log files of a memory bank and turns each entry into a ledger entry file with the task-021 frontmatter (`id`, `date`, `title`, `summary`, `tags`, `task`, plus `superseded_by` for decisions) and the legacy body copied verbatim.

Without `--apply` it is a dry run: it prints, per legacy file, the entry files it would create, the placeholders it skips, the preamble it drops, any unparsed text (with line numbers) and any ID conflicts, and writes nothing. With `--apply` and a clean plan it writes the entries, deletes `global/decision-log.md` and `ledger/learnings.md`, cuts the `## Delivery log` section from `progress.md`, and regenerates the ledger `INDEX.md` files. A plan with conflicts or unparsed text makes `--apply` exit 1 and leave the tree untouched.

`spine.py update` prints a one-line hint when legacy files remain. Rules, commands and docs drop "(planned)" and describe the command.

## Inputs

- `scripts/spine_cli/memory.py` — `LEDGER_FOLDERS`, `ENTRY_SUMMARY_MAX_CHARS`, `read_entry`, `collect_entries`, `write_indexes`, `_section`, legacy regexes (`_H3_RE`, `_LEARN_HEADING_RE`, `_PLACEHOLDER_ENTRY_RE`, `_table_rows`), `run_memory`, `LOG_HINT`
- `scripts/spine.py` — `memory` subparser (`choices`, module docstring usage)
- `scripts/spine_cli/update.py` — Step 4/4 Memory bank
- `templates/docs/memory/ledger/{decisions,learnings,deliveries}/_template.md` — field order and body labels
- `rules/02-memory-bank.md` (§ Ledger entries, § Memory budgets), `commands/spine-harvest.md` (step 4c.1 follow-ups), `commands/spine-update.md`, `README.md`, `AGENTS.md`
- Legacy samples: Spine `docs/memory/`, and read-only the 11 projects in the survey above

## Expected Outputs

- `scripts/spine_cli/migrate.py` (new): parsers for the three legacy shapes, `MigrationPlan` (entries, skipped placeholders, dropped preamble, unparsed lines, conflicts), entry rendering, `render_report`, `apply_plan`, `run_migrate`
- `scripts/spine.py`: `migrate` action and `--apply` flag on `memory`
- `scripts/spine_cli/update.py`: legacy-files hint in Step 4/4
- `scripts/spine_cli/memory.py`: shared helpers made importable only where `migrate.py` needs them (no behaviour change); `LOG_HINT` and `LEGACY_LABEL` text unchanged unless a test pins new wording
- Docs: `rules/02-memory-bank.md`, `commands/spine-harvest.md`, `commands/spine-update.md`, `README.md`, `AGENTS.md`
- Tests: `tests/unit/test_memory_migrate.py` (new); `tests/unit/test_spine_cli.py` (update hint)
- Roadmap: I25 Review Log line at plan time; `Done` at harvest

## Acceptance Criteria (verifiable, TDD-ready)

- [x] The parsers turn every legacy shape from the survey into entries: heading-format decisions (`-`, `—`, `–` separators and a date-slug heading), table-format decisions (bold-lead and plain cells), `##`/`###` learnings with `**First seen:**`/`**Task:**`/`**Tags:**` and inner sub-headings, and the progress Delivery log with `**Task:**`/`**Tags:**`. Each entry has `id`, `date`, `title`, `summary` (title capped at `ENTRY_SUMMARY_MAX_CHARS` with an ellipsis), `tags`, `task`, and its body verbatim. Placeholders are skipped; slugs are ASCII and capped; duplicate IDs in one run get `-2`, `-3`, ….
  - Test: `test_parse_heading_decisions`, `test_parse_table_decisions`, `test_parse_learnings_with_metadata_and_subheadings`, `test_parse_delivery_log_section`, `test_placeholders_are_skipped`, `test_summary_is_title_capped`, `test_slug_folds_accents_and_caps_length`, `test_duplicate_ids_get_suffixes`, `test_body_is_copied_verbatim`
- [x] Every rendered entry reads back through `memory.read_entry` with the same `id`, `date`, `title`, `summary`, `tags` and `task`, and passes the `spine_validate.py memory` summary checks.
  - Test: `test_rendered_entry_round_trips_through_read_entry`, `test_migrated_entries_pass_summary_checks`
- [x] `spine.py memory migrate` without `--apply` prints the report (entries to create per legacy file, skipped placeholders, dropped preamble, unparsed lines with line numbers, conflicts) and changes nothing on disk; with no legacy files it prints "nothing to migrate" and exits 0.
  - Test: `test_dry_run_reports_and_writes_nothing` (byte-for-byte tree snapshot before/after), `test_dry_run_lists_dropped_preamble`, `test_no_legacy_files_prints_nothing_to_migrate`
- [x] `--apply` on a clean plan writes the entry files, deletes `global/decision-log.md` and `ledger/learnings.md`, removes only the `## Delivery log` section from `progress.md` (Current state and any other section stay byte-identical), and regenerates `INDEX.md`; afterwards `check_budgets` reports no legacy-file warning and no stale index, the digest shows no legacy label, and a second run prints "nothing to migrate".
  - Test: `test_apply_writes_entries_and_removes_legacy`, `test_apply_keeps_other_progress_sections`, `test_apply_regenerates_indexes`, `test_apply_is_idempotent`
- [x] `--apply` exits 1 and leaves the tree byte-identical when the plan has unparsed text or an ID that already exists as an entry file; the report names each problem.
  - Test: `test_apply_refuses_on_unparsed_text`, `test_apply_refuses_on_existing_entry_conflict`
- [x] `spine.py update` prints a hint naming `spine.py memory migrate` when any legacy file (or a Delivery log section) exists, and no hint otherwise. `rules/02-memory-bank.md`, `commands/spine-harvest.md`, `commands/spine-update.md`, `README.md` and `AGENTS.md` describe `memory migrate` (dry run default, `--apply`, legacy removal) and no longer call it "planned"; the 021 legacy-mention sweep stays green.
  - Test: `test_update_hints_migrate_when_legacy_files_exist`, `test_update_no_hint_without_legacy_files`, `test_docs_describe_memory_migrate`, `test_migrate_not_called_planned`, existing `test_old_log_paths_only_mentioned_as_legacy`
- [x] Manual evidence in `## Execution evidence`: dry run on the 11 surveyed projects (read-only, `git status --porcelain docs/memory` unchanged, report counts match the survey); `--apply` on scratch copies of onboarding-hub, agenthub, juste and intelligence-engine (validator then shows no legacy warning); and Spine's own memory bank migrated after a backup to the session scratchpad and the human's go-ahead (Spine's `docs/` is not versioned, so git history cannot restore it).
  - Test: manual run; commands, counts and backup path recorded.

## Test Strategy

- **Unit (`tests/unit/test_memory_migrate.py`, new):** `tmp_path` memory banks built from small fixtures that copy each surveyed shape (heading decisions with each separator, Portuguese 4-column table with bold-lead cells, `##` and `###` learnings with metadata and inner `### Sintomas`, a progress file with Current state + Delivery log + a following `##` section, and each placeholder form). Use `ENTRY_SUMMARY_MAX_CHARS` and the module's slug cap constant, never literal numbers. Dry-run and refusal tests compare a `{path: bytes}` snapshot of `docs/` before and after.
- **CLI:** call `run_migrate` and `spine.py main(["memory", "migrate", ...])` with `--project-root=tmp_path`; capture stdout with `capsys`.
- **Update hint:** extend the `test_spine_cli.py` update pattern with a project that has a legacy `decision-log.md` and one that doesn't.
- **Text contract:** key-phrase assertions on the five doc files, plus a "no `migrate` line says planned" check.
- **Regression:** full suite, especially `test_ledger_entries.py`, `test_memory_digest.py`, `test_memory_budgets.py`, `test_spine_cli.py`.
- **Command:** `pytest -v tests/`

## Implementation Plan

### Task 1: Legacy parsers

**Files:**
- Create: `scripts/spine_cli/migrate.py`
- Test: `tests/unit/test_memory_migrate.py`

**Step 1:** Write failing tests for the four parsers and placeholder skipping (fixtures from the survey shapes).
**Step 2:** Run — expect FAIL (module missing).
**Step 3:** Implement `LegacyEntry(kind, id, date, title, tags, task, body, line)` and `parse_decision_log`, `parse_learnings`, `parse_delivery_log`, each returning entries plus dropped-preamble lines and unparsed lines (with 1-based line numbers). Reuse `memory._section`, `_PLACEHOLDER_ENTRY_RE` and the `LEARN-` heading regex; treat `Example incident slug` as the learnings placeholder.
**Step 4:** Run — expect PASS. Commit `feat(memory): parse legacy decision-log, learnings and delivery log`.

### Task 2: Entry IDs, slugs and rendering

**Files:**
- Modify: `scripts/spine_cli/migrate.py`
- Test: `tests/unit/test_memory_migrate.py`

**Step 1:** Failing tests: slug folding/capping, delivery ID with and without `**Task:**`, duplicate suffixes, summary capped, round trip through `memory.read_entry`, summary checks pass.
**Step 2:** Implement `slugify`, `assign_ids`, `render_entry` (frontmatter in the `_template.md` field order, then the verbatim body; table rows rendered as `**Decision:**` / `**Why:**` / `**Alternatives considered:**`).
**Step 3:** Run — expect PASS. Commit `feat(memory): render legacy entries as ledger entry files`.

### Task 3: Plan, report and apply

**Files:**
- Modify: `scripts/spine_cli/migrate.py`, `scripts/spine.py`, `scripts/spine_cli/memory.py` (dispatch only)
- Test: `tests/unit/test_memory_migrate.py`

**Step 1:** Failing tests for dry run (snapshot unchanged, report content), nothing-to-migrate, apply (entries written, legacy removed, other progress sections intact, indexes regenerated, budgets clean, idempotent), refusals (unparsed text, existing-entry conflict; snapshot unchanged, exit 1).
**Step 2:** Implement `build_plan(root)`, `render_report(plan)`, `apply_plan(root, plan)` (write entries → delete/cut legacy → `write_indexes`), `run_migrate(project_root, apply)`; add `migrate` to the `memory` choices and `--apply` (help: "with migrate: write entries and remove legacy files; default is a dry run"); update the `spine.py` docstring usage.
**Step 3:** Run — expect PASS. Commit `feat(memory): spine.py memory migrate with dry run and --apply`.

### Task 4: Update hint

**Files:**
- Modify: `scripts/spine_cli/update.py`
- Test: `tests/unit/test_spine_cli.py`

**Step 1:** Failing tests: hint printed with a legacy file or Delivery log section; absent otherwise.
**Step 2:** Implement a `has_legacy_logs(memory_dir)` helper in `migrate.py` and print the hint in Step 4/4.
**Step 3:** Run — expect PASS. Commit `feat(update): hint memory migrate when legacy log files remain`.

### Task 5: Docs

**Files:**
- Modify: `rules/02-memory-bank.md`, `commands/spine-harvest.md`, `commands/spine-update.md`, `README.md`, `AGENTS.md`
- Test: `tests/unit/test_memory_migrate.py` (text contract)

**Step 1:** Failing text-contract tests.
**Step 2:** Describe the command (dry run default, `--apply`, what it removes, refusal on unparsed text or conflicts, `memory index` run). Keep old-path mentions on lines that say "legacy". Stage explicit files only (LEARN-003: the tree holds untracked `skills/synced/`).
**Step 3:** Full suite `pytest -v tests/` — expect PASS. Commit `docs(memory): document spine.py memory migrate`.

### Task 6: Evidence

**Step 1:** For each surveyed project, record `git status --porcelain docs/memory`, run `python3 scripts/spine.py memory migrate --project-root=<repo>`, confirm the status is unchanged, and keep the report in the session scratchpad.
**Step 2:** Copy onboarding-hub, agenthub, juste and intelligence-engine `docs/memory` into scratch git repos; `--apply`; run `spine_validate.py memory` and `memory digest`.
**Step 3:** Back up Spine's `docs/memory` to the session scratchpad, ask the human, then `--apply` on Spine itself (expect no conflicts: the legacy `LEARN-001` is a placeholder and the legacy delivery log stops before 021; `LEARN-002`/`LEARN-003` and the 021 delivery already live in the folders).
**Step 4:** Record results in `## Execution evidence`.

## Execution notes
- 2026-11-14 — environment — Spine's `docs/memory` is partly versioned despite `/docs/` in `.gitignore`: 17 files are force-tracked, among them `global/decision-log.md` and `ledger/progress.md`; `ledger/learnings.md` and task files are not. The scratchpad backup before the self-apply stays required. → tech-context Known Risks
- 2026-11-14 — decision — `migrate` is dispatched in `scripts/spine.py` (`_cmd_memory`), not in `memory.run_memory`: `migrate.py` imports `memory.py`, so dispatching from `memory.py` would make the import circular. `memory.py` is unchanged; `migrate.py` imports `_cap` and `_PLACEHOLDER_ENTRY_RE` from it as they are. → no promotion
- 2026-11-14 — decision — Frontmatter scalars that plain YAML would misread (leading indicator char, `: `, ` #`, trailing `:`) are written as a one-line `>-` block. `memory.read_frontmatter` reads it back unchanged, so entries round-trip and stay valid YAML. → no promotion
- 2026-11-14 — deviation — The dry run on 27 local banks (more than the 11 surveyed) found shapes the survey missed: `## YYYY-MM-DD — Title` decision headings (fgv, libidus), bracketed dates `### [2026-04-15] - Title` (terraform/medpedia), learnings dated `**Data:** 2026-06-25` instead of `**First seen:**`, and `# comments` inside fenced code blocks in entry bodies (hetzner, libidus). Fix: decision entries accept heading levels 2–3 and bracketed dates; learning `date:` falls back to the first ISO date in the body; headings inside ``` / ~~~ fences are body text (the Delivery log section finder skips them too). This widens parsing but stays within the plan (no AC or scope change), so no stop. → LEARN-004
- 2026-11-14 — rework — My first parser marked the text of files with no entries (e.g. `_No learnings recorded yet._`) as unparsed, which blocked `--apply` on 4 empty-template banks. Changed to follow the plan: all text before the first entry is dropped preamble. To keep unknown entry formats from being dropped quietly, a non-entry heading at the deepest entry level (`###`) before the first entry starts unparsed text. → LEARN-004
- 2026-11-14 — out-of-scope — `memory._section` (digest, budgets) also ends a section at a `## ` line inside a fenced code block. Never seen in a real Current state, so left as is. Worth a fence-aware `_section` if it shows up. → Known Opportunities
- 2026-11-14 — incident — Commit `e666045` broke `test_old_log_paths_only_mentioned_as_legacy`, and the break was found only after `69f9207`. Symptom: the 021 sweep flagged 11 lines of `migrate.py` that name old log paths without "legacy". Root cause: the sweep reads only git-tracked files, so the pre-commit `pytest` run (317 passed) never saw the untracked new module; the next run's failure was then hidden because `pytest … | tail` returns tail's exit code. Fix: follow-up commit `2e48744` labels those lines "legacy". Later runs check pytest's real exit code. → LEARN-005
- 2026-11-14 — deviation — After `--apply`, agenthub and juste still get the whole-file `progress.md` budget warning (24,654 and 23,327 chars > 6,000). The hint on that warning says "split it into ledger entries with spine.py memory migrate", but migrate has nothing left to do there. The excess is pre-v2.1 sections (`O que funciona`, `Entregue recentemente`, …), which this task leaves out of scope. The AC "no legacy-file warning afterwards" holds on the fixtures, on onboarding-hub, on intelligence-engine and on Spine, but not on these two banks. Proposed fix (not done; waiting for the human): when `progress.md` has no Delivery log section, its whole-file warning names the pre-v2.1 sections and "trim with human approval" instead of migrate. This changes `LOG_HINT` behaviour in `memory.py`. → no promotion
- 2026-11-14 — environment — Spine's own `--apply` writes the new entry files under the gitignored `docs/`. `global/decision-log.md` and `ledger/progress.md` are tracked, so git sees one deletion and one modification. The 24 new entries would need `git add -f`, as the 021 harvest did for its entries. → tech-context Known Risks
- 2026-11-14 — decision — Human approved the progress hint fix in this task (2026-11-14). `check_budgets` now uses `PROGRESS_LEGACY_SECTIONS_HINT` ("trim them with human approval") for `progress.md` once it has no Delivery log section, and keeps `LOG_HINT` (migrate) while the section remains. The rule's budget table says the same. Commit `0b46a25`. → no promotion

## Execution evidence
**Tests executed:**
- `pytest -v tests/` (branch `feature/memory-migrate` at `0cb2f21`)
- Red/green runs per task: `pytest tests/unit/test_memory_migrate.py`, `pytest tests/unit/test_spine_cli.py -k "migrate or legacy_files"`, `pytest tests/unit/test_memory_budgets.py -k delivery_log_remains`

**Test results:** 322 passed, 0 failed (was 291 before the task). 31 new tests: 28 in `test_memory_migrate.py` (parsers, rendering round trip, dry run, apply, refusals, idempotence, code fences, docs contract), 2 update-hint tests in `test_spine_cli.py`, 1 progress-hint test in `test_memory_budgets.py`, and the existing 021 sweep `test_old_log_paths_only_mentioned_as_legacy` passing again.

**Manual / external evidence** (agent, 2026-11-14, branch `feature/memory-migrate`; raw output in the session scratchpad `/tmp/claude-1000/-home-juste-Workspace-ide-spine/24553b83-1210-48ab-a75d-3a757aca4a6f/scratchpad/evidence/` and `/tmp/claude-1000/-home-juste-Workspace-ide-spine/24553b83-1210-48ab-a75d-3a757aca4a6f/scratchpad/apply/`, temporary):
- **Dry run, 11 surveyed projects** (`spine.py memory migrate --project-root=<repo>`): every run exit 0; `git status --porcelain docs/memory` md5 identical before and after in all 11. Totals: onboarding-hub 220 (70 decisions / 34 learnings / 116 deliveries), agenthub 75 (35/16/24), intelligence-engine 50 (17/6/27), juste 46 (44 decisions + 4 unparsed table rows / 2 learnings), spine 24 and 6 smaller banks (4–25 entries each). Cross-checked against the digest's legacy counts: every difference is a placeholder the digest does not recognize (`LEARN-001 — Example incident slug`, `### [DATA] - [TITULO]`) or one of juste's 4 three-cell rows (the survey's "50" for juste was approximate; the file has 48 dated rows). 0 conflicts anywhere. A wider sweep of 27 local banks found 4 more parser shapes (see Execution notes). Its only remaining unparsed lines are genuine hand-fix cases: month-only dates (hetzner, ansible/medpedia), undated headings (tf-dsbr-chatbot, ansible/medpedia) and the juste rows.
- **`--apply` on scratch git copies:** onboarding-hub (220 files), agenthub (75) and intelligence-engine (50) applied with exit 0. juste refused with exit 1 and `git status` stayed clean; after adding the missing cell to its 4 rows by hand in the copy, it applied 50 entries. On all four: `spine_validate.py memory` exit 0 with no stale or missing `INDEX.md` and no summary problems; the digest shows no legacy label; a second run prints "nothing to migrate"; the `progress.md` diff removes only the Delivery log lines. All 395 migrated entry files parse with PyYAML `safe_load`. agenthub and juste still warn on the whole-file `progress.md` budget because of their pre-v2.1 sections; after `0b46a25` that warning says to trim with human approval and no longer points at migrate.
- **Spine self-apply** (human go-ahead 2026-11-14): `docs/memory` (36 files) was backed up to `/tmp/claude-1000/-home-juste-Workspace-ide-spine/24553b83-1210-48ab-a75d-3a757aca4a6f/scratchpad/backup-spine-docs-memory/` and checked identical with `diff -r`, then rehearsed on a copy. The real apply wrote 24 entries (18 decisions, 6 deliveries; the LEARN-001 placeholder was skipped), removed `global/decision-log.md` and `ledger/learnings.md`, and cut the Delivery log. Validator exit 0 with 0 warnings; digest 4,436 / 8,000 chars; a second run prints "nothing to migrate". Committed in `0cb2f21` (new entries via `git add -f`). Follow-up for harvest: `progress.md` Current state still calls the delivery log "legacy and frozen", and that text is now stale.

## Delivery summary
Shipped `spine.py memory migrate [--apply]` (new `scripts/spine_cli/migrate.py`), the update hint, the progress budget-hint fix and the docs, which completes roadmap I25. Evidence (from `## Execution evidence`): `pytest -v tests/` 322 passed (31 new); dry run on the 11 surveyed projects left them unchanged and the counts reconcile; `--apply` on 4 scratch banks (395 entries, valid YAML, validator clean, juste refused until hand-fixed); Spine's own bank migrated in `0cb2f21`.

Note routing: Spine's tracked-vs-ignored `docs/` (2 environment notes) → tech-context Known Risks; survey gap + parser rework → LEARN-004; sweep/pipe incident → LEARN-005; fence-aware `_section` → Known Opportunities; 3 decisions and 1 deviation → no promotion (reversible, or resolved in-task). Discovery decisions → DEC 2026-11-14-memory-migrate-explicit-all-or-nothing. During harvest, 9 notes that execution had appended under `## Execution evidence` were moved back under `## Execution notes`; their text is unchanged.

Learnings: LEARN-004. Root cause: parser rules came from a sample survey plus an unplanned strictness rule. Prevention: dry-run on every real input early. Regression tests: the three shape tests. LEARN-005. Root cause: the sweep reads only git-tracked files, and `pytest | tail` hides the exit code. Prevention: re-run after committing new files and check pytest's own exit code. Regression test: `test_old_log_paths_only_mentioned_as_legacy`.

