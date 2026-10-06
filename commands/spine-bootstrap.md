---
description: Deep project assessment and agent-optimized memory bank fill after spine.py install; optional $ARGUMENTS for briefing
agent: build
---

# Slash Command: /spine-bootstrap

Act as the project's Initial Assessment Architect.

**Goal:** Build a complete, **agent-ready** project context layer. Deep assessment of source code and Graphify (when present), then fill memory bank documents with maximal detail for **agent consumption** (tiered SYNC), not human storytelling.

**Bootstrap is not planning.** Do not create active tasks, plans, or modify `roadmap.md`. Delivery starts with `/spine-plan`.

**Optional context (`$ARGUMENTS`):** Non-empty free text = project briefing (domain, stack, constraints, stakeholders, links). Highest priority when filling files; do not contradict existing valid content.

**Precondition:** `python3 .spine/scripts/spine.py install` completed (symlinks, seeded `docs/`, `opencode.json`).

---

## Step 0 — Setup boundary and readiness

Run from project root:

```bash
python3 .spine/scripts/spine_validate.py bootstrap
```

Cross-platform Python 3.9+ (on Windows, if `python3` is unavailable, use `py -3` or `python`). `python3 .spine/scripts/spine_validate.py bootstrap` remains a thin wrapper.

**On success:** proceed to Step 1.

**On failure (bridge mode):**

1. Stop assessment.
2. Ask: "Setup incomplete. Run `python3 .spine/scripts/spine.py install` from the project root now?"
3. If yes: user runs install in terminal (not a slash command), reload IDE, re-run the script.
4. If no: list missing artifacts from script output and stop.

**Forbidden (agent must never):**

- Copy/seed `docs/` (`cp -R`, downloads, creating missing template files)
- Run `spine.py install` from the agent
- Modify [`docs/memory/ledger/roadmap.md`](../../templates/docs/memory/ledger/roadmap.md)
- Create or modify `docs/memory/active_tasks/NNN-*.md` (numbered tasks)

**Re-bootstrap:** Safe to re-run. Idempotent enrichment — replace placeholders, append non-conflicting detail, preserve valid existing content.

---

## Step 1 — Deep assessment (mandatory, before any writes)

Goal: **complete project understanding**. Do not write memory bank files until assessment is sufficient.

**Discovery order:**

1. `$ARGUMENTS` (if non-empty)
2. **Graphify** when `graphify-out/graph.json` exists: follow `02-memory-bank.md` **Graphify Discovery Protocol** — read `GRAPH_REPORT.md`, run `graphify query` for architecture/modules/entry points/integrations, confirm with targeted file reads. Run `python3 .spine/scripts/spine_validate.py graphify` and report per-IDE status in the summary.
3. **Source and configs:** README, manifests, CI, infra, entry points, layer structure, tests, env patterns
4. Existing memory bank (re-bootstrap) — conflicts → **Gaps**, do not silently overwrite

**Assessment must cover:**

| Area | Feeds |
|------|--------|
| Stack (languages, frameworks, DB, queue, infra, deploy) | `system-patterns.md`, `tech-context.md` |
| Architecture (layers, data flow, external APIs) | `system-patterns.md` |
| Domain terms and bounded contexts | `domain-glossary.md` |
| Dev workflow (install, run, test commands) | `tech-context.md` |
| **Alterations** (custom payment, auth, webhooks vs platform default) | `system-patterns.md` § Project-Specific Alterations + `decision-log.md` |
| **Risks** (fragile integrations, missing tests, deprecated deps) | `tech-context.md` § Known Risks |
| **Opportunities** (unplanned improvements, not scheduled work) | `product-context.md` § Known Opportunities (unplanned) |
| Scope, goals, boundaries | `project-brief.md`, `product-context.md` |
| Git default branch vs Spine GitFlow (`develop` + `feature/*`) | `tech-context.md`, summary **Gaps** if mismatch |
| Graphify status (active / stale / absent; check `graphify-out/`, `graphify-out/graph.json`, `.graphifyignore`) | `system-patterns.md`, summary |

**Hunt signals:** Graphify clusters; grep `TODO|FIXME|HACK|override|custom`; payment/checkout/auth/shipping directories; `$ARGUMENTS`.

**Depth bar:** If any global section would still read like `[Fill in]` after Step 2, assessment was insufficient — explore deeper.

**No `@grill-me`:** Unresolved domain ambiguity → **Gaps** + recommend `/spine-plan` with discovery triggers when delivery starts.

---

## Step 2 — Memory Bank bootstrap (global) — agent-optimized

**Primary audience: agents.** Structure for SYNC, grep, and navigation.

| Principle | Guidance |
|-----------|----------|
| Structure | Predictable headings per `02-memory-bank.md` Core SYNC |
| Specificity | Concrete paths, modules, config files, CLI commands |
| Glossary | Term + definition + code location hint |
| Architecture | Layer map, request/job flow, key files/classes |
| Alterations | Table in `system-patterns.md`; non-obvious WHY → `decision-log.md` entry; link both ways |
| Risks | Bullet list with impact and related paths |
| Opportunities | Unplanned improvements only (not roadmap milestones) |
| Cross-links | `See tech-context.md § Known Risks` |
| Scannable | Bullets and short paragraphs; no marketing tone |
| English | All generated content |
| Depth | **Maximize detail**; completeness over brevity |

**Fill rules:**

| Signal | Action |
|--------|--------|
| Placeholder (`[Fill in]`, empty section, template boilerplate) | Replace with detailed inferred content |
| Valid project-specific content already present | Preserve; append only non-conflicting detail |
| Conflict (repo vs `$ARGUMENTS` vs existing doc) | Do not overwrite; record in **Gaps** |
| `domain-glossary.md` | Add terms; never delete existing entries |
| `decision-log.md` | Append bootstrap baseline entry (date, baseline established, key facts + WHY) |

**Files to fill:**

- `docs/memory/global/project-brief.md`
- `docs/memory/global/product-context.md` (incl. § Known Opportunities (unplanned))
- `docs/memory/global/domain-glossary.md`
- `docs/memory/global/system-patterns.md` (preserve Graphify section; incl. § Project-Specific Alterations)
- `docs/memory/global/tech-context.md` (incl. § Known Risks)
- `docs/memory/global/decision-log.md`

If a new section is missing in an older consumer template, add the section during fill.

---

## Step 3 — Memory Bank bootstrap (ledger) — limited scope

**In scope:**

- `docs/memory/ledger/progress.md` — update **Current state** only: bootstrap complete, memory bank baseline ready, no active delivery tasks; **never wipe Delivery log**
- `docs/memory/ledger/learnings.md` — leave empty unless repo evidence supports an incident-style entry; flag in **Gaps** if file missing after install

**Out of scope:**

- **`docs/memory/ledger/roadmap.md` — do not modify** (seed template; use `/spine-roadmap`)
- **`active_tasks/NNN-*.md` — do not create**

---

## Step 4 — Mandatory summary

Always include:

- **Assessment coverage:** Graph queries, key dirs, configs explored; confidence level
- **Memory bank files filled:** Each updated `global/*` and ledger file with one-line depth note
- **Counts:** alterations documented, risks listed, opportunities captured
- **Intentionally untouched:** `roadmap.md` (not bootstrap scope)
- **Created vs. updated vs. preserved**
- **Gaps:** Credentials, business rules, stakeholder intent, branch policy exceptions, unresolved domain terms
- **Setup status:** `spine_validate.py bootstrap` result
- **Graphify status:** active / partial / absent; per-IDE integration (Cursor mdc, OpenCode plugin, Claude hook); whether `GRAPH_REPORT.md` was read and sample `graphify query` commands run; suggest README § Optional: Graphify if medium/large repo without Graphify
- **GitFlow note:** default branch vs Spine target (`develop` + `feature/*`)
- **Next step:** `/spine-plan <goal>` — bootstrap does not produce plans or tasks
- **Re-bootstrap:** idempotent enrichment only

If user asks for a plan, task, or roadmap: "Bootstrap builds agent context only. Use `/spine-plan` for delivery planning. Use `/spine-roadmap` to structure the roadmap."

---

## Knowledge mapping (reference)

| Concept | Primary home | When |
|---------|--------------|------|
| Project-specific alteration | `system-patterns.md` § Project-Specific Alterations | Bootstrap |
| WHY of alteration | `decision-log.md` | Bootstrap |
| Known risk | `tech-context.md` § Known Risks | Bootstrap |
| Opportunity (unplanned) | `product-context.md` § Known Opportunities | Bootstrap |
| Incident / recurrence | `learnings.md` | `/spine-harvest` only |
| Scheduled milestone | `roadmap.md` | `/spine-roadmap` |

---

## Acceptance criteria (command behavior)

- [ ] Runs `spine_validate.py bootstrap` before assessment
- [ ] Deep assessment of source code and Graphify (when present) before writing
- [ ] Fills `global/*` and ledger (`progress.md`, `learnings.md` if applicable) with agent-optimized detail
- [ ] Documents alterations, risks, and opportunities when evidence exists
- [ ] Does **not** modify `roadmap.md`
- [ ] No installation side effects; no active task or plan creation
- [ ] Preserves valid existing content; conflicts → **Gaps**
- [ ] Summary includes counts, untouched files, gaps, and `/spine-plan` handoff
- [ ] All generated content in English
