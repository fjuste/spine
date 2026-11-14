---
id: 2026-11-12-core-sync-reads-spine-py-memory-digest-stdout-only-instead
date: 2026-11-12
title: Core SYNC reads `spine.py memory digest` (stdout only) instead of every global file, the whole `progress.md` and open task bodies; narrative files carry an age…
summary: Core SYNC reads `spine.py memory digest` (stdout only) instead of every global file, the whole `progress.md` and open task bodies; narrative files carry an age…
tags: []
task:
superseded_by:
---

**Decision:** Core SYNC reads `spine.py memory digest` (stdout only) instead of every global file, the whole `progress.md` and open task bodies; narrative files carry an agent-written `summary:` frontmatter, log files are summarized deterministically (entry count + newest 5 titles)

**Why:** Measured legacy Core SYNC reached ~422k chars (~105k tokens) on the largest consumer; digest is 5–13k chars (92–98% less) and needs no summarizing of 100k-char logs. Stdout avoids staleness and merge conflicts of a committed file; missing summaries are written by the agent in paced SETUP batches (60k source chars per session), so existing projects need no migration step

**Alternatives considered:** Committed `docs/memory/digest.md` (stale, conflicts in multi-dev), agent-written summaries on log files too (setup too large), "read only Current state" as prose rule (not enforceable)
