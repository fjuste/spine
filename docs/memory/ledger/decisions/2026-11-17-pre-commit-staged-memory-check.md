---
id: 2026-11-17-pre-commit-staged-memory-check
date: 2026-11-17
title: Memory format is enforced by an opt-in git pre-commit hook on the staged snapshot, blocking format errors only
summary: An opt-in git pre-commit hook validates the staged docs/memory/ snapshot; only format errors block; budgets and open tasks warn. Agent hooks stay out.
tags:
  - area/memory
  - area/workflow
task: 026-pre-commit-memory-validation
superseded_by:
---

**Context:** Memory-format errors (task contract, entry summaries, stale `INDEX.md`) surfaced only when an agent ran the validator, usually at harvest. Agents differ (Claude Code, Cursor, OpenCode, Antigravity) and humans commit too; no single agent hook covers them all (roadmap G2, I8).

**Decision:** A marked block in the git `pre-commit` hook runs `python3 .spine/scripts/spine_validate.py staged`. It checks the staged (index) snapshot, not the working tree, and only files whose content the commit changes. It blocks on task contract errors, missing or over-long entry `summary:` and a stale or missing `INDEX.md` in a touched ledger folder; budget and open-task problems print warnings. Installation is opt-in (TTY prompt, `--with-pre-commit`), like Graphify and MkDocs. Rule 01 forbids `--no-verify`.

**Why:** git is the one point every agent and human passes through. The staged snapshot catches the "fixed the file, forgot `git add`" case. Blocking only on deterministic format errors keeps false blocks rare; checking only changed files lets legacy content (Spine's tasks 008–014) stay until a human closes it with a pure `git mv`.

**Alternatives considered:** Per-agent edit hooks (I9, I11–I13) — one implementation per agent, humans not covered; kept as separate roadmap ideas. Checking the working tree — misses unstaged fixes and validates what is not committed. Blocking on budgets or open tasks — would block unrelated commits in every bank with legacy content. Hook managers (husky, the pre-commit framework) — extra dependency; the installer prints the manual line instead. Always-on install — a git hook is machine-local and intrusive; opt-in matches the other optional layers.

**Consequences:** Each clone enables the hook itself (`.git/hooks` is not versioned); `vendor` and Windows install do not install it. Commands that commit memory (`/spine-plan`, `/spine-harvest`) must leave a valid staged snapshot (LEARN-002). Validator bugs now block commits, e.g. `related_learnings` items counted as tags (Known Opportunities).
