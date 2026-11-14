---
id: LEARN-003
date: 2026-11-14
title: git add -A on a path stages someone else's untracked files
summary: git add -A <path> stages every untracked file under that path; stage named files when the tree holds untracked work that isn't yours.
tags:
  - type/incident
  - area/infra
task: 021-per-entry-ledger
---

**Symptoms:** A task commit included 227 unrelated files from the user's untracked `skills/synced/` folder.

**Root cause:** `git add -A rules commands skills …` stages untracked files under each given path, not only the files the task changed.

**Detect early:** Before committing, check `git status --short` for `A` lines the task did not create; when the session started with `??` entries, assume they are not yours.

**Prevention:** Stage with `git add -u -- <paths>` plus explicitly named new files, or list files one by one. Never use `-A` on a directory that holds pre-existing untracked work.

**Regression test:** none (process); `git show --name-only HEAD` before merge.

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
