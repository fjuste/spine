---
id: 2026-11-14-021-per-entry-ledger
date: 2026-11-14
title: Per-entry ledger — one file per decision, learning and delivery with a generated INDEX.md
summary: ledger/{decisions,learnings,deliveries}/ with generated, committed INDEX.md (merge=union); legacy log files frozen.
tags:
  - type/feature
  - area/memory
  - stack/python
task: 021-per-entry-ledger
---

**Branch:** feature/per-entry-ledger

**Description:** Append-only memory moves to `docs/memory/ledger/{decisions,learnings,deliveries}/`: one Markdown file per entry with frontmatter (`id`, `date`, `title`, one-line `summary:` ≤ 160 chars, `tags`, `task`, `superseded_by` for decisions). `spine.py memory index` regenerates each folder's committed `INDEX.md` (newest first, superseded decisions marked, learning recurrence counts); the installer (`install`, `--copy`, `vendor`, `update`; not the self-install) adds `docs/memory/ledger/*/INDEX.md merge=union` to `.gitattributes`. The digest lists the folders and labels legacy single files; `spine_validate.py memory` warns on missing/long summaries and stale indexes, and points over-budget legacy files to `spine.py memory migrate`. Seeds: folder `_template.md` + `INDEX.md`, Current-state-only `progress.md`, no `decision-log.md`/`learnings.md`. Rules, commands (harvest step 4c.1 now runs `memory index` then the budget check), skills, templates, README and AGENTS.md describe the layout; a sweep test keeps old-file mentions on "legacy" lines. Evidence: `pytest tests/` 291 passed (39 new ledger tests incl. a real-git union-merge test whose control without `merge=union` conflicts). Manual runs by the agent on 2026-11-14 at `0cc3257`: digest and validator exit 0 on onboarding-hub, agenthub and intelligence-engine with legacy labels, `git status docs/memory` unchanged; fresh scratch install seeded the folders, flagged stale indexes, `memory index` fixed them, validator OK. Raw output in the session scratchpad (temporary). Graphify and MkDocs not active.
