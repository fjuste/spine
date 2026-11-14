---
id: 2026-11-14-spine-memory-bank-is-versioned-and-public
date: 2026-11-14
title: Spine's own memory bank is versioned and public; confidential content stays out of it
summary: docs/memory and docs/governance are tracked in the public repo; docs/documentation and docs/discovery stay ignored; no client or private-project data in memory.
tags:
  - area/memory
  - area/workflow
task:
superseded_by:
---

**Context:** `/docs/` was gitignored to keep Spine's memory private, but globals, `progress.md`, `roadmap.md`, ledger entries and indexes had been force-added and pushed. The repository is public, so part of the memory was already public, while task files and new entries were silently left out of commits. GitHub has no per-branch visibility, so keeping develop/staging/production private with only `master` public is not possible in one repository.

**Decision:** Version Spine's memory bank (`docs/memory/`, `docs/governance/`) openly in the public repository. Keep `docs/documentation/` (personal notes) and `docs/discovery/` (third-party research clones) gitignored. Never record confidential content in the memory: client or employer names, private project names, local paths outside the repo, secrets. Existing task files were redacted before the first commit.

**Why:** The content is Spine's own roadmap, decisions and deliveries; nothing in it needs protection, and it is the best public example of Spine in use. A private memory repo would add a second repository, cross-repo `git mv` at harvest and a force-push history purge to protect non-sensitive content that was already public.

**Alternatives considered:** Separate private repository for `docs/` (extra repo and harvest friction). Private repository plus a filtered public mirror of `master` (merges carry `docs/` history; every release needs a history rewrite). Keep the ignore with force-adds (memory partly public anyway, new files silently untracked).

**Consequences:** Plain `git add docs/memory/...` works; harvest's `git mv` to `completed_tasks/` is tracked. Agents must refer to consumer projects generically when recording evidence. Consumer projects are unaffected: their memory is versioned with their code and follows their repository's visibility.
