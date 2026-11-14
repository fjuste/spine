---
id: 2026-11-14-022-memory-migrate
date: 2026-11-14
title: Memory migrate — split legacy decision-log, learnings and delivery log into ledger entries
summary: spine.py memory migrate splits legacy log files into ledger entries; dry run by default, --apply all-or-nothing; Spine's own bank migrated.
tags:
  - type/feature
  - area/memory
  - stack/python
task: 022-memory-migrate
---

**Branch:** feature/memory-migrate

**Description:** New `scripts/spine_cli/migrate.py` behind `spine.py memory migrate [--apply] [--project-root]`. It parses the legacy `global/decision-log.md` (`##`/`###` dated headings, bracketed dates, 4-column tables), `ledger/learnings.md` (`##`/`###` `LEARN-NNN`, `**First seen:**`/`**Data:**` dates) and the `progress.md` Delivery log, and ignores headings inside code fences. Each entry becomes one ledger file with task-021 frontmatter (`summary:` = title capped at 160; tags and task from `**Tags:**`/`**Task:**`) and its body copied verbatim. The default dry run reports entries, placeholders, dropped preamble, unparsed lines and id conflicts. `--apply` refuses (exit 1, nothing written) on unparsed text or conflicts; otherwise it writes the entries, removes the legacy files, cuts the Delivery log and runs `memory index`. `spine.py update` hints while legacy files remain. The `progress.md` budget warning stops pointing at migrate once the Delivery log is gone. Rule 02, harvest, update, README and AGENTS.md document the command. Evidence: `pytest -v tests/` 322 passed (31 new). Manual runs by the agent on 2026-11-14: dry run on the 11 surveyed projects left `git status` unchanged and the counts reconcile with the digest; `--apply` on scratch copies of onboarding-hub (220), agenthub (75), intelligence-engine (50) and juste (refused, then 50 after a hand fix) passed the validator, and all 395 files are valid YAML. Spine's own bank was migrated (24 entries, 0 validator warnings; backup in the session scratchpad, which is temporary). Follow-ups: hand-fix shapes remain in hetzner, ansible/medpedia, tf-dsbr-chatbot and juste; the roadmap v2.5 note still says "migration in `spine.py update`". Graphify and MkDocs not active.
