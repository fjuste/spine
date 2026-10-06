# SPINE

SPINE is the backbone framework on top of which agents operate.

It is a reusable instruction and workflow repository for local projects, designed for solo development with predictable execution, low coupling, and pragmatic quality controls. It started as a personal operating system and is now shared with the community.

## Why SPINE Exists

This repository centralizes:
- delivery workflow (adapted GitFlow for solo development);
- skill governance (minimal allowlist and controlled trials);
- quality guardrails (test-first validation discipline);
- memory-bank structure for context, decisions, and continuous learning.

The goal is to avoid rebuilding process from scratch on every new repository.

## Core Principles

- Simplicity first: no overengineering.
- Minimal rules, but non-optional.
- Opt-in per project: Spine rules are only loaded when a project explicitly opts in.
- Every delivery leaves quality evidence (test + memory + decision).
- Lessons learned become operational standards.

## Repository Layout

```text
spine/
├── templates/
│   └── docs/
│       ├── memory/ (empty templates for bootstrap)
│       ├── governance/
│       ├── quality/
│       └── workflow/
├── docs/ (internal Spine use - not versioned)
├── commands/
│   ... (execution command templates)
├── agents/
│   ... (OpenCode agent definitions, e.g. ask.md)
├── skills/
│   ... (curated skill repository)
├── rules/
│   ... (source-of-truth rules in .md)
├── scripts/
│   ... (maintenance scripts)
└── tests/
```

## Setup

Spine installs **per project only**. Each consumer repository links to a local Spine clone via `.spine` and receives its own symlinks for rules, commands, and skills.

### 1. Clone Spine (machine-local)

Clone the Spine repository once on your machine (outside consumer project trees):

```bash
git clone https://github.com/fjuste/spine.git ~/Workspace/ide/spine
```

### 2. Link Spine to your project

From the consumer project root:

```bash
cd /path/to/my-project
bash ~/Workspace/ide/spine/scripts/link-spine.sh
```

This creates `.spine` → absolute path to the Spine repository. Use `--spine-dir=PATH` if the repo lives elsewhere, `--force` to replace a mismatched symlink, or `--dry-run` to preview.

### 3. Install Spine (terminal — full deterministic setup)

```bash
# Default: relative symlinks for IDE trees
bash .spine/install.sh          # all skills; interactive Graphify opt-in when TTY
bash .spine/install.sh --core   # minimal 5-skill profile only

# Hybrid (recommended for mixed-OS / versionable copies):
# .spine stays a gitignored symlink; rules/skills/commands are physical copies
bash .spine/install.sh --copy
bash .spine/install.sh --copy --update

bash .spine/install.sh --no-graphify-prompt   # skip Graphify question (CI/non-interactive)
```

> **Important:** Slash commands (`/spine-bootstrap`, `/spine-plan`, etc.) are **not** available until this step completes. After `link-spine.sh` (step 2) you only have the `.spine` symlink — the only valid next action is `bash .spine/install.sh` from the terminal.

`install.sh` performs all deterministic setup: wiring (symlinks **or** `--copy` physical files), `docs/` template seed, `opencode.json` merge, gitignore entries, and optional Graphify. Re-runs are idempotent — existing `docs/` content is never overwritten.

**Default (symlink wiring)** creates:

```text
PROJECT_ROOT/
├── .spine              → Spine repository (gitignored symlink)
├── .agents/skills/     per-skill symlinks (gitignored)
├── .agents/rules/      core rule symlinks (Antigravity)
├── .agents/workflows/  command symlinks → slash /spine-* (Antigravity)
├── .cursor/rules/      core rule symlinks (committable)
├── .cursor/commands/   command symlinks (committable)
├── .cursor/skills/     → .agents/skills/ (committable)
├── .opencode/commands/ command symlinks (committable)
├── .opencode/agents/   agent symlinks (committable)
├── .claude/skills/     → .agents/skills/ (committable)
├── opencode.json       created or merged (versioned)
└── docs/               memory bank templates (versioned)
```

**Hybrid (`--copy`)** creates the same layout with **physical file copies** under `.agents/`, `.cursor/`, `.claude/`, and `.opencode/` (versionable). Only `.spine` remains a local symlink (gitignored). Teammates get applied trees via `git pull`; maintainers refresh with `bash .spine/install.sh --copy --update`.

#### Platform wiring matrix

| Artefato Spine | Cursor | OpenCode | Claude Code | Antigravity |
|---|---|---|---|---|
| `skills/` | `.cursor/skills` | (hub) | `.claude/skills` | `.agents/skills/` |
| `rules/` | `.cursor/rules` | URLs in `opencode.json` | (via skills/CLAUDE.md) | `.agents/rules/` |
| `commands/` (slash) | `.cursor/commands` | `.opencode/commands` | — | `.agents/workflows/` |

Antigravity has no `commands/` directory: slash commands are **workflows** under `.agents/workflows/`.
### 4. Bootstrap (IDE, recommended)

Open (or reload) the project in your agent IDE, then run:

```
/spine-bootstrap
```

`/spine-bootstrap` performs a **deep assessment** of the codebase (and Graphify when present), then fills memory bank templates with **agent-optimized** detail: `global/*` (including project-specific alterations, known risks, and unplanned opportunities), and `progress.md` Current state. It does **not** fill `roadmap.md`, create active tasks, or produce delivery plans — use `/spine-plan` next.

Readiness check: `python3 .spine/scripts/spine_validate.py bootstrap` (wrapper: `bash .spine/scripts/validate-bootstrap-ready.sh`). Validators are cross-platform Python 3.9+; on Windows use `py -3` or `python` when `python3` is unavailable.

Requires step 3 complete.

**Prerequisites for slash commands:** (1) `.spine` via `link-spine.sh`, (2) `bash .spine/install.sh`. If slash commands are missing in the IDE, run step 3 from the terminal, then reload the project.

#### Manual `opencode.json` (alternative)

Each Spine project opts in via `opencode.json` with `instructions` pointing to Spine rule URLs:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode-go/deepseek-v4-pro",
  "small_model": "nvidia/deepseek-ai/deepseek-v4-pro",
  "default_agent": "ask",
  "instructions": [
    "https://raw.githubusercontent.com/fjuste/spine/refs/heads/master/rules/01-core-protocol.md",
    "https://raw.githubusercontent.com/fjuste/spine/refs/heads/master/rules/02-memory-bank.md",
    "https://raw.githubusercontent.com/fjuste/spine/refs/heads/master/rules/03-code-quality.md"
  ],
  "compaction": { "enabled": true, "strategy": "summarize", "threshold": 16000 },
  "agent": {
    "plan": { "mode": "primary", "model": "opencode-go/deepseek-v4-pro", "variant": "medium" },
    "build": { "mode": "primary", "model": "opencode-go/deepseek-v4-pro", "variant": "medium" },
    "ask": { "mode": "primary", "model": "opencode-go/deepseek-v4-pro", "prompt": "{file:.spine/agents/ask.md}" }
  }
}
```

Canonical full template: [`templates/opencode.json`](templates/opencode.json). Ask loads its prompt from `.spine/agents/ask.md` via `{file:...}` (requires `.spine` symlink). `bash .spine/install.sh` also symlinks the file to `.opencode/agents/` for OpenCode-native discovery.

> **Why URLs instead of local paths?**
> - **Portable:** works on any machine without a local Spine clone
> - **Auto-updating:** OpenCode fetches rules on each session; `git push` on Spine propagates changes
> - **Versionable:** pin to a tag (`refs/tags/v1.0.0`) for stability, or use `refs/heads/master` for latest
> - **Commitable:** `opencode.json` is plain JSON, safe to commit to the project repo

**Version pinning:** replace `refs/heads/master` with `refs/tags/v1.0.0` in each URL.

> **Important:** Never add Spine `instructions` to global `~/.config/opencode/opencode.json`. Rules and agents are opt-in per project only (`opencode.json` + `.opencode/agents/`).

### 5. Non-Spine projects

Projects that do not follow Spine simply omit Spine rule URLs from their `opencode.json`. They do not need `.spine` or `install.sh`.

### 6. Updating

From inside a consumer repository:

```bash
bash .spine/scripts/update.sh
```

This pulls the Spine repo via `.spine`, reconciles project symlinks (`install.sh --update --force`), syncs `opencode.json`, and preserves `docs/memory/`.

- **Rules:** Projects using URL-based `instructions` receive updates when OpenCode fetches rules each session.
- **Skills and commands:** `update.sh` reconciles symlinks after `git pull` on the Spine clone.

Optional update modes:

```bash
bash .spine/scripts/update.sh --dry-run
bash .spine/scripts/update.sh --replace-opencode
bash .spine/scripts/update.sh --with-graphify      # see "Optional: Graphify"
bash .spine/scripts/update.sh --graphify-init      # setup + first graph build
```

## Optional: Vendor install (commit Spine into the project)

**Default remains symlink mode** (`link-spine.sh` + `install.sh`). Use vendor mode when the team needs Spine as **real files** in the consumer repo (mixed OS without symlink privilege, or share via `git clone` with no per-machine Spine clone for day-to-day use).

Vendor mode copies Spine into `.spine/` (no nested `.git`) and materializes `.agents/`, `.cursor/`, `.opencode/`, and `.claude/` as real files. Those trees are intended to be **committed**.

### Install (maintainer)

```bash
cd /path/to/consumer-project
bash /path/to/spine/scripts/install-vendor.sh --spine-dir=/path/to/spine
# minimal skills: add --core
```

If the project already has symlink-mode Spine, conversion is refused unless you opt in:

```bash
bash /path/to/spine/scripts/install-vendor.sh --force --spine-dir=/path/to/spine
```

Then commit:

```bash
git add .spine .agents .cursor .opencode .claude .spine-vendor docs opencode.json .gitignore
git commit -m "chore: vendor Spine into project"
```

Teammates only need `git pull` — no symlink privilege and no local Spine clone for IDE use.

### Update (maintainer)

Overwrite vendored trees from an upstream Spine clone (required `--spine-dir`; never use the project's own `.spine` as source):

```bash
bash .spine/scripts/install-vendor.sh --update --spine-dir=/path/to/spine
git add .spine .agents .cursor .opencode .claude .spine-vendor
git commit -m "chore: update vendored Spine"
git push
```

`docs/memory/` content is never overwritten; `opencode.json` is merged non-destructively.

### Notes

- Marker file: `.spine-vendor` (signals vendor mode).
- Do **not** ignore `.spine`, `.agents/`, `.cursor/`, `.claude/`, or `.opencode/` in vendor mode (the script strips those ignores when present).
- Graphify / MkDocs: run existing `.spine/scripts/` helpers after vendor install if needed (not co-installed by `install-vendor.sh` in v1).
- Uninstall vendor trees (leaves `docs/` and `opencode.json`): `bash .spine/scripts/install-vendor.sh --uninstall`

### Windows (PowerShell)

`install.ps1` (Spine root) is the PowerShell port of `install-vendor.sh` for native Windows: no Bash, Python, symlink privilege, or Developer Mode required. It copies the Spine directory into `<project>\.spine` (nested `.git` excluded), materializes the IDE trees as real files, seeds `docs\`, merges `opencode.json`, and writes the same `.spine-vendor` marker — so a project installed by either script can be updated by the other.

```powershell
# Spine directory obtained via git clone or .zip download (unblock the script if downloaded)
Unblock-File C:\tools\spine\install.ps1

# Install — -ProjectRoot is required (prompted when omitted)
powershell -ExecutionPolicy Bypass -File C:\tools\spine\install.ps1 -ProjectRoot C:\dev\my-project
# options: -Core | -Skills grill-me,python-patterns | -Targets cursor,opencode | -DryRun | -Force

# Update — run the vendored copy, point -SpineDir at the upstream Spine directory
powershell -ExecutionPolicy Bypass -File C:\dev\my-project\.spine\install.ps1 -Update -ProjectRoot C:\dev\my-project -SpineDir C:\tools\spine

# Uninstall (leaves docs\ and opencode.json)
powershell -ExecutionPolicy Bypass -File C:\dev\my-project\.spine\install.ps1 -Uninstall -ProjectRoot C:\dev\my-project
```

Then commit the trees exactly as in **Install (maintainer)** above.

Limitations:

- Slash-command validators (`/spine-plan`, `/spine-bootstrap`) run `scripts/spine_validate.py`, so install [Python 3.9+](https://www.python.org/downloads/windows/) (or `winget install Python.Python.3.12`). No Bash required; agents use `py -3` or `python` when `python3` is unavailable.
- Graphify / MkDocs are not co-installed (same as `install-vendor.sh`).
- Requires Windows PowerShell 5.1+ or PowerShell 7+; uses `robocopy` for mirroring (falls back to `Copy-Item` when unavailable).

## Optional: Graphify

Graphify is an optional **code-structure** layer for consumer projects. **Spine** owns conceptual/documentary context (`docs/memory/`); **Graphify** accelerates where to look in source via `GRAPH_REPORT.md` and `graphify query`. The memory bank remains the operational source of truth.

When active, agents follow the **Graphify Discovery Protocol** in `rules/02-memory-bank.md`: read `graphify-out/GRAPH_REPORT.md` → run `graphify query` → targeted file reads.

### Install CLI (once per machine)

```bash
uv tool install graphifyy    # recommended; minimum graphifyy 0.7.16 for tri-platform co-install
# alternatives: pipx install graphifyy | pip install graphifyy
```

### Enable Graphify (primary: interactive prompt)

During `bash .spine/install.sh` (or `bash .spine/install.sh --update`) in a terminal, answer **yes** at the Graphify prompt. No extra flags are required.

This copies `.graphifyignore`, runs `graphify update .` (produces `graphify-out/graph.json` + `GRAPH_REPORT.md`), and co-installs Graphify for Cursor, OpenCode, and Claude Code (default `--targets=cursor,opencode,claude`).

**Non-interactive / CI only:**

```bash
bash .spine/install.sh --with-graphify          # same full co-install, no prompt
bash .spine/install.sh --no-graphify-prompt       # skip prompt (also skipped when not a TTY)
```

### Tri-platform co-install (what "yes" installs)

| IDE | Graphify artifact | Spine coexistence |
|-----|-------------------|-------------------|
| **Cursor** | `.cursor/rules/graphify.mdc` | Spine rule symlinks in same directory |
| **OpenCode** | `.opencode/plugins/graphify.js` + plugin in `opencode.json` | Spine 3 URL `instructions` preserved |
| **Claude Code** | `CLAUDE.md` section + PreToolUse hook | `.claude/skills/` Spine symlink preserved |

Optional git hooks: add `--graphify-hooks` to install (interactive yes does not enable hooks by default).

Remove platform artifacts only: `bash .spine/install.sh --graphify-uninstall`

### Existing project already using Spine

Re-run install and answer yes at the prompt (also offered on `--update` when integration is incomplete):

```bash
cd /path/to/existing-project
bash .spine/install.sh
# or: bash .spine/install.sh --update
```

**Non-interactive:** `bash .spine/install.sh --with-graphify` or `bash .spine/scripts/update.sh --graphify-init`

**Manual fallback** (if flags are unavailable on an old Spine clone):

```bash
bash .spine/scripts/install-graphify.sh --project-root=. --init-graph
```

### Verify activation

```bash
python3 .spine/scripts/spine_validate.py graphify
# wrapper: bash .spine/scripts/validate-graphify-integration.sh
```

Reports per-IDE status (graph, Cursor mdc, OpenCode plugin, Claude hook, CLI version).

Quick check:

```bash
test -f graphify-out/graph.json && echo "Graphify active"
test -f graphify-out/GRAPH_REPORT.md && echo "Report ready"
```

Agents follow the Graphify Discovery Protocol when `graphify-out/graph.json` exists (see `rules/01-core-protocol.md` and `rules/02-memory-bank.md` § Graphify Discovery Protocol).

### Refresh / regenerate `graphify-out`

After large refactors or when exploration feels stale:

```bash
graphify update .
```

### Git policy

- `graphify-out/` is machine-generated; most teams add `graphify-out/` to the project `.gitignore`.
- `.graphifyignore` is safe to commit (excludes Spine symlinks and Graphify cache artifacts).
- `graphify-out/graph.json` is the file agents check — it must exist locally even if gitignored.

### Troubleshooting

| Symptom | Fix |
|---|---|
| `graphify: command not found` | Install CLI: `uv tool install graphifyy` |
| No `graphify-out/graph.json` after setup | Run `graphify update .` manually from the project root |
| Graph build fails | Check `.graphifyignore`; ensure you are in the project root; rerun `graphify update .` |
| Agents still scan files broadly | Run `python3 .spine/scripts/spine_validate.py graphify`; restart agent session |
| OpenCode plugin missing | Re-run `bash .spine/install.sh` and answer yes; or `--with-graphify` (non-interactive); ensure graphifyy >= 0.7.16 |
| Root `AGENTS.md` from Graphify | Optional delete; Spine uses URL rules + Discovery Protocol, not root AGENTS.md |

## Optional: MkDocs

MkDocs is an optional **public-facing documentation** layer for consumer projects. **Spine** owns operational context (`docs/memory/`); **MkDocs** generates a static documentation site from `docs/mkdocs/`.

When active, agents follow the `documentation-driven-development` skill: update `docs/mkdocs/*.md` alongside code changes, and verify the build passes at harvest.

### Install CLI (once per machine)

```bash
pip install mkdocs
# or for Material theme:
pip install mkdocs-material
```

### Enable MkDocs (primary: interactive prompt)

During `bash .spine/install.sh` (or `bash .spine/install.sh --update`) in a terminal, answer **yes** at the MkDocs prompt. No extra flags are required.

This seeds `docs/mkdocs/mkdocs.yml`, `docs/mkdocs/index.md`, `docs/mkdocs/architecture.md`, and runs `mkdocs build --strict` to verify.

**Non-interactive / CI only:**

```bash
bash .spine/install.sh --with-mkdocs              # full setup, no prompt
bash .spine/install.sh --no-mkdocs-prompt          # skip prompt (also skipped when not a TTY)
```

### Existing project already using Spine

Re-run install and answer yes at the prompt (also offered on `--update` when integration is incomplete):

```bash
cd /path/to/existing-project
bash .spine/install.sh
# or: bash .spine/install.sh --update
```

**Non-interactive:** `bash .spine/install.sh --with-mkdocs` or `bash .spine/scripts/update.sh --with-mkdocs`

**Manual fallback:**

```bash
bash .spine/scripts/install-mkdocs.sh --project-root=. --init-mkdocs
```

### Verify activation

```bash
python3 .spine/scripts/spine_validate.py mkdocs
# wrapper: bash .spine/scripts/validate-mkdocs-integration.sh
```

Reports config, CLI, build status, and gitignore check.

Quick check:

```bash
test -f docs/mkdocs/mkdocs.yml && echo "MkDocs configured"
mkdocs build -f docs/mkdocs/mkdocs.yml --strict && echo "Build passes"
```

### Preview documentation

```bash
mkdocs serve -f docs/mkdocs/mkdocs.yml
# or:
cd docs/mkdocs && mkdocs serve
```

### Refresh build

After updating documentation files:

```bash
mkdocs build -f docs/mkdocs/mkdocs.yml
```

### Git policy

- `docs/mkdocs/site/` is machine-generated; add to project `.gitignore`.
- `docs/mkdocs/mkdocs.yml` and `docs/mkdocs/*.md` source files are safe to commit.
- `install.sh` automatically adds `docs/mkdocs/site/` to `.gitignore`.

### Remove MkDocs

Remove templates and config only: `bash .spine/install.sh --mkdocs-uninstall`

### Troubleshooting

| Symptom | Fix |
|---|---|
| `mkdocs: command not found` | Install CLI: `pip install mkdocs` |
| Build fails with broken links | Check `docs/mkdocs/*.md` for valid relative links |
| `site/` appears in git status | Add `docs/mkdocs/site/` to `.gitignore` and re-run install |
| Documentation not updating at harvest | Ensure `docs/mkdocs/mkdocs.yml` exists; run harvest step 4e manually |

## Migration from v1.2 and earlier

| Old setup | Action |
|-----------|--------|
| Ran `bash install.sh` (global mode, removed in v1.3) | Remove Spine symlinks under `~/.cursor/`, `~/.config/opencode/`, `~/.claude/` if no longer wanted |
| Ask agent in `~/.config/opencode/agents/` | Remove global symlink: `rm ~/.config/opencode/agents/ask.md`; use per-project `.opencode/agents/` via `bash .spine/install.sh` |
| Consumer without `.spine` | Run `scripts/link-spine.sh`, then `bash .spine/install.sh` |
| Core-only skill symlinks | `bash .spine/scripts/update.sh` adds remaining skills (default is now `all`) |

### Migrating opencode.json (6 rules → 3)

If your consumer project still loads 6 Spine rules or an `AGENTS.md` in the system prompt, migrate to the token-optimized layout:

**What changed:**
- 6 rules in `opencode.json` → **3 core rules** (~79% smaller system prompt)
- `compaction` added (`threshold: 16000`)
- Consumer projects no longer use `AGENTS.md` in the system prompt — context lives in `docs/memory/`

**Steps:**

1. Update the Spine clone: `git -C .spine pull origin master`
2. Update `opencode.json` — use [`templates/opencode.json`](templates/opencode.json) as the canonical source (3 `instructions` URLs + `compaction` block)
3. Or run `bash .spine/scripts/update.sh` (merge mode syncs `opencode.json` non-destructively); use `/spine-update` in the IDE only if slash commands are already installed (step 3)
4. Refresh Cursor rules: `bash .spine/install.sh --update --targets=cursor`
5. Remove consumer-root `AGENTS.md` if present (optional)
6. Restart the agent session

**3 core rules:**

| Rule | Responsibility |
|---|---|
| `01-core-protocol.md` | Execution cycle, definition of done, commits, guard rails |
| `02-memory-bank.md` | Structure and reading of `docs/memory/` |
| `03-code-quality.md` | Style, architecture, error handling, security |

Removed rules (`handoff-protocol`, `testing`, `gitflow`) remain available as on-demand skills or `docs/` workflow files.

## Cursor Setup

> **Cursor users:** Spine rules are installed per project in `.cursor/rules/` (supports `.md` and `.mdc`). No global Spine installer is provided.

## Compatibility (Claude Code and Other Tools)

SPINE works with Claude Code and other AI agents via per-project symlinks (`.claude/skills/`, `.cursor/`, `.opencode/`). For other tools, adapt paths or file names to match the expected format.

## Memory Bank v2.1

Operational source of truth: `docs/memory/` (Markdown in git). Tag policy: `docs/governance/memory-tags-policy.md`.

```text
docs/memory/
  global/              # Stable context (brief, glossary, patterns, decisions)
  ledger/
    roadmap.md        # GIST-informed: Goals + Idea Bank with ICE scoring (optional; filled by /spine-roadmap)
    progress.md        # Current state + append-only delivery log
    learnings.md       # Recurrence registry (LEARN-NNN)
  active_tasks/        # Open work (PLANNING | IN_PROGRESS | REVIEW)
  completed_tasks/     # DONE tasks (moved at harvest via git mv)
```

**Task files** use Obsidian-style YAML frontmatter (`tags`, `status`, `goal`, `branch`, `base`, …). Reference template: `templates/docs/memory/active_tasks/_task-template.md`. Optional `## Implementation Plan` holds bite-sized Task/Step detail for `/spine-execute`; harvest uses frontmatter and summary only.

Validate a task file manually: `python3 .spine/scripts/spine_validate.py task docs/memory/active_tasks/NNN-name.md` (wrapper: `bash .spine/scripts/validate-task.sh ...`). `/spine-plan` runs this automatically before the approval gate (structure only, not plan quality).

**Tiered SYNC** (see `rules/02-memory-bank.md`):

| Tier | When | Read |
|------|------|------|
| Core | Every session | global 1–6, progress Current state, open `active_tasks/` |
| Extended | Plan, harvest, ambiguous scope | `roadmap.md`, full delivery log |
| On demand | Debugging, recurrence | `learnings.md`, `completed_tasks/` |

**Harvest** (`/spine-harvest`): append delivery log entry (with **Tags**), update `learnings.md` when applicable, set frontmatter `status: DONE`, `git mv` task to `completed_tasks/`. When the task has `roadmap_idea`, update that Idea Bank row to `Done` (or keep `In Progress` if other open linked tasks remain); suggest `/spine-roadmap --review` for ICE re-score.

**Migration from v2.0:** Run `bash .spine/scripts/update.sh` (or `/spine-update` if slash commands exist), seed missing templates via `bash .spine/install.sh --update`, manually move DONE files from `active_tasks/` to `completed_tasks/`, optionally restructure `progress.md` (preserve legacy content under a heading).

## Slash Commands

Slash commands are symlinked into `.cursor/commands/` and `.opencode/commands/` by `bash .spine/install.sh` (setup step 3). They are unavailable until that step completes. Deterministic setup (symlinks, `docs/` seed, `opencode.json`) is handled by `install.sh` — not by a slash command.

Available command templates in `commands/`:
- `/spine-update` to refresh an already-installed consumer project safely.
- `/spine-bootstrap` for deep assessment and agent-optimized memory bank fill (not planning; not roadmap).
- `/spine-plan` to create the active task plan in memory-bank.
- `/spine-execute` to implement the selected active task with validation cycle.
- `/spine-harvest` to consolidate delivery learnings and close the task.
- `/spine-roadmap` to fill or update the roadmap with GIST-informed Goals and ICE-scored Idea Bank.
- `/spine-commit` to create a high-quality commit with branch safety checks.

`/spine-update` wraps `scripts/update.sh` and is the recommended maintenance path for existing consumer projects.

## OpenCode Agents

Spine ships agent definitions in `agents/`. `install.sh` deploys them **per project only** to `.opencode/agents/` (per-file symlinks to `.spine/agents/`). Do not symlink Spine agents into global `~/.config/opencode/agents/` — OpenCode loads project agents from `.opencode/agents/` when working in that repository.

Available agents:

- **ask** (`ask.md`) — Read-only thinking partner. Loads memory bank context (tiered SYNC) and optional Graphify graph-first exploration. Explore ideas, validate approaches, and discuss architecture without modifying the codebase. Read-only bash diagnostics are allowed; state-changing operations are blocked. Switch to the **Build** agent and run `/spine-plan` when ready to implement (paste native Plan draft into arguments if needed).

## Skill Governance

- `install.sh` links the **full skill catalog** by default; use `--core` for the minimal 5-skill profile.
- **Active allowlist** (5–8 skills in workflow) is governed by `docs/governance/skills-policy.md` — not by omitting symlinks unless you choose `--core` or `--remove-skill`.
- Add trial skills with `bash .spine/install.sh --add-skill=NAME`.

## Operational Workflow

Detailed sources:
- `docs/workflow/gitflow-operacional.md`
- `docs/workflow/ciclo-de-entrega.md`
- `docs/quality/guardrails.md`

High-level flow:

```mermaid
flowchart TD
    intake[IntakeTask] --> plan[QuickPlanAndTestPlan]
    plan --> feature[ImplementInFeatureBranch]
    feature --> validate[ValidatePositiveNegativeRegression]
    validate --> memory[UpdateMemoryBankAndDecisionLog]
    memory --> merge[MergeFeatureIntoDevelop]
    merge --> staging[PromoteDevelopToStaging]
    staging --> releaseCheck[RunReleaseChecklist]
    releaseCheck --> production[PromoteStagingToProduction]
    production --> mainSync[SyncProductionWithMain]
    mainSync --> harvest[RunHarvestToConsolidateDocs]
    harvest --> memory
    harvest --> intake
```

## Solo Developer Daily Routine

- Before starting:
  - read `docs/workflow/ciclo-de-entrega.md`;
  - confirm acceptance criteria;
  - define a compact test plan.
- During implementation:
  - avoid new abstractions without at least two real use cases;
  - record relevant technical decisions.
- Before closing the task (`/spine-harvest`):
  - append delivery log in `docs/memory/ledger/progress.md` (with **Tags**);
  - register recurrences in `docs/memory/ledger/learnings.md` when applicable;
  - record decisions in `docs/memory/global/decision-log.md`;
  - move task to `docs/memory/completed_tasks/`.

## Monthly Maintenance

1. Review active skill allowlists and remove low-value entries.
2. Update roadmap and progress ledgers.
3. Convert recurring lessons into explicit operating rules.

## Author

- Fernando Juste - juste@opsscale.ai

## Version

**v2.1.0** — Memory Bank v2.1.

- `completed_tasks/`, `ledger/learnings.md`, structured delivery log in `progress.md`
- Obsidian-style task frontmatter and `memory-tags-policy.md`
- Tiered SYNC; OpenCode `ask` agent in template; native Plan input via `/spine-plan`
- Optional vendor install: `scripts/install-vendor.sh` (copy Spine into the project, commit trees, overwrite update)

<details>
<summary>Version history</summary>

**v1.3.0** — Project-only installation.

- Removed global installation mode from `install.sh`
- Added `scripts/link-spine.sh` to create the `.spine` symlink in consumer projects
- `install.sh` is project-only; default skills = all; `--core` for minimal profile
- `--global` and `--project` flags removed

**v1.2.0** — ASK agent and OpenCode agents deployment.

- Added `agents/ask.md` — read-only Ask agent for OpenCode (explore ideas, memory bank context)

**v1.1.0** — Per-project installation via URL.

- Rules loaded via remote URLs in project-level `opencode.json` (opt-in)
- `install.sh` creates `opencode.json` with Spine rule URLs automatically

**v1.0.0** — First stable release.

- `install.sh` creates symlinks for Cursor, OpenCode, and Claude Code
- Rules in universal `.md` format (compatible with all agents)
- 34 curated skills, 6 slash commands, 3 framework rules

</details>

## References and Credits

This project was inspired by practical community work, especially:

- [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)
- [Cursor Memory Bank (gist)](https://gist.github.com/ipenywis/1bdb541c3a612dbac4a14e1e3f4341ab)

There are additional references that influenced SPINE over time and may be added as they are recovered and verified.

---

SPINE is intentionally pragmatic: low ceremony, high clarity, and consistent execution.