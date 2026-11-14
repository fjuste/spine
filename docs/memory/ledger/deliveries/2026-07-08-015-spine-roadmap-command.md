---
id: 2026-07-08-015-spine-roadmap-command
date: 2026-07-08
title: Add /spine-roadmap command with GIST-informed template
summary: Add /spine-roadmap command with GIST-informed template
tags:
  - type/feature
  - area/workflow
  - area/docs
  - area/governance
task: 015-spine-roadmap-command
---

**Task:** 015-spine-roadmap-command | **Branch:** feature/spine-roadmap-command
**Tags:** type/feature, area/workflow, area/docs, area/governance
**Description:** Wired up the long-reserved `/spine-roadmap` slot. Created the command with fill, `--review`, and `--add-ideas` modes using grill-me strategic discovery. Replaced roadmap stub with GIST-informed template (Goals + Idea Bank with ICE scoring). Added `templates/docs/governance/ice-scoring-guide.md` with objective 1-10 scoring criteria. Updated bootstrap, rules, install/validate scripts, task template (`roadmap_idea` field), harvest (passive review suggestion), plan (idea-ID linking), README, and AGENTS.md. 13 files changed/created. 86/91 tests pass (5 pre-existing failures in `test_opencode_template.py` unrelated). Graphify and MkDocs inactive — not applicable.
