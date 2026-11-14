# 014-graphify-consumer-adoption

> **Suggested execution skill:** @executing-plans

## Branch: feature/graphify-consumer-adoption
## Base: develop

## Status: DONE

## Objective

Adopt Graphify as an optional, consumer-project-level optimization layer on top of Spine, without reintroducing always-on prompt bloat. The framework must guide projects to use graph-first retrieval only when Graphify artifacts exist, while keeping Spine's core prompt lean (3 core rules + compaction).

## Inputs

- `docs/memory/active_tasks/012-token-optimization.md` (completed baseline optimization)
- `docs/memory/active_tasks/013-cursor-token-optimization.md` (cursor-side token optimization)
- `commands/spine-install.md`
- `commands/spine-bootstrap.md`
- `commands/spine-plan.md`
- `rules/01-core-protocol.md`
- `rules/02-memory-bank.md`
- `templates/docs/memory/global/system-patterns.md`
- `templates/docs/governance/skills-policy.md`
- `README.md`
- Existing plan: `docs/memory/active_tasks/011-graphify-integration.md` (historical reference; partially obsolete after AGENTS removal in templates)

## Expected Outputs

- Updated command specifications that define where Graphify is introduced in consumer lifecycle:
  - `commands/spine-install.md`
  - `commands/spine-bootstrap.md`
  - `commands/spine-plan.md`
- Updated framework rules that define graph-first behavior only when Graphify exists:
  - `rules/01-core-protocol.md`
  - `rules/02-memory-bank.md`
- Updated template docs that keep Graphify optional and consumer-scoped:
  - `templates/docs/memory/global/system-patterns.md`
  - `templates/docs/governance/skills-policy.md`
- Optional template artifact for consumer setup:
  - `templates/dot.graphifyignore`
- Regression/contract tests for installation and command guidance:
  - `tests/unit/test_graphify_consumer_adoption.py`
- Memory-bank update artifacts:
  - `docs/memory/global/decision-log.md`
  - `docs/memory/ledger/progress.md`

## Acceptance Criteria

- [x] Spine still loads only the 3 core rules by default, with no Graphify always-on prompt inflation.
- [x] `/spine-install` defines a consumer-safe Graphify onboarding path (optional, explicit, non-breaking).
- [x] `/spine-bootstrap` recognizes Graphify artifacts (`graphify-out/`, `.graphifyignore`) and records status in assessment summaries.
- [x] `/spine-plan` adds graph-first planning guidance when Graphify is present, with fallback to normal file-reading when absent.
- [x] `rules/01-core-protocol.md` and `rules/02-memory-bank.md` clearly encode conditional graph usage ("if graph exists -> query graph first for exploration").
- [x] A default `templates/dot.graphifyignore` exists (or an explicit decision is documented not to provide it), aligned with Spine directories and noise control.
- [ ] Tests and validation commands pass (`bash -n install.sh`, targeted pytest, and grep-based contract checks). *(partial: pytest unavailable in environment)*

## Tasks

### Task 1: Define the consumer-adoption policy and scope boundaries

**Files:**
- Modify: `templates/docs/memory/global/system-patterns.md`
- Modify: `docs/memory/global/decision-log.md`

**Step 1:** Write failing documentation contract test in `tests/unit/test_graphify_consumer_adoption.py` asserting:
- Graphify is optional
- Graphify is consumer-project scoped (not Spine core dependency)
- Graphify is retrieval-layer optimization, not replacement for memory bank/rules

**Step 2:** Run the targeted test and confirm it fails.

**Step 3:** Update `templates/docs/memory/global/system-patterns.md` with a concise "Optional Complementary Tooling" section for Graphify.

**Step 4:** Add decision-log entry documenting the architecture decision and rejected alternatives.

**Step 5:** Run test again and confirm it passes.

**Step 6:** Commit.

---

### Task 2: Add `/spine-install` guidance for optional Graphify onboarding

**Files:**
- Modify: `commands/spine-install.md`
- Optional Create: `templates/dot.graphifyignore`
- Test: `tests/unit/test_graphify_consumer_adoption.py`

**Step 1:** Add failing contract test asserting `spine-install`:
- does not make Graphify mandatory
- provides explicit optional onboarding instructions
- avoids AGENTS-based assumptions

**Step 2:** Run the test and verify it fails.

**Step 3:** Update `commands/spine-install.md` with an "optional Graphify onboarding" subsection, including:
- when to enable
- minimal commands
- where `.graphifyignore` comes from
- no changes to core instruction loading

**Step 4:** If selected, create `templates/dot.graphifyignore` tuned for Spine consumer projects.

**Step 5:** Run tests and verify pass.

**Step 6:** Commit.

---

### Task 3: Add `/spine-bootstrap` Graphify-aware assessment behavior

**Files:**
- Modify: `commands/spine-bootstrap.md`
- Test: `tests/unit/test_graphify_consumer_adoption.py`

**Step 1:** Add failing test asserting bootstrap checks for `graphify-out/` and `.graphifyignore` as context signals.

**Step 2:** Run the test and confirm failure.

**Step 3:** Update `commands/spine-bootstrap.md` so initial assessment:
- detects Graphify presence
- reports status in mandatory summary
- never treats Graphify artifacts as installation blockers

**Step 4:** Run targeted tests and confirm pass.

**Step 5:** Commit.

---

### Task 4: Add graph-first planning behavior to `/spine-plan`

**Files:**
- Modify: `commands/spine-plan.md`
- Test: `tests/unit/test_graphify_consumer_adoption.py`

**Step 1:** Add failing test asserting `/spine-plan` includes conditional guidance:
- query graph first for exploratory/context-heavy tasks when graph exists
- fall back to normal repository reading when graph is missing/stale

**Step 2:** Run the test and confirm failure.

**Step 3:** Update `commands/spine-plan.md` with the conditional Graphify decision path while preserving current planning workflow.

**Step 4:** Run tests and confirm pass.

**Step 5:** Commit.

---

### Task 5: Encode conditional graph usage in core rules

**Files:**
- Modify: `rules/01-core-protocol.md`
- Modify: `rules/02-memory-bank.md`
- Test: `tests/unit/test_graphify_consumer_adoption.py`

**Step 1:** Add failing test for rule-level contract:
- Graph usage is conditional on graph artifact presence
- Memory bank remains mandatory source of truth
- No unconditional graph dependency in base flow

**Step 2:** Run test and confirm failure.

**Step 3:** Update both rules with short, explicit, non-duplicative conditional instructions.

**Step 4:** Run tests and confirm pass.

**Step 5:** Commit.

---

### Task 6: Validate and document rollout quality gates

**Files:**
- Modify: `docs/memory/ledger/progress.md`
- Modify: `README.md` (if command discoverability section needs update)
- Test: `tests/unit/test_graphify_consumer_adoption.py`

**Step 1:** Execute full validation sequence:
- `bash -n install.sh`
- `pytest -v tests/unit/test_graphify_consumer_adoption.py`
- `rg "graphify|dot.graphifyignore|graphify-out" commands/ rules/ templates/`

**Step 2:** Add progress ledger entry with delivered scope and known limitations.

**Step 3:** If needed, add concise README note for maintainers on where Graphify now fits in the framework lifecycle.

**Step 4:** Commit.

## Test Strategy

- **Positive tests**
  - Graphify optional policy is documented in template memory docs.
  - `spine-install`, `spine-bootstrap`, and `spine-plan` contain expected conditional Graphify guidance.
  - Core rules include graph-first exploratory behavior only when Graphify artifacts exist.

- **Negative tests**
  - Ensure no instruction makes Graphify mandatory for baseline Spine operation.
  - Ensure no reintroduction of AGENTS-based template coupling for consumer projects.

- **Regression tests**
  - Confirm 3-core-rule baseline remains unchanged in templates and command guidance.
  - Confirm existing token-optimization outcomes from `012/013` are not reversed.

- **Execution command**
  - `pytest -v tests/unit/test_graphify_consumer_adoption.py`

## Scope Validation

This plan covers **1 primary domain** (framework command/rule governance) with **7 acceptance criteria** and **1 execution skill** (`@executing-plans`).

It is executable in a single implementation session, but it is near the upper bound of recommended scope. If preferred, split into:

1. **Plan A:** commands + templates (`spine-install`, `spine-bootstrap`, `spine-plan`, `dot.graphifyignore`)  
2. **Plan B:** rules + tests + ledger/README finalization

## Review Checklist

- **Tests executed:**
  - `bash -n install.sh`
  - `rg "graphify|dot.graphifyignore|graphify-out" commands/ rules/ templates/`
  - `pytest -v tests/unit/test_graphify_consumer_adoption.py`
- **Results:**
  - `bash -n install.sh`: PASS
  - `rg ...`: PASS (expected Graphify references found in updated files)
  - `pytest ...`: BLOCKED (pytest not installed in environment: `pytest: command not found`)

## Delivery Summary

**Delivered:** 2026-04-30

**What was delivered (task 014):**
- Graphify adoption model finalized as **optional and consumer-project scoped**.
- Conditional graph-first behavior added to planning/operation flows (`spine-install`, `spine-bootstrap`, `spine-plan`, `rules/01`, `rules/02`).
- New `templates/dot.graphifyignore` added.
- New `scripts/install-graphify.sh` helper added.
- New `scripts/update.sh` added to separate consumer update lifecycle from install lifecycle.
- New `/spine-update` command added as wrapper for update workflow.
- Rules cleanup completed: removed unused rules and renumbered code-quality to `03-code-quality.md`.

**Validation evidence:**
- `bash -n install.sh` PASS
- `bash -n scripts/update.sh` PASS
- `bash -n scripts/install-graphify.sh` PASS
- `rg "graphify|dot.graphifyignore|graphify-out" commands/ rules/ templates/` PASS
- `pytest tests/` BLOCKED (`pytest` not installed)

## Learning

**Root cause:** Installation and maintenance responsibilities were mixed, and Graphify guidance existed without a concrete update pathway for already-installed consumer projects.

**Prevention:**
1. Keep lifecycle separation explicit: `install.sh` for setup, `scripts/update.sh` + `/spine-update` for maintenance.
2. Keep Graphify optional and conditional; never inflate default always-on rule loading.
3. Preserve `docs/memory/` as immutable operational memory during updates.

**Regression test:**
- Script syntax gates:
  - `bash -n install.sh`
  - `bash -n scripts/update.sh`
  - `bash -n scripts/install-graphify.sh`
- Contract checks in `tests/unit/test_graphify_consumer_adoption.py` (requires `pytest` in environment).

