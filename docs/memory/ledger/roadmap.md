---
last_updated: 2026-11-14
last_reviewed: 2026-11-14
review_cadence: monthly
goals_active: 6
ideas_total: 33
ice_method: "Impact × Confidence × Ease (1–10 each). See templates/docs/governance/ice-scoring-guide.md."
sources:
  - docs/documentation/evolucao/feedback-261111.txt
  - docs/documentation/evolucao/hooks-and-summaries.md
  - docs/documentation/evolucao/files/RFC-001-spine-evolution.md
  - docs/documentation/evolucao/files/RFC-001-tasks.md
  - docs/documentation/evolucao/spine-framework-improvement-proposal.md
  - docs/documentation/evolucao/spine-cloud-vision.md
---

# Roadmap

> Consolidates the evolution documents in `docs/documentation/evolucao/`.
> Latest shipped release: **v2.2.0** (cross-platform installer + execution record).
> RFC-001 release numbers are shifted by one (its "v2.2" is now v2.4, etc.) because v2.2.0 shipped with different scope.
> `spine-cloud-vision.md` (2026-07-29) is **superseded by RFC-001** (2026-10-28): same repo, git owns execution, Supabase owns coordination, metadata-only projection, no bidirectional sync.

## Goals

### G1: Lean context

- **Outcome:** Context loaded at session start stays small and flat as a consumer project grows.
- **Impact metric:** Characters read by Core SYNC per session (baseline to measure on AgentHub — I1).
- **Outcome metric:** Core SYNC ≤ 8,000 chars and growth < 10% between task 20 and task 50.
- **Horizon:** Short
- **Status:** Active

### G2: Deterministic automation

- **Outcome:** Mechanical steps (validation, preflight, indexing, guard rails) run as scripts/hooks instead of prompt prose.
- **Impact metric:** Number of command steps executed by a script; memory-format errors found at harvest.
- **Outcome metric:** Zero frontmatter/tag errors reaching harvest; preflight and validation scripted in all Spine commands.
- **Horizon:** Short / Medium
- **Status:** Active

### G3: Trustworthy delivery closure

- **Outcome:** A DONE task always carries structured evidence and no orphan operational follow-up.
- **Impact metric:** % DONE tasks with complete evidence; open follow-ups without owner/ETA.
- **Outcome metric:** 100% evidence; zero follow-ups without owner/ETA (AgentHub proposal success criteria).
- **Horizon:** Short
- **Status:** Active (partially delivered by v2.2.0 execution record)

### G4: Team-ready (multi-dev)

- **Outcome:** Several developers work on the same project without structural conflicts.
- **Impact metric:** Merge conflicts in memory files; duplicated task IDs.
- **Outcome metric:** Two devs, one week, same project, zero structural conflicts (RFC-001 P4).
- **Horizon:** Medium
- **Status:** Active

### G5: Lower review load

- **Outcome:** Human review effort is proportional to risk; work is grouped in epics.
- **Impact metric:** Average human review time per task; % tasks linked to an epic.
- **Outcome metric:** Low-risk tasks closed without a plan gate; 100% of large initiatives under an epic (RFC-001 P1, P2).
- **Horizon:** Medium
- **Status:** Active

### G6: Central coordination

- **Outcome:** Requests born outside the repo become tasks in one command; cross-project visibility.
- **Impact metric:** Manual copy steps from ticket to task.
- **Outcome metric:** Request → task in one command (RFC-001 P5).
- **Horizon:** Long
- **Status:** Active (after G4/G5)

### G7: Parallel execution

- **Outcome:** Independent tasks of an epic run in parallel with independent verification.
- **Impact metric:** Tasks executed concurrently without merge conflict.
- **Outcome metric:** Two independent tasks executed, verified and merged in parallel (RFC-001 P3).
- **Horizon:** Long
- **Status:** Paused until G5 is stable

## Idea Bank

**Status lifecycle:** `/spine-plan` sets `In Progress` when a task links `roadmap_idea`; `/spine-harvest` sets `Done` when no other open linked tasks remain.

| ID  | Idea | Goal | ICE | Confidence | Status |
|-----|------|------|-----|------------|--------|
| I1  | Measure baseline: chars/tokens of Core SYNC and of each growing file on AgentHub (prerequisite for budgets) — shipped as `spine.py memory stats` in 018 | G1 | 432 (6×9×8) | 9 | Done |
| I2  | Summary-first frontmatter (`summary`, `entries`, `last_entry`, `budget_chars`) on growing files + task `summary` — narrative `summary:` shipped in 018; `entries`/`last_entry` made obsolete by I25 `INDEX.md`; remaining: task `summary` | G1 | 105 (3×5×7) | 5 | Candidate |
| I3  | Generated `docs/memory/digest.md` (`spine.py memory digest`); Core SYNC reads digest first | G1 | 432 (8×9×6) | 9 | Done |
| I4  | Memory budgets in `spine_validate.py memory` + harvest compaction step | G1 | 336 (6×8×7) | 8 | Done |
| I5  | Generated indexes: `completed_tasks/INDEX.md`, `ledger/learnings-index.md` — learnings index shipped in I25; remaining: `completed_tasks/INDEX.md` (on-demand tier) | G1 | 147 (3×7×7) | 7 | Candidate |
| I6  | Rolling window + archive (`progress`, `decision-log`, roadmap Review Log) via `spine.py memory compact`; agent writes period summary — log archive replaced by I25 entries; remaining: roadmap Review Log, pre-v2.1 `progress.md` sections | G1 | 90 (3×5×6) | 5 | Candidate |
| I7  | Generated short `AGENTS.md` entry file (summary + pointers, ≤ 4k chars, never rule copies) + `CLAUDE.md` `@AGENTS.md`; optional per-directory | G1 | 210 (6×5×7) | 5 | Candidate |
| I8  | git `pre-commit` memory validation (agent-neutral) | G2 | 320 (5×8×8) | 8 | Candidate |
| I9  | Hook: validate-on-edit for `docs/memory/**` (H2) | G2 | 294 (6×7×7) | 7 | Candidate |
| I10 | Preflight script (fetch, ahead/behind, branch vs task) + prompt hook on `/spine-*` (H3, RFC SPN-22-04) | G2 | 294 (6×7×7) | 7 | Candidate |
| I11 | Hook: inject digest at session start and before compaction (H1) — needs I3, I12 | G2 | 252 (7×6×6) | 6 | Candidate |
| I12 | Hook runtime `spine.py hook <event>` with per-agent adapters + `install --with-hooks` + `spine_validate.py hooks` | G2 | 210 (7×6×5) | 6 | Candidate |
| I13 | Hook guard rails: protected branches, `completed_tasks/`, `.env` (H4) | G2 | 180 (5×6×6) | 6 | Candidate |
| I14 | Command/prompt lint: repeated instructions, contradictions, actions without precondition | G2 | 144 (4×6×6) | 6 | Candidate |
| I15 | Human summary block (≤ 10 lines) in `/spine-plan` and `/spine-harvest` (RFC SPN-23-04) | G5 | 336 (6×7×8) | 7 | Candidate |
| I16 | Harvest cleanup: remove redundancy; split docs closure vs git closure (AgentHub A.1) | G3 | 252 (6×7×6) | 7 | Candidate |
| I17 | Formal quality gates in harvest → "partial harvest" with listed blockers (AgentHub A.2) | G3 | 252 (6×6×7) | 6 | Candidate |
| I18 | Operational follow-ups with owner/ETA/closing criterion in execution evidence (AgentHub B.1/B.3 delta over v2.2.0) | G3 | 210 (5×6×7) | 6 | Candidate |
| I19 | PR template mirrors execution evidence (AgentHub F) | G3 | 192 (4×6×8) | 6 | Candidate |
| I20 | Hook: execution-record nudge at end of turn while `IN_PROGRESS` (H5) | G3 | 150 (5×5×6) | 5 | Candidate |
| I21 | `/spine-memory-audit` (AgentHub A.3) | G3 | 125 (5×5×5) | 5 | Candidate |
| I22 | Skill usage record + scorecard + contextual recommendation (AgentHub C.1–C.3) | G3 | 80 (4×4×5) | 4 | Candidate |
| I23 | Unique task IDs (RFC SPN-22-01) | G4 | 280 (7×8×5) | 8 | Candidate |
| I24 | Ownership + claim via push (RFC SPN-22-03) | G4 | 216 (6×6×6) | 6 | Candidate |
| I25 | One-entry-per-file ledgers; `progress`/`learnings` become generated views reusing the I3 generator (RFC SPN-22-02) — shipped as `ledger/{decisions,learnings,deliveries}/` + generated `INDEX.md` (merge=union) + `memory migrate` | G4 | 224 (7×8×4) | 8 | Done |
| I26 | `risk: low\|medium\|high` + proportional human gate; absorbs lite/full templates (RFC SPN-23-03, AgentHub B.2) | G5 | 252 (7×6×6) | 6 | Candidate |
| I27 | Epic model + `/spine-epic` (DAG, derived status); hierarchy Goal → Epic → Task → Subtask (RFC SPN-23-01/02 + feedback) | G5 | 168 (7×6×4) | 6 | Candidate |
| I28 | Supabase schema + RLS + `spine` CLI + git → Supabase projection (RFC SPN-24-01..03) | G6 | 90 (6×5×3) | 5 | Candidate |
| I29 | `/spine-inbox` requests → PLANNING tasks with `origin` (RFC SPN-24-04) | G6 | 120 (6×5×4) | 5 | Candidate |
| I30 | Read-only decision-oriented dashboard (RFC SPN-24-05) | G6 | 100 (5×5×4) | 5 | Candidate |
| I31 | Cross-project tasks and portable learnings (cloud vision §3; RFC open question 5) | G6 | 30 (5×3×2) | 3 | Candidate |
| I32 | Parallelism: `touches`, worktree per task, orchestrator, independent verifier (RFC SPN-25-01..04) | G7 | 56 (7×4×2) | 4 | Candidate |
| I33 | Spine Cloud as separate commercial product (fork) | G6 | 6 (3×2×1) | 2 | Candidate — parked |

## Release sequence (proposed)

| Release | Theme | Ideas | Notes |
|---------|-------|-------|-------|
| **v2.3** | Lean context + deterministic basics | I1 → I2 → I3 → I4 → I5, I8, I9, I10, I15, I16 | Highest ICE, solo value, no format break. I1 first to set budgets from data. |
| **v2.4** | Hooks across agents + closure quality | I12, I11, I13, I17, I18, I6, I7, I19 | Claude Code first, then Cursor/OpenCode, Antigravity last. Commands keep working without hooks. |
| **v2.5** | Multi-dev (RFC "v2.2") | I23, I24 (I25 shipped early, non-breaking) | Format changes migrate through explicit commands with a dry run (`spine.py memory migrate`); `update` only hints (DEC 2026-11-14-memory-migrate-explicit-all-or-nothing). Pin tags. |
| **v2.6** | Epics + risk review (RFC "v2.3") | I26, I27, I20, I21 | Subtasks added to the epic model. |
| **v2.7** | Supabase coordination (RFC "v2.4") | I28, I29, I30 | Metadata only; RLS from day one. |
| **v2.8** | Parallelism (RFC "v2.5") | I32 | Requires v2.6 stable. |
| Parked | — | I14, I22, I31, I33 | Revisit at monthly review. |

## Review Log

| Date | Goal/ID | Change |
|------|---------|--------|
| 2026-11-11 | — | Replaced legacy milestone list (Base Operacional, Memory-Bank Operacional, Ciclo Piloto) with GIST roadmap consolidating `docs/documentation/evolucao/`. Legacy milestones considered delivered or obsolete (pilot cycle covered by AgentHub). |
| 2026-11-11 | — | RFC-001 releases renumbered +1 (v2.2.0 already shipped). `spine-cloud-vision.md` marked superseded by RFC-001. |
| 2026-11-11 | I18 | Scoped as delta over v2.2.0 execution evidence (owner/ETA/closing criterion only). |
| 2026-11-11 | I3 | Planned as task 018-memory-digest (In Progress); folds in I1 baseline and I2 summary frontmatter |
| 2026-11-12 | I3 | Harvested task 018-memory-digest → Done. Digest goes to stdout (no committed `digest.md`); I1 baseline shipped as `memory stats`, I2 shipped as narrative `summary:` only (no `entries`/`last_entry`/`budget_chars`, no task `summary`) |
| 2026-11-13 | I4 | Planned as task 020-memory-budgets (In Progress); digest-first budgets, harvest compacts Current state only, archive stays in I6 |
| 2026-11-14 | I4 | Harvested task 020-memory-budgets → Done. `spine_validate.py memory` + harvest step 4a.1; log-file budgets warn on all three real projects (input for the per-entry ledger plan that replaces I6's archive) |
| 2026-11-14 | I25 | Planned as task 021-per-entry-ledger (In Progress); ledger/{decisions,learnings,deliveries}/ + generated INDEX.md (merge=union); migrate is a follow-up task |
| 2026-11-14 | I25 | Harvested task 021-per-entry-ledger — still In Progress: `spine.py memory migrate` (split legacy files) is the remaining I25 work, not yet planned |
| 2026-11-14 | I25 | Planned as task 022-memory-migrate (In Progress); dry run by default, `--apply` writes entries and removes legacy files, title-capped summaries, `update` hints only |
| 2026-11-14 | I25 | Harvested task 022-memory-migrate → Done. `spine.py memory migrate [--apply]` shipped; 395 entries migrated on 4 scratch banks, Spine's own bank migrated (24 entries) |
| 2026-11-14 | — | Review (--review). Evidence from 7 real banks: digest 4.3k–13.7k chars vs legacy Core SYNC 56k–414k (−92% to −98%). Still over 8,000: onboarding-hub 13.7k, agenthub 10.6k, ansible 8.0k. The excess is Current state (5.4k/6.6k vs 1,500) and open tasks (4.7k on onboarding-hub), not logs: migrating barely changes digest size (−86 to −516). goals_active recounted 7 → 6 (G7 Paused). |
| 2026-11-14 | I1, I3, I4 | Confidence raised from delivery evidence: I1 8→9 and Done (baseline measured with `memory stats` in 018; Status corrected), I3 7→9 (−92..98% on 7 banks), I4 7→8 (validator names the real overrun causes). |
| 2026-11-14 | I25 | Confidence 7→8: real-git union-merge test, plus 395 entries migrated on 4 banks and 24 on Spine. G4's two-dev week is still untested. |
| 2026-11-14 | I2, I5, I6 | Impact lowered after I3/I25 shipped most of their scope: I2 343→105 (remaining: task `summary`), I5 245→147 (remaining: `completed_tasks/INDEX.md`), I6 216→90 (remaining: Review Log and pre-v2.1 progress sections). |
| 2026-11-14 | v2.5 | Release note corrected: migration is an explicit command (`memory migrate`), not part of `update`; I25 shipped ahead of v2.5. |
| 2026-11-14 | G1 | Stays Active: 3 of 7 banks over 8,000; growth between task 20 and task 50 not yet measurable. Gaps not covered by any idea (use `--add-ideas`): stale open-task lists in the digest, Current state compaction for banks that skip harvest, and the 3,000-char narrative budget (real narrative files run 4k–26k, so it warns on most files of every consumer bank). |
