---
id: 2026-11-12-018-memory-digest
date: 2026-11-12
title: Memory digest — summary-first Core SYNC for growing memory banks
summary: Memory digest — summary-first Core SYNC for growing memory banks
tags:
  - type/feature
  - area/memory
  - stack/python
task: 018-memory-digest
---

**Task:** 018-memory-digest | **Branch:** feature/memory-digest
**Tags:** type/feature, area/memory, stack/python
**Description:** New stdlib-only `spine.py memory stats|digest` (`scripts/spine_cli/memory.py`). `digest` prints progress Current state, one line per open task (`NNN | STATUS | title — goal`), narrative `summary:` frontmatter or a capped outline, log entry counts with the newest 5 titles (heading and table-row formats), Extended-tier pointers, and a paced `SETUP:` block (largest-first, `--budget` default 60,000 chars) asking the agent to write missing summaries. `stats` prints per-file chars, the legacy Core total and the digest size. `rules/02-memory-bank.md` Core tier is digest-first with the legacy list as fallback, plus a new § Narrative summaries; `01-core-protocol.md`, `/spine-bootstrap`, the 5 narrative templates (`summary:` placeholder), README and AGENTS.md updated. Evidence: `pytest -q tests/` 222 passed (52 new in `test_memory_digest.py`). Manual read-only runs by the agent on 2026-11-11 at `b1ea53f`: onboarding-hub 421,762 → 13,039 chars (97%), intelligence-engine 209,066 → 5,076 (98%), agenthub 129,093 → 10,522 (92%); raw output was in the session scratchpad (temporary), reproducible with the same commands. Roadmap I3 → Done. Graphify and MkDocs not active.
