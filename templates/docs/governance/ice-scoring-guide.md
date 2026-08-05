# ICE Scoring Guide

Used by `/spine-roadmap` to score and prioritize ideas in the Idea Bank. ICE stands for **Impact**, **Confidence**, and **Ease**. Each dimension is scored 1–10 with objective criteria.

**Honesty principle:** Score based on evidence, not optimism. When evidence is thin, lower Confidence — never inflate to make an idea "look better." Re-score after delivery to reflect new information.

## When to Use

- `/spine-roadmap` fill mode: score each idea during strategic discovery
- `/spine-roadmap --add-ideas`: score new ideas against existing goals
- `/spine-roadmap --review`: re-evaluate scores based on delivery evidence

## Score = Impact × Confidence × Ease

Each dimension gets a raw 1–10 score. The final ICE score is the product (1–1000). Higher = more valuable to do next.

## Impact (1–10)

How much does this idea move the needle on its Goal's outcome metric?

| Score | Criteria |
|-------|----------|
| 1–2 | Cosmetic or invisible to the outcome metric. No measurable effect. |
| 3–4 | Minor improvement. Single-digit percentage gain on the outcome metric. |
| 5–6 | Meaningful lift. 10–30% gain on the outcome metric. |
| 7–8 | Large lift. 30–60% gain on the outcome metric. Unlocks adjacent goals. |
| 9–10 | Transformative. 2x+ gain on the outcome metric. Enables entire new capabilities. |

**Anchor questions:**
- Does this directly change the Outcome metric defined in the Goal?
- If we ship this and nothing else, does the metric move?
- Is this a prerequisite for other high-impact ideas?

## Confidence (1–10)

How certain are we that this idea will produce the claimed Impact?

| Score | Criteria |
|-------|----------|
| 1–2 | Pure guess. No evidence, no precedent. |
| 3–4 | Weak signal. One anecdote, vague competitor behavior, or a single user request. |
| 5–6 | Moderate signal. Multiple user requests, consistent qualitative feedback, or an analogous success in a different context. |
| 7–8 | Strong signal. Quantitative data (analytics, A/B test, cohort analysis) supports the hypothesis. Clear problem-to-solution chain. |
| 9–10 | Proven. We or a direct competitor have already validated this exact solution in a similar context. |

**Anchor questions:**
- What data supports this (quantitative or qualitative)?
- Have we tested any part of this before?
- What would falsify this idea? How would we know?

## Ease (1–10)

How fast can we deliver this? Score inversely to effort (10 = trivial, 1 = massive).

| Score | Criteria |
|-------|----------|
| 1–2 | Multi-month effort. Cross-team coordination, infra changes, or dependency on external milestones. |
| 3–4 | Weeks of work. Significant new code, complex integration, or data migration. |
| 5–6 | Days of work. Self-contained feature, moderate complexity, limited surface area. |
| 7–8 | Hours of work. Simple change, well-understood component, clear implementation path. |
| 9–10 | Minutes of work. Config change, copy update, or toggle flip. |

**Anchor questions:**
- Can one person build this in a single task?
- Are there unknown unknowns (new API, new dependency, new area of the codebase)?
- Does it require coordination beyond the implementer?

## ICE Score Interpretation

| ICE Range | Label | Action |
|-----------|-------|--------|
| 500–1000 | Must-do | Prioritize in next /spine-plan cycle |
| 200–499 | Should-do | Queue for upcoming cycles |
| 50–199 | Could-do | Revisit after high-ICE ideas ship |
| 1–49 | Won't-do now | Archive or re-scope; may become relevant after context change |

## Usage in /spine-roadmap

1. **Fill mode:** For each goal in `## Goals`, brainstorm ideas. Score each idea using this guide. Add to `## Idea Bank` table.
2. **Review mode:** Re-read ideas linked to delivered tasks. Update Confidence based on what was learned. Adjust Impact if delivery evidence changed assumptions. Update `last_reviewed` in roadmap frontmatter.
3. **Add-ideas mode:** Same scoring discipline as fill mode, but append to existing goals without re-scoring the full bank.

## Re-score Rule

After completing a task that was linked to a roadmap idea (via `roadmap_idea` in task frontmatter):

1. `/spine-harvest` updates Idea Bank **Status** to `Done` when no other open linked tasks remain (factual lifecycle only).
2. Run `/spine-roadmap --review` to update Confidence (and Impact if needed) for the linked idea based on delivery outcome.
3. Review may confirm Status and mark Goals `Achieved` when outcome metrics are met — it does not replace harvest’s Status update.

Harvest does **not** change ICE product, Confidence, or Impact columns.
