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

1. `global/project-brief.md` (scope)
2. `global/product-context.md` (product context)
3. `global/domain-glossary.md` (domain language — create lazily during `@grill-me` or `@spine-bootstrap` if missing)
4. `global/system-patterns.md` (how to build)
5. `global/tech-context.md` (constraints)
6. `global/decision-log.md` (previous decisions)
7. `ledger/progress.md` — **Current state** section only
8. `active_tasks/` — open tasks only (files matching `^\d{3}-`; skip `_task-template.md`)

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
