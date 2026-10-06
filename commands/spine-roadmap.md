---
description: Fill or update roadmap.md with GIST-informed structure (Goals + Idea Bank + ICE scoring)
agent: build
variant: high
---

# Slash Command: /spine-roadmap [--review | --add-ideas]

Act as a Strategic Product Manager. Use `@grill-me` for strategic discovery; score ideas with ICE per `docs/governance/ice-scoring-guide.md`.

**Precondition:** `docs/memory/ledger/roadmap.md` exists (seeded by `spine.py install`; fill template with this command).

## Modes

| Mode | Flag | Behavior |
|------|------|----------|
| Fill (default) | *(none)* | Full strategic discovery. Define Goals via `@grill-me`, generate ideas, ICE-score everything, write roadmap.md. Overwrites template placeholders. |
| Review | `--review` | Re-read existing goals and Idea Bank. Update Confidence based on delivery evidence. Adjust Impact if assumptions changed. Update `last_reviewed` in frontmatter. Re-score ideas linked to recently completed tasks. |
| Add ideas | `--add-ideas` | Append new ideas to existing goals without re-scoring the full bank. Brainstorm against active goals, ICE-score new entries, append to Idea Bank table. Do not modify existing goals or scores. |

## Step 1 — Load context

1. Read `docs/memory/ledger/roadmap.md` frontmatter and content.
2. Read `docs/governance/ice-scoring-guide.md` for scoring criteria.
3. Read `docs/memory/global/` Core SYNC files for domain context (product-context, project-brief, decision-log).

## Step 2 — Fill mode (default, no flags)

### 2a. Strategic discovery via `@grill-me`

Load the `@grill-me` skill. Interview the user to define Goals. Use strategic framing questions:

**Goal discovery questions (one at a time):**

- "What outcome should this project achieve in the next [short/medium/long] horizon?"
- "How would you measure success for that outcome? What metric and what target?"
- "What's the baseline today for that metric?"
- "Is this goal a prerequisite for anything else, or dependent on another goal?"
- "What's a realistic time horizon for this goal?"

**Per-goal validation criteria:**

- Is the outcome **measurable**? (If not, ask for a metric.)
- Is it **time-bound**? (If not, set a horizon.)
- Is it distinct from features/ideas? Goals describe outcomes, not work.

**Iterate:** Define 1–5 active goals. Assign G1, G2, … IDs. Write each into `## Goals` section.

### 2b. Idea generation

For each active goal, brainstorm 1–5 ideas. For each idea:

1. **Anchor to the goal's Outcome metric.** Does this idea directly move that metric?
2. **Score with ICE** using `docs/governance/ice-scoring-guide.md` criteria:
   - **Impact (1–10):** How much does this move the goal's outcome metric?
   - **Confidence (1–10):** How sure are we? What evidence supports this?
   - **Ease (1–10):** How fast can we deliver? (Inverse of effort.)
   - **ICE = I × C × E**

### 2c. Write roadmap.md

1. Set frontmatter: `last_updated`, `last_reviewed` (today), `goals_active` (count), `ideas_total` (count).
2. Fill `## Goals` with discovered goals.
3. Fill `## Idea Bank` table with scored ideas.
4. Append to `## Review log`: initial fill entry.
5. Preserve `review_cadence` and `ice_method` frontmatter (template defaults).

## Step 3 — Review mode (`--review`)

1. Read existing `## Goals` and `## Idea Bank`. Identify ideas linked to recently completed tasks (grep `docs/memory/completed_tasks/` for `roadmap_idea` frontmatter matches).
2. For each idea with recent delivery evidence:
   - **Update Confidence:** Did delivery confirm or contradict assumptions? Adjust score per ICE guide criteria.
   - **Update Impact:** Did the actual outcome match expected impact? Adjust if needed.
   - **Update Status:** Treat harvest’s `Done` (or plan’s `In Progress`) as already applied when present. Confirm Status; only change it if delivery evidence shows it is wrong. Do not rely on `--review` as the primary way to mark Done — Harvest owns that lifecycle update.
3. Re-evaluate goal statuses: `Active` → `Achieved` if outcome metric threshold was met.
4. Update frontmatter: `last_reviewed` (today), `ideas_total` (recount), `goals_active` (recount).
5. Append to `## Review log`: review entry with date and changes made.
6. **Do not add new goals or ideas** in review mode. Suggest `--add-ideas` for new ideas.

## Step 4 — Add-ideas mode (`--add-ideas`)

1. Read existing `## Goals`. Present active goals to the user.
2. Ask which goal(s) to brainstorm against.
3. For each selected goal, use `@grill-me` to generate ideas. Same ICE scoring discipline as fill mode.
4. Append new rows to `## Idea Bank` table. Assign next available I* IDs.
5. Update frontmatter: `last_updated` (today), `ideas_total` (recount).
6. Append to `## Review log`: add-ideas entry.
7. **Do not modify existing goals, scores, or frontmatter timestamps** other than `last_updated` and `ideas_total`.

## Step 5 — Completion

After writing or updating `roadmap.md`:

- Summarize changes: goals defined/reviewed, ideas added/scored, ICE ranges.
- Suggest: "Use `roadmap_idea: I3` in task frontmatter to link future tasks to roadmap ideas. `/spine-plan` sets Idea Bank Status to In Progress; `/spine-harvest` marks Done when linked work is complete. Run `/spine-roadmap --review` after harvest to re-score Confidence/Impact."
- For fill mode: remind that `/spine-plan` is the next step for the highest-ICE idea.

## Guard rails

- **Strategic content** (Goals, ICE scores, Confidence, Impact, new ideas) is modified only by this command. Bootstrap does not touch `roadmap.md`.
- **Lifecycle Status** and Review Log entries for linked tasks may be updated by `/spine-plan` (In Progress) and `/spine-harvest` (Done / still In Progress). Do not treat those edits as out of policy.
- ICE scores must reference `docs/governance/ice-scoring-guide.md` criteria. No gut-feel scores without anchoring to the guide.
- Goals must be outcome-based and measured. Reject feature-disguised-as-goal entries (e.g., "Add dark mode" is an idea, not a goal — "Improve user accessibility satisfaction from 60% to 85%" is a goal).
- Roadmap is optional — projects without roadmap.md skip this command gracefully.
