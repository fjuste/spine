---
description: Consolidate final delivery, update memory-bank, and close the active task with learnings
agent: build
variant: high
---

# Slash Command: /spine-harvest <plan_file_path>
Act as a Tech Lead and Knowledge Manager.

1. **Plan File Selection:** Use the provided `<plan_file_path>` argument.
   - Validate if the file exists and has a `.md` extension.
   - File must be under `docs/memory/active_tasks/` (open tasks only).
2. **GitFlow Compliance Check (mandatory):**
   - GitFlow is mandatory (not optional) for harvest.
   - Read `branch` and `base` from task frontmatter (fallback: legacy `## Branch:` / `## Base:` if present).
   - The implementation branch must match `feature/<descriptive-name>`.
   - The base integration branch must be `develop`.
   - If branch naming does not comply, stop and request correction before any consolidation steps.

3. **Final Verification:** Run the full test suite to ensure there are no regressions.

3.5. **Graphify refresh (only when Graphify is in use):**
    - Proceed only if `graphify-out/graph.json` exists in the project root (Graphify is active for this consumer project).
    - If `graphify` CLI is available, run `graphify update .` from the project root to refresh the exploration graph after delivery changes.
    - If the CLI is missing or the update fails, note it in the harvest summary; do not block harvest or Git consolidation.

3.6. **MkDocs refresh (only when MkDocs is in use):**
    - Proceed only if `docs/mkdocs/mkdocs.yml` exists in the project root (MkDocs is active for this consumer project).
    - Do **not** rely on bare `mkdocs` on PATH (often missing). From the project root, run the first command that works:
      1. `uv run --extra docs mkdocs build -f docs/mkdocs/mkdocs.yml --strict` (preferred when `uv` + `docs` optional-dep / `requirements-docs.txt` exist)
      2. `.venv/bin/mkdocs build -f docs/mkdocs/mkdocs.yml --strict` (when venv already has mkdocs)
      3. `mkdocs build -f docs/mkdocs/mkdocs.yml --strict` (only if `command -v mkdocs` succeeds)
    - If none work, install docs deps (`uv sync --extra docs` or `uv pip install -r requirements-docs.txt`) and retry step 1; if still failing, report the errors.
    - If the build fails, report the errors; do not block harvest or Git consolidation.

3.7. **Execution record (primary source):**
    - Read `## Execution notes` and `## Execution evidence` from the task file. Treat them as the primary source of what happened during execution — this may be a new session with no memory of `/spine-execute`; do not rely on conversation history.
    - For each note, decide its destination and apply it in step 4:

      | Note type | Destination |
      |---|---|
      | `incident`, `rework` | `docs/memory/ledger/learnings/` (step 4b) — search `ledger/learnings/INDEX.md` by **tags** + symptoms first; append to **Recurrences** of the matching entry, otherwise create a new `LEARN-NNN` entry |
      | `decision` | New entry in `docs/memory/ledger/decisions/` (step 4c) only when **all three** `@grill-me` criteria hold (hard to reverse, surprising without context, result of a real trade-off); otherwise no promotion |
      | `environment` | `docs/memory/global/tech-context.md` § **Known Risks** when it is a risk; otherwise no promotion |
      | `out-of-scope` | `docs/memory/global/product-context.md` § **Known Opportunities (unplanned)**, or a new task suggested to the human (do not create it) |
      | `deviation` | Stays in the task; summarize in the delivery summary. Promote to a `ledger/learnings/` entry only when it exposes a recurring planning gap |
      | `resume` | No promotion — temporary state, superseded once execution continued |
      | Any note that names a new canonical domain term | `docs/memory/global/domain-glossary.md` |
      | Any note that establishes a reusable pattern | `docs/memory/global/system-patterns.md` |

    - Mark the destination on the note itself by appending it to the end of the entry: `→ LEARN-023`, `→ LEARN-007 recurrence`, `→ DEC 2026-11-11-short-slug`, `→ domain-glossary`, `→ system-patterns`, `→ tech-context Known Risks`, `→ Known Opportunities`, `→ suggested task`, `→ no promotion`. This marker is the only edit harvest makes to existing notes — never rewrite their content.
    - A note `No deviations from plan.` needs no routing.
    - **Legacy task** (no `## Execution notes` / `## Execution evidence`): proceed as before (task body, git log, current session) and state in the harvest summary that the execution record was missing.

4. **Memory Bank Update:**

   Entries are one file each (`02-memory-bank.md` § Ledger entries): copy the folder's `_template.md`, fill the frontmatter (`summary:` is one line of at most 160 chars) and create the file. Never read or append to a legacy single file (`global/decision-log.md`, `ledger/learnings.md`, the legacy delivery log section of `progress.md`).

   **4a. Delivery entry and Current state**
   - Create `docs/memory/ledger/deliveries/YYYY-MM-DD-NNN-task-slug.md`:
     - `id:` the file stem; `date:` today; `title:` from task frontmatter `title`; `task:` `NNN-slug`
     - `tags:` copied from task frontmatter (per `docs/governance/memory-tags-policy.md`)
     - `summary:` one line: what was delivered
     - Body: `**Branch:**` from frontmatter; `**Description:**` — concise delivery summary that cites the execution evidence: tests executed and results, plus manual/external runs (who, when, where the raw output lives) from `## Execution evidence`
   - Refresh **Current state** in `docs/memory/ledger/progress.md` (short bullet list).

   **4b. Learning entries** (when `## Execution notes` holds `incident` / `rework` entries routed in step 3.7, or the task recorded root cause, incident, or rework elsewhere)
   - Before a new `LEARN-NNN`, search `docs/memory/ledger/learnings/INDEX.md` by **tags** + symptoms per `memory-tags-policy.md`; in a project that still has a legacy `ledger/learnings.md`, search it too.
   - On a match, append `- YYYY-MM-DD — task NNN-slug (brief)` under **Recurrences** in that entry file. Otherwise create `docs/memory/ledger/learnings/LEARN-NNN-short-slug.md` with the next free number (highest `LEARN-NNN` in the index or the legacy file, plus one).
   - **Tags** required on new entries; copy from task frontmatter, refine if needed.
   - Mirror one-line pointer in task Delivery summary body.

    **4c. Decision entries and global files (apply the routing decided in step 3.7):**
    - Architectural decisions only: create `docs/memory/ledger/decisions/YYYY-MM-DD-short-slug.md` (Context, Decision, Why, Alternatives considered, Consequences).
    - When the new decision replaces an earlier one, set `superseded_by:` on the earlier entry to the new entry's `id` (search `ledger/decisions/INDEX.md`).
    - `docs/memory/global/domain-glossary.md` — canonical terms promoted during discovery or delivery.
    - `docs/memory/global/system-patterns.md` — new patterns established.
    - `## Implementation Plan` in the task body is not copied to the delivery entry (it uses frontmatter `title`, `tags`, and the delivery description only).

    **4c.1 Ledger index and memory budgets** (see `02-memory-bank.md` § Ledger entries and § Memory budgets)
    - Run `python3 .spine/scripts/spine.py memory index` from the project root to regenerate the `INDEX.md` files; never edit them by hand.
    - Run `python3 .spine/scripts/spine_validate.py memory`. Warnings never block harvest (exit 0); an `ERROR:` means `docs/memory/` is missing.
    - **Entry warnings** (missing or over-160-char `summary:`, stale `INDEX.md`) on entries written in this harvest: fix them now and re-run both commands.
    - **Current state over budget:** rewrite the **Current state** block of `progress.md` to fit (keep In flight / Blocked / Next; drop delivered detail that the delivery entries already hold), then re-run the validator.
    - **Every other warning** (digest total, legacy log files, narrative files, older entries): do not fix it here. List it in the step 7 summary as a follow-up — legacy log files → `spine.py memory migrate` (dry run, then `--apply`), open-task list → close or harvest stale tasks, narrative files → the human.
    - Never edit `global/` to meet a budget without showing the diff to the human and getting approval first.

     **4d. Roadmap lifecycle update (when `roadmap_idea` is set):**
     - Read `docs/memory/ledger/roadmap.md`.
     - Find the Idea Bank row matching frontmatter `roadmap_idea` (exact ID, e.g. `I3` — never fuzzy title match).
     - If the row is missing: note it in the harvest summary; do not invent a row.
     - If found:
       - Grep `docs/memory/active_tasks/` and `docs/memory/completed_tasks/` for other tasks with the same `roadmap_idea`.
       - If any **non-DONE** linked task remains (other than the one being harvested): keep or set Status to `In Progress`; do **not** mark `Done`. Append Review Log: `YYYY-MM-DD | I<n> | Harvested task NNN-… — still In Progress (open tasks remain)`.
       - If no other open linked work: set Status to `Done`. Append Review Log: `YYYY-MM-DD | I<n> | Harvested task NNN-… → Done`.
       - Update roadmap frontmatter `last_updated` (today). Do **not** change `last_reviewed` (that stays for strategic review).
     - Still suggest `/spine-roadmap --review` so Confidence/Impact can be re-scored from delivery evidence.
     - **Forbidden in harvest:** changing ICE product, Confidence, or Impact columns; editing Goals; inventing new ideas.

     **4e. MkDocs documentation (when `docs/mkdocs/mkdocs.yml` exists):**
    - Load the `documentation-driven-development` skill for documentation update criteria.
    - Review whether this task introduced public APIs, architectural patterns, or user-facing features.
    - If so, update the relevant `docs/mkdocs/*.md` files and include them in the final commit with the `docs:` prefix.
    - Run `uv run --extra docs mkdocs build -f docs/mkdocs/mkdocs.yml --strict` (fallback: `.venv/bin/mkdocs` or PATH `mkdocs`) to verify the documentation builds cleanly.
    - If the task does not warrant documentation updates, note the decision in the delivery summary.

5. **Active Task Closure:**
   - Update frontmatter: `status: DONE`, `completed_at: YYYY-MM-DD`, `updated_at: YYYY-MM-DD`.
   - Set `related_learnings:` when linked to `LEARN-NNN` entries.
   - Add final **Delivery summary** block in task body; cite the evidence from `## Execution evidence` (tests and manual runs) and list where each execution note was promoted.
   - Record learning: root cause + prevention + regression test.
    - If there was UI/E2E with Playwright, also record:
      - skill used (`playwright-cli` or `playwright-skill`);
      - reason for the choice (short and objective);
      - evidence of benefit (time, rework avoided, reduced risk).
    - If MkDocs is active, record in delivery summary: files updated in `docs/mkdocs/`, mkdocs build status.
   - **`git mv`** `docs/memory/active_tasks/NNN-name.md` → `docs/memory/completed_tasks/NNN-name.md` (create dir if missing).
   - Include the move in the final commit before merge to `develop`.

6. **Git Consolidation (GitFlow required):**
   - Make the final commit with a semantic message.
   - Merge only a valid `feature/<descriptive-name>` branch into `develop`.
   - Remove the local feature branch.

7. **Summary:** Present a concise summary of what was learned and improved in the project. When step 3.5 ran (or was skipped/failed), include Graphify refresh status and whether `graphify query` was used during delivery exploration. When step 3.6 ran (or was skipped/failed), include MkDocs build status. Report the execution record outcome from step 3.7: how many notes were promoted and where, or that a legacy task had no `## Execution notes` / `## Execution evidence` (missing). When step 4d ran, report whether the Idea Bank row was updated and to which Status (`Done` / `In Progress` / missing), and note that `/spine-roadmap --review` was suggested for ICE re-score. Report the memory budget outcome from step 4c.1: whether Current state was compacted, and each remaining `WARNING:` as a follow-up (scope, chars, limit, suggested owner).
