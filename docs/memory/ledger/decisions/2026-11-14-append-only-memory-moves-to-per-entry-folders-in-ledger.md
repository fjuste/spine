---
id: 2026-11-14-append-only-memory-moves-to-per-entry-folders-in-ledger
date: 2026-11-14
title: >-
  Append-only memory moves to per-entry folders in `ledger/` (`decisions/`, `learnings/`, `deliveries/`): one file per entry with frontmatter (`summary:` ≤ 160 c…
summary: >-
  Append-only memory moves to per-entry folders in `ledger/` (`decisions/`, `learnings/`, `deliveries/`): one file per entry with frontmatter (`summary:` ≤ 160 c…
tags: []
task:
superseded_by:
---

**Decision:** Append-only memory moves to per-entry folders in `ledger/` (`decisions/`, `learnings/`, `deliveries/`): one file per entry with frontmatter (`summary:` ≤ 160 chars, tags, task, `superseded_by` for decisions) plus a script-generated, committed `INDEX.md` merged with `merge=union`; `decision-log.md` leaves `global/`; `progress.md` keeps only Current state; old single files stay frozen until `spine.py memory migrate` splits them (task 021, roadmap I25)

**Why:** Agents read the index and open only the entries they need, so memory keeps its full detail: one entry is 0.4–4k chars vs log files of 13k–113k on real projects (50–70× less). Harvest creates files instead of reading and editing a large file. Date-slug IDs for decisions and deliveries and `merge=union` on INDEX.md let parallel branches harvest without conflicts

**Alternatives considered:** Rolling window + archive files (roadmap I6: archives are still large files to read), one large file with a better summary (on-demand reads stay whole-file), INDEX.md not committed (no browsable index), DEC-NNN counters (collide across branches)
