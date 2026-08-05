---
last_updated: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
review_cadence: monthly
goals_active: 0
ideas_total: 0
ice_method: "Impact × Confidence × Ease (1–10 each). See docs/governance/ice-scoring-guide.md."
---

# Roadmap

> Filled by `/spine-roadmap`. Bootstrap does not touch this file.
> ICE scoring guide: `docs/governance/ice-scoring-guide.md`.

## Goals

Goal definitions are outcome-based, measured, and time-bound. Each goal has a unique ID (G1, G2, …). Goals are distinct from features/ideas — they describe the outcome to achieve, not the work to do.

### G1: [Goal Name]

- **Outcome:** [What measurable result this goal achieves]
- **Impact metric:** [How we measure progress — metric name and baseline]
- **Outcome metric:** [Success threshold — target value and current value]
- **Horizon:** [Short / Medium / Long]
- **Status:** [Active / Achieved / Paused]

### G2: [Goal Name]

- **Outcome:** [What measurable result this goal achieves]
- **Impact metric:** [How we measure progress]
- **Outcome metric:** [Success threshold]
- **Horizon:** [Short / Medium / Long]
- **Status:** [Active / Achieved / Paused]

## Idea Bank

Ideas are linked to goals via the `Goal` column. Each gets an ICE score (see `docs/governance/ice-scoring-guide.md`). Tasks can reference ideas via the optional `roadmap_idea` frontmatter field.

**Status lifecycle:** `/spine-plan` sets `In Progress` when a task links `roadmap_idea`; `/spine-harvest` sets `Done` when no other open linked tasks remain. ICE/Confidence/Impact changes stay in `/spine-roadmap`.

| ID  | Idea | Goal | ICE | Confidence | Status    |
|-----|------|------|-----|------------|-----------|
| I1  | [Idea description] | G1 | [I×C×E] | [1–10] | [Candidate / In Progress / Done] |
| I2  | [Idea description] | G2 | [I×C×E] | [1–10] | [Candidate / In Progress / Done] |

## Review Log

| Date | Goal/ID | Change |
|------|---------|--------|
| YYYY-MM-DD | — | Template created |
