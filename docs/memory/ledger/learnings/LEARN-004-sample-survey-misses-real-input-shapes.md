---
id: LEARN-004
date: 2026-11-14
title: A parser built from a sampled survey misses real input shapes
summary: Rules drawn from a sample of legacy files missed 4 shapes and blocked 4 empty templates; dry-run the parser on every available real input early.
tags:
  - type/rework
  - area/memory
  - stack/python
task: 022-memory-migrate
---

**Symptoms:** `spine.py memory migrate` passed every unit test built from the 11-project survey. The first dry run over all 27 local memory banks then found `## DATE — Title` decision headings, bracketed dates (`### [2026-04-15] - …`), learnings dated with `**Data:**`, and `# comments` inside code fences that were read as headings. A rule added beyond the plan (text in files with no entries is unparsed) also blocked `--apply` on 4 banks holding only an intro note.

**Root cause:** Parser rules and fixtures came from a sample of the inputs, plus one unplanned strictness rule; neither had met the full set of real files before the code was written.

**Detect early:** A parser or migration whose inputs are hand-written files across many projects, where the survey covered only part of them.

**Prevention:** As soon as the parser runs, dry-run it on every real input you can read (read-only) and list unparsed and placeholder lines per file before committing. Turn each new shape into a fixture test. Do not add rules the plan did not ask for without a real file that needs them.

**Regression test:** `tests/unit/test_memory_migrate.py::test_parse_h2_and_bracketed_date_decisions`, `test_intro_text_without_entries_is_preamble`, `test_headings_inside_code_fences_stay_in_body`.

**Recurrences:**
- (append-only — one line per recurrence with date and task ref)
