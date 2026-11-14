---
description: "Defines structure and practical use of the Memory Bank as the operational source of truth."
globs: 
alwaysApply: true
---

# MEMORY BANK V2.1 - State API

The `docs/memory/` directory is the **operational source of truth**.
The memory bank remains mandatory even when Graphify is available.

Tag conventions: see `docs/governance/memory-tags-policy.md`.

## Structure

```
docs/memory/
  global/                    # Stable narrative (changes with explicit justification)
    project-brief.md         # Scope, goals, project boundaries
    product-context.md       # Why the project exists, problems it solves, UX goals; § Known Opportunities (unplanned)
    domain-glossary.md       # Ubiquitous language: canonical domain terms (language only)
    system-patterns.md       # Stack, architecture, design patterns; § Project-Specific Alterations
    tech-context.md          # Dev setup, constraints, infra; § Known Risks
  ledger/                    # Changes every delivery cycle
    roadmap.md               # Prioritized milestones (filled by /spine-roadmap — not filled at bootstrap)
    progress.md              # Current state only (snapshot rewritten at harvest)
    decisions/               # One file per architectural decision (WHY) + generated INDEX.md
    learnings/               # One file per LEARN-NNN (incidents, root causes — harvest only) + INDEX.md
    deliveries/              # One file per harvested delivery + INDEX.md
  active_tasks/              # Open work only (PLANNING | IN_PROGRESS | REVIEW)
    <sequential-number>-<descriptive-name>.md
  completed_tasks/           # DONE tasks moved on harvest
    <sequential-number>-<descriptive-name>.md
```

Projects created before the per-entry ledger may still hold the legacy single files `global/decision-log.md`, `ledger/learnings.md` and a legacy delivery log section in `progress.md`: they are frozen (§ Ledger entries).

### File semantics (agent-oriented)

| File | Bootstrap fills | Notes |
|------|-----------------|-------|
| `project-brief.md` | Yes | Scope, goals, boundaries |
| `product-context.md` | Yes | Product behavior; § **Known Opportunities (unplanned)** for improvements not yet scheduled |
| `domain-glossary.md` | Yes | Terms + code location hints |
| `system-patterns.md` | Yes | Architecture; § **Project-Specific Alterations** (custom payment, auth, etc.) — agents must not revert |
| `tech-context.md` | Yes | Dev commands, env; § **Known Risks** |
| `roadmap.md` | **No** | Seeded with GIST-informed template; filled by `/spine-roadmap`; `/spine-plan` sets Idea Bank `In Progress` + `roadmap_idea`; `/spine-harvest` marks `Done`; optional split-plan notes from `/spine-plan` |
| `ledger/decisions/` | Yes (baseline entry) | WHY for major alterations; one entry per decision |
| `ledger/learnings/` | Rarely at bootstrap | Incidents at `/spine-harvest` only |
| `ledger/deliveries/` | No | One entry per `/spine-harvest` |

`/spine-bootstrap` runs after `python3 .spine/scripts/spine.py install` and fills placeholders in `global/`, `progress.md` Current state and the baseline entry in `ledger/decisions/`. It does **not** create `active_tasks/` files — use `/spine-plan`.

## Access Rules (pragmatic)

| Layer | Author | When it changes |
|---|---|---|
| `global/` | Human or agent with explicit approval | Scope/architecture changes |
| `ledger/` | Executing agent | Every delivery cycle |
| `active_tasks/` | Executing agent | Created in PLAN; updated until harvest |
| Task `## Execution notes` | `/spine-execute` writes; `/spine-harvest` reads | Appended when each fact happens (dated, typed, append-only); harvest only appends a destination marker (`→ LEARN-NNN`, `→ no promotion`, …) |
| Task `## Execution evidence` | `/spine-execute` writes; `/spine-harvest` reads | Filled before `REVIEW` (tests executed, results, manual/external runs); harvest cites it in the delivery summary |
| `completed_tasks/` | Executing agent | Written only at harvest (`git mv` from `active_tasks/`) |
| `ledger/decisions/`, `learnings/`, `deliveries/` | Executing agent | At harvest: new entry files (learnings when root cause / incident / rework recorded); `INDEX.md` only via `spine.py memory index` |

## Tiered SYNC (reading rules)

If `graphify-out/graph.json` exists, follow the **Graphify Discovery Protocol** below after memory bank SYNC. Graphify is an auxiliary code-structure layer; it does not replace reading and maintaining the memory bank.

If a file does not exist, create it only if it is part of the current task flow.

## Graphify Discovery Protocol

**When:** `graphify-out/graph.json` exists in the project root (Graphify active).

**Precedence (highest first):**

1. Memory bank (`docs/memory/`) — scope, alterations, decisions
2. This protocol — how to use the graph
3. Graphify platform always-on artifacts (Cursor `graphify.mdc`, OpenCode plugin, Claude PreToolUse hook)
4. Broad file search (Glob/grep) — last resort when graph is absent or insufficient

**Discovery sequence (execute in order; do not skip because file search is easier):**

1. Read `graphify-out/GRAPH_REPORT.md` (god nodes, communities, suggested questions)
2. Run targeted queries from project root:
   ```bash
   graphify query "<question>" --graph graphify-out/graph.json
   ```
3. Open source files cited in query output; confirm **EXTRACTED** edges; treat **INFERRED** as hypotheses until file reads confirm
4. Cross-check `docs/memory/global/system-patterns.md` § Project-Specific Alterations before suggesting "standard" platform behavior
5. Do **not** paste full `graph.json` into context

**Skill trigger:** When the user types `/graphify`, invoke the graphify skill before other work (rebuild, query, or explain per skill).

**Verify integration:** `python3 .spine/scripts/spine_validate.py graphify` (from project root after enabling Graphify via `python3 .spine/scripts/spine.py install` prompt or `--with-graphify`).

### Core (every session)

**Digest first.** From the project root run:

```bash
python3 .spine/scripts/spine.py memory digest
```

It prints `progress.md` **Current state**, one line per open task (`NNN | STATUS | title — goal`), the `summary:` of each narrative file (or a capped outline marked `summary missing`), entry counts and newest titles of the ledger folders (plus any legacy log file), and Extended-tier pointers. The digest **is** the Core SYNC:

1. Read the digest. Do not open full memory files by default.
2. Open a full file only when the task needs it: the task file you execute or plan against, a narrative file whose area you change, a ledger entry whose title the digest or a `ledger/<folder>/INDEX.md` row lists.
3. **SETUP:** if the digest ends with a `SETUP:` block, first write `summary:` frontmatter for the listed files only (§ Narrative summaries), then continue the task. Files the block defers wait for later sessions.
4. When you edit a narrative file, update its `summary:` in the same change.

**Fallback (script unavailable):** if the command fails (older `.spine` without `memory`, no Python), read the legacy Core list below and suggest `python3 .spine/scripts/spine.py update` to the user:

1. `global/project-brief.md` (scope)
2. `global/product-context.md` (product context)
3. `global/domain-glossary.md` (domain language — create lazily during `@grill-me` or `@spine-bootstrap` if missing)
4. `global/system-patterns.md` (how to build)
5. `global/tech-context.md` (constraints)
6. `ledger/decisions/INDEX.md` (previous decisions; legacy projects: `global/decision-log.md`)
7. `ledger/progress.md` — **Current state** section only
8. `active_tasks/` — open tasks only (files matching `^\d{3}-`; skip `_task-template.md`)

Measure the load on any project with `python3 .spine/scripts/spine.py memory stats` (per-file chars, legacy Core total, digest size).

### Extended (planning, harvest, ambiguous scope)

- `ledger/roadmap.md`
- `ledger/deliveries/INDEX.md` — delivery history (open single entries as needed)

### On demand (debugging, recurrence, audits)

- `ledger/learnings/INDEX.md`, then the entries it links
- `ledger/decisions/INDEX.md` for decision history (skip rows marked superseded)
- `completed_tasks/`
- Grep task and ledger entry frontmatter (`tags:`) per `memory-tags-policy.md`

After SYNC, before any code change, state:
- Key assumptions about the task derived from the memory bank.
- Any ambiguities, gaps, or conflicts found in the context — present them; do not pick silently.
- The simplest approach that satisfies the requirements. If a simpler alternative exists, name it and push back.

## Narrative summaries

Narrative files carry an agent-written `summary:` in YAML frontmatter; the digest shows it instead of the file.

- **Narrative:** `global/*.md` and any `ledger/*.md` file other than `progress.md` and `roadmap.md` (the legacy single log files `global/decision-log.md` and `ledger/learnings.md` are not narrative).
- **Ledger entries** (`ledger/decisions/`, `learnings/`, `deliveries/`) carry a one-line `summary:` each instead (§ Ledger entries); the digest counts them and lists the newest titles. `progress.md` holds only Current state; `roadmap.md` stays Extended tier. Tasks use their existing frontmatter (`task_id`, `status`, `title`, `goal`).

```yaml
---
summary: >-
  Stack, layers and request flow; Project-Specific Alterations for payment
  and auth. Open before changing architecture or integrations.
---
```

- At most 5 lines: what the file holds and when to open it. Leave out facts that change every task.
- Whoever edits a narrative file (bootstrap, harvest, any agent edit) updates its `summary:` in the same change.
- A value starting with `[Fill in` (seeded template placeholder) counts as missing.
- Write missing summaries only when a digest `SETUP:` block lists them; the block paces the one-time setup by a source budget per session.

## Ledger entries

Append-only memory is one Markdown file per entry, in three folders under `ledger/`. Agents read the digest, then a folder's `INDEX.md`, and open only the entries they need.

| Folder | One file per | File name (`id:`) | Written by |
|---|---|---|---|
| `decisions/` | Architectural decision with its WHY | `YYYY-MM-DD-short-slug.md` (reference: `DEC YYYY-MM-DD-short-slug`) | `/spine-bootstrap` (baseline), `/spine-harvest` |
| `learnings/` | Incident, rework or root cause | `LEARN-NNN-short-slug.md` (`id: LEARN-NNN`) | `/spine-harvest` |
| `deliveries/` | Harvested task | `YYYY-MM-DD-NNN-task-slug.md` | `/spine-harvest` |

Copy the folder's `_template.md`. Frontmatter:

```yaml
---
id: 2026-11-12-memory-digest
date: 2026-11-12
title: Core SYNC reads the memory digest
summary: Digest replaces full-file Core SYNC; narrative files carry summary frontmatter.
tags:
  - area/memory
  - type/feature
task: 018-memory-digest
superseded_by:
---
```

- `summary:` is required: one line, at most 160 chars. It is the entry's row in `INDEX.md`.
- `superseded_by:` (decisions only): when a new decision replaces an older one, set it on the old entry to the new entry's `id`. `INDEX.md` marks the old row superseded so agents skip it.
- Learning recurrences: append `- YYYY-MM-DD — task NNN-slug (brief)` under `**Recurrences:**` in the existing `LEARN-NNN` file instead of creating a new entry.
- **INDEX.md** in each folder is generated from entry frontmatter: run `python3 .spine/scripts/spine.py memory index` after adding or editing entries; never edit it by hand. It is committed; the installer adds `docs/memory/ledger/*/INDEX.md merge=union` to `.gitattributes`, so parallel branches merge their new rows without conflict. Re-run `memory index` after a merge to restore order.
- `spine_validate.py memory` warns on entries with a missing or over-160-char `summary:` and on a stale or missing `INDEX.md`.
- **Legacy single files** — `global/decision-log.md`, `ledger/learnings.md` and the legacy delivery log section of `progress.md` — are frozen in projects created before the per-entry ledger: read them, never append to them. The digest labels them legacy; the recurrence check at harvest also searches a legacy `learnings.md`. `spine.py memory migrate` (planned) splits them into entries.

## Memory budgets

`python3 .spine/scripts/spine_validate.py memory` measures the memory bank against fixed char budgets. Over-budget scopes print `WARNING:` lines (exit 0); only a missing `docs/memory/` is an error (exit 1).

| Scope | Budget (chars) | Remedy |
|---|---|---|
| `memory digest` total (Core SYNC) | 8,000 | Warning lists digest sections largest first |
| `progress.md` § Current state | 1,500 | `/spine-harvest` compacts it |
| Each narrative file body (frontmatter excluded) | 3,000 | Split or trim with human approval |
| Each ledger entry `summary:` | 160 | Validator names the files; also warns on a stale `INDEX.md` |
| Legacy `decision-log.md` | 5,000 | Frozen; split with `spine.py memory migrate` |
| `progress.md` whole file (legacy delivery log included) | 6,000 | Frozen legacy part; split with `spine.py memory migrate` |
| Legacy `learnings.md` | 6,000 | Frozen; split with `spine.py memory migrate` |

Task files, `roadmap.md`, `completed_tasks/` and whole `INDEX.md` files have no budget (an index grows by one line per entry; agents search it). The digest never shows budgets. `/spine-harvest` runs the validator, rewrites an over-budget Current state (which it owns) and reports every other warning as a follow-up. Never edit `global/` to meet a budget without showing the diff to the human first.

## Template: active_tasks/_task-template.md

Reference file (not a numbered task). Tasks use Obsidian-style YAML frontmatter. See `templates/docs/memory/active_tasks/_task-template.md`.

```yaml
---
task_id: 007
title: Social login adjustment
goal: One-line outcome the task must achieve
status: PLANNING
tags:
  - area/auth
  - type/feature
branch: feature/social-login-adjustment
base: develop
execution_skill: executing-plans
created_at: 2026-06-05
updated_at: 2026-06-05
completed_at:
related_learnings: []
---
```

| Property | Required | Notes |
|---|---|---|
| `task_id` | yes | Zero-padded number matching filename prefix |
| `title` | yes | Human-readable title |
| `goal` | yes | Single outcome sentence |
| `status` | yes | `PLANNING` \| `IN_PROGRESS` \| `REVIEW` \| `DONE` |
| `tags` | yes | YAML list; 1–5 tags per `memory-tags-policy.md` |
| `branch` | yes | GitFlow execution branch |
| `base` | yes | GitFlow base (default `develop`) |
| `execution_skill` | recommended | Without `@` prefix |
| `created_at` / `updated_at` | yes | ISO date `YYYY-MM-DD` |
| `completed_at` | on DONE | Set at harvest |
| `related_learnings` | optional | List of `LEARN-NNN` refs |

Body sections (no duplicate metadata — no `## Branch`, `## Base`, or body `## Status`):

```markdown
# 007-social-login-adjustment

## Discovery notes
...

## Objective
[Expanded goal]

## Inputs
- [Input files/data]

## Expected Outputs
- [Files/artifacts that must be generated]

## Acceptance Criteria (verifiable, TDD-ready)
- [ ] [Criterion 1]
  - Test: [specific test that proves this criterion]

## Test Strategy
...
```

Optional body section (use when bite-sized execution steps are needed):

```markdown
## Implementation Plan

### Task 1: [Component]
**Files:** ...
**Step 1:** ...
```

Execution sections (after `## Implementation Plan`; written by `/spine-execute`, read by `/spine-harvest` as its primary source so harvest works in a new session):

```markdown
## Execution notes
- 2026-11-11 — deviation — Split migration into two steps; plan assumed a single table → LEARN-023
- 2026-11-11 — out-of-scope — Retry helper duplicated in two services → Known Opportunities

## Execution evidence
**Tests executed:** `pytest tests/`
**Test results:** 42 passed
**Manual / external evidence:** who, when, commit/branch, command, summary, where the raw output lives
```

- Note types: `deviation` (contradiction with the plan → record and stop for the human), `incident` (symptom, root cause, fix), `rework`, `decision`, `out-of-scope`, `environment`, `resume` (resume point when execution stops midway; never promoted). With nothing to record: `No deviations from plan.`
- Append-only: execute adds entries; harvest only appends the destination marker.
- Never paste secrets, tokens, or keys — point to where raw output lives.
- Legacy tasks without these sections: harvest proceeds as before and reports the absence.

**Anti-patterns (do not use in task files):**

- Inline legacy metadata blocks (`**Status:**`, `**Branch:**`, `**Goal:**` at document top)
- `superpowers:*` skill headers instead of frontmatter `execution_skill`
- Hotfix/production-base branches in standard feature tasks (exceptions only when documented in workflow docs)

## Template: ledger/progress.md

```markdown
## Current state
- In flight: ...
- Blocked: ...
- Next: ...
```

Deliveries, learnings and decisions are entry files: see § Ledger entries and each folder's `_template.md`.

## Template: completed_tasks/

Same file as `active_tasks/` after harvest: frontmatter `status: DONE`, `completed_at` set, file moved via `git mv`.
