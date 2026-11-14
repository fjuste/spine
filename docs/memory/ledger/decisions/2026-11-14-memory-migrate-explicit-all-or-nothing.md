---
id: 2026-11-14-memory-migrate-explicit-all-or-nothing
date: 2026-11-14
title: Legacy log migration is an explicit, all-or-nothing command that removes the legacy files
summary: spine.py memory migrate is a dry run by default; --apply refuses on unparsed text or ID conflicts, removes legacy files; update only prints a hint.
tags:
  - area/memory
  - type/feature
task: 022-memory-migrate
superseded_by:
---

**Context:** Task 021 froze `global/decision-log.md`, `ledger/learnings.md` and the `progress.md` Delivery log. Consumer projects hold hundreds of hand-written legacy entries in shapes that vary by project (headings at two levels, Portuguese tables, inner sub-headings, code fences).

**Decision:** `spine.py memory migrate` prints a plan and writes nothing. `--apply` computes the whole plan first and writes only when no line is unparsed and no entry id already exists. It then writes one entry per legacy entry (body verbatim, `summary:` = title), deletes the two legacy files, cuts only the Delivery log section and regenerates `INDEX.md`. `spine.py update` prints a hint and never migrates.

**Why:** Deleting the legacy files avoids two sources of truth, and git history keeps the originals. All-or-nothing with a refusal keeps entry text from being lost silently in odd shapes; a person fixes those few lines. An explicit step keeps each project's migration reviewable in its own diff.

**Alternatives considered:** Keep the legacy files after migrating (duplicate memory, digest still lists them). Skip or best-effort the unparsed text (silent loss). Migrate automatically during `update` (large unreviewed rewrites of consumer memory). Rewrite summaries with an LLM (non-deterministic, needs a model).

**Consequences:** Projects with month-only dates, undated headings or malformed table rows must be fixed by hand before `--apply`. Summaries are titles until an agent improves them. Projects that harvested into the new folders before migrating can hit id conflicts and must resolve them by hand.
