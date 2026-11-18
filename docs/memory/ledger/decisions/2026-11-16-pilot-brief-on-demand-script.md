---
id: 2026-11-16-pilot-brief-on-demand-script
date: 2026-11-16
title: The pilot brief is an on-demand script that agents show verbatim, not a committed file or a session hook
summary: spine.py brief computes project state from docs/memory/ and git on demand; rule 01 makes agents show it verbatim; no committed file, no SessionStart hook.
tags:
  - area/memory
  - area/workflow
task: 025-pilot-brief
superseded_by:
---

**Context:** At every session start the pilot asked the agent where the project stands and what is next. The facts already existed (Current state, deliveries, open tasks, git) but were spread over several files, written for agents, and the live state (branch, uncommitted changes) lived in no file.

**Decision:** `python3 .spine/scripts/spine.py brief` computes the answer on demand and prints it to stdout; only the recommended next step is stored, as `next_step` / `next_command` / `next_alternatives` in `progress.md` frontmatter written by `/spine-harvest` and `/spine-plan`. Rule 01 tells every agent to run the brief and show its output verbatim when the pilot asks, instead of composing the answer from memory files.

**Why:** A computed view never goes stale and costs the pilot zero tokens in a terminal; a rule works in every agent (Cursor, OpenCode, Claude Code, Antigravity) without installer changes, and verbatim output keeps agents from paraphrasing or inventing state.

**Alternatives considered:** A committed `brief.md` regenerated at harvest — goes stale when someone commits without harvesting and adds merge noise. A Claude Code `SessionStart` hook — Claude-only, and plain hook stdout goes to the model's context, not documented as shown to the user (checked 2026-11-16). A chat summary block at plan/harvest (original I15) — lost when the session closes.

**Consequences:** The brief appears only when the pilot asks or runs it; showing it automatically at session start waits for the hook runtime (roadmap I11/I12). The next step is only as fresh as the last harvest or plan, so both commands must keep writing it.
