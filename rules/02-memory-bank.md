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
  global/                    # Stable base (changes with explicit justification)
    project-brief.md         # Scope, goals, project boundaries
    product-context.md       # Why the project exists, problems it solves, UX goals; § Known Opportunities (unplanned)
    domain-glossary.md       # Ubiquitous language: canonical domain terms (language only)
    system-patterns.md       # Stack, architecture, design patterns; § Project-Specific Alterations
    tech-context.md          # Dev setup, constraints, infra; § Known Risks
    decision-log.md          # Record of architectural decisions with WHY
  ledger/                    # Current state (updated on each task)
    roadmap.md               # Prioritized milestones (filled by /spine-roadmap — not filled at bootstrap)
    progress.md              # Current state + delivery log (append-only)
    learnings.md             # Recurrence registry (incidents, root causes — harvest only)
  active_tasks/              # Open work only (PLANNING | IN_PROGRESS | REVIEW)
    <sequential-number>-<descriptive-name>.md
  completed_tasks/           # DONE tasks moved on harvest
    <sequential-number>-<descriptive-name>.md
```

### Global file semantics (agent-oriented)

| File | Bootstrap fills | Notes |
|------|-----------------|-------|
| `project-brief.md` | Yes | Scope, goals, boundaries |
| `product-context.md` | Yes | Product behavior; § **Known Opportunities (unplanned)** for improvements not yet scheduled |
| `domain-glossary.md` | Yes | Terms + code location hints |
| `system-patterns.md` | Yes | Architecture; § **Project-Specific Alterations** (custom payment, auth, etc.) — agents must not revert |
| `tech-context.md` | Yes | Dev commands, env; § **Known Risks** |
| `decision-log.md` | Yes | WHY for major alterations and bootstrap baseline |
| `roadmap.md` | **No** | Seeded with GIST-informed template; filled by `/spine-roadmap`; `/spine-plan` sets Idea Bank `In Progress` + `roadmap_idea`; `/spine-harvest` marks `Done`; optional split-plan notes from `/spine-plan` |
| `learnings.md` | Rarely at bootstrap | Incidents at `/spine-harvest` only |

`/spine-bootstrap` runs after `python3 .spine/scripts/spine.py install` and fills placeholders in `global/` plus `progress.md` Current state. It does **not** create `active_tasks/` files — use `/spine-plan`.

## Access Rules (pragmatic)

| Layer | Author | When it changes |
|---|---|---|
| `global/` | Human or agent with explicit approval | Scope/architecture changes |
| `ledger/` | Executing agent | Every delivery cycle |
| `active_tasks/` | Executing agent | Created in PLAN; updated until harvest |
| Task `## Execution notes` | `/spine-execute` writes; `/spine-harvest` reads | Appended when each fact happens (dated, typed, append-only); harvest only appends a destination marker (`→ LEARN-NNN`, `→ no promotion`, …) |
| Task `## Execution evidence` | `/spine-execute` writes; `/spine-harvest` reads | Filled before `REVIEW` (tests executed, results, manual/external runs); harvest cites it in the delivery summary |
| `completed_tasks/` | Executing agent | Written only at harvest (`git mv` from `active_tasks/`) |
| `ledger/learnings.md` | Executing agent | At harvest when root cause / incident / rework recorded |

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

It prints `progress.md` **Current state**, one line per open task (`NNN | STATUS | title — goal`), the `summary:` of each narrative file (or a capped outline marked `summary missing`), entry counts and newest titles of the log files, and Extended-tier pointers. The digest **is** the Core SYNC:

1. Read the digest. Do not open full memory files by default.
2. Open a full file only when the task needs it: the task file you execute or plan against, a narrative file whose area you change, a `decision-log.md` or `learnings.md` entry whose title the digest lists.
3. **SETUP:** if the digest ends with a `SETUP:` block, first write `summary:` frontmatter for the listed files only (§ Narrative summaries), then continue the task. Files the block defers wait for later sessions.
4. When you edit a narrative file, update its `summary:` in the same change.

**Fallback (script unavailable):** if the command fails (older `.spine` without `memory`, no Python), read the legacy Core list below and suggest `python3 .spine/scripts/spine.py update` to the user:

1. `global/project-brief.md` (scope)
2. `global/product-context.md` (product context)
3. `global/domain-glossary.md` (domain language — create lazily during `@grill-me` or `@spine-bootstrap` if missing)
4. `global/system-patterns.md` (how to build)
5. `global/tech-context.md` (constraints)
6. `global/decision-log.md` (previous decisions)
7. `ledger/progress.md` — **Current state** section only
8. `active_tasks/` — open tasks only (files matching `^\d{3}-`; skip `_task-template.md`)

Measure the load on any project with `python3 .spine/scripts/spine.py memory stats` (per-file chars, legacy Core total, digest size).

### Extended (planning, harvest, ambiguous scope)

- `ledger/roadmap.md`
- `ledger/progress.md` — full **Delivery log**

### On demand (debugging, recurrence, audits)

- `ledger/learnings.md`
- `completed_tasks/`
- Grep task frontmatter (`tags:`) and ledger `**Tags:**` per `memory-tags-policy.md`

After SYNC, before any code change, state:
- Key assumptions about the task derived from the memory bank.
- Any ambiguities, gaps, or conflicts found in the context — present them; do not pick silently.
- The simplest approach that satisfies the requirements. If a simpler alternative exists, name it and push back.

## Narrative summaries

Narrative files carry an agent-written `summary:` in YAML frontmatter; the digest shows it instead of the file.

- **Narrative:** `global/*.md` except `decision-log.md`, plus any `ledger/*.md` other than `progress.md`, `learnings.md` and `roadmap.md`.
- **Log files** (`decision-log.md`, `progress.md`, `learnings.md`) need no summary: the digest counts entries and lists the newest titles. `roadmap.md` stays Extended tier. Tasks use their existing frontmatter (`task_id`, `status`, `title`, `goal`).

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

## Delivery log (newest first)
### YYYY-MM-DD — Title
**Task:** NNN-slug | **Branch:** feature/slug
**Tags:** area/example, type/feature
**Description:** ...
```

## Template: ledger/learnings.md

```markdown
## LEARN-001 — Short slug title
**First seen:** YYYY-MM-DD | **Task:** NNN-slug
**Tags:** area/example, type/incident

**Symptoms:** ...
**Root cause:** ...
**Detect early:** ...
**Prevention:** ...
**Regression test:** ...

**Recurrences:**
- YYYY-MM-DD — task NNN-slug (brief)
```

## Template: completed_tasks/

Same file as `active_tasks/` after harvest: frontmatter `status: DONE`, `completed_at` set, file moved via `git mv`.
