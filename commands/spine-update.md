---
description: Update an already-installed Spine consumer project while preserving memory docs
agent: build
---

# Slash Command: /spine-update
Act as the project's Update Operator.

Goal: update an existing Spine-enabled consumer project safely, preserving `docs/memory/`.

---

## 1. Preconditions

- Project must be a git repository.
- `.spine` symlink must exist in the project root.
- If `.spine` is missing, stop and ask the user to run `scripts/link-spine.sh`, then `bash .spine/install.sh`.
- If slash commands are missing, stop and ask the user to run `bash .spine/install.sh` from the terminal (step 3 in README), reload the IDE, then retry `/spine-update` or use `bash .spine/scripts/update.sh` directly.

---

## 2. Default update flow

Run from project root:

```bash
bash .spine/scripts/update.sh
```

This performs:
1. update Spine source via `.spine` (`git pull`);
2. reconcile project symlinks (`install.sh --update --force`);
3. sync `opencode.json` with current Spine template (merge mode);
4. preserve `docs/memory/` (non-destructive).

**Memory Bank v2.1 migration (manual, after update):** If DONE tasks remain in `active_tasks/`, run `git mv docs/memory/active_tasks/<file>.md docs/memory/completed_tasks/`. Seed missing `learnings.md` and `memory-tags-policy.md` via `bash .spine/install.sh --update` (idempotent). See Spine README § Memory Bank v2.1.

---

## 3. Optional modes

- Dry run:

```bash
bash .spine/scripts/update.sh --dry-run
```

- Skip `.spine` pull:

```bash
bash .spine/scripts/update.sh --no-pull
```

- Replace `opencode.json` (instead of merge):

```bash
bash .spine/scripts/update.sh --replace-opencode
```

- Include Graphify setup:

```bash
bash .spine/scripts/update.sh --with-graphify
```

- Include MkDocs setup:

```bash
bash .spine/scripts/update.sh --with-mkdocs
```

- Include Graphify setup + initial graph build:

```bash
bash .spine/scripts/update.sh --graphify-init
```

### Adopt Graphify on an existing project

When the consumer project already uses Spine but Graphify is not fully integrated:

1. Install Graphify CLI on the machine if needed: `uv tool install graphifyy` (recommended).
2. **Primary (interactive):** from project root, run install or update — answer **yes** at the Graphify prompt when integration is incomplete:

```bash
bash .spine/install.sh
# or: bash .spine/install.sh --update
```

3. **Non-interactive:** `bash .spine/scripts/update.sh --graphify-init` (pulls Spine, reconciles symlinks, full co-install).

This copies `.graphifyignore` if missing, runs `graphify update .`, co-installs Graphify for Cursor + OpenCode + Claude Code (default targets), merges OpenCode plugin into `opencode.json`, and preserves `docs/memory/`.

4. Verify tri-platform integration:

```bash
python3 .spine/scripts/spine_validate.py graphify
```

5. Refresh after large refactors: `graphify update .`

### Adopt MkDocs on an existing project

When the consumer project already uses Spine but MkDocs is not yet enabled:

1. Install MkDocs CLI on the machine if needed: `pip install mkdocs` (or `pip install mkdocs-material` for Material theme).
2. **Primary (interactive):** from project root, run install or update — answer **yes** at the MkDocs prompt:

```bash
bash .spine/install.sh
# or: bash .spine/install.sh --update
```

3. **Non-interactive:** `bash .spine/scripts/update.sh --with-mkdocs` (pulls Spine, reconciles symlinks, seeds templates).

This seeds `docs/mkdocs/mkdocs.yml`, `docs/mkdocs/index.md`, `docs/mkdocs/architecture.md`, runs `mkdocs build --strict`, and adds `docs/mkdocs/site/` to `.gitignore`. The memory bank (`docs/memory/`) is preserved untouched.

4. Verify:

```bash
python3 .spine/scripts/spine_validate.py mkdocs
```

Validators are cross-platform Python 3.9+ (on Windows, if `python3` is unavailable, use `py -3` or `python`); `bash .spine/scripts/validate-*.sh` remain thin wrappers.

5. Preview documentation: `mkdocs serve -f docs/mkdocs/mkdocs.yml`

Full guide: Spine repository README, section **Optional: MkDocs**.

---

## 4. Mandatory summary

Always report:

- Whether `.spine` pull was executed or skipped.
- Symlink reconciliation result.
- `opencode.json` mode used (merge or replace).
- Confirmation that `docs/memory/` was preserved.
- Graphify status when `--with-graphify` or `--graphify-init` was used: `.graphifyignore`, `graphify-out/graph.json`, per-IDE integration (Cursor mdc, OpenCode plugin, Claude hook), result of `spine_validate.py graphify`, and refresh command if graph build failed.
- MkDocs status when `--with-mkdocs` was used: `docs/mkdocs/mkdocs.yml`, `docs/mkdocs/index.md`, result of `spine_validate.py mkdocs`, and build command if build failed.
- Any blockers and exact command to recover.

---

## Acceptance criteria (command behavior)

- [ ] Fails fast with clear message if project is not Spine-enabled (`.spine` missing).
- [ ] Uses `scripts/update.sh` as the single update entrypoint.
- [ ] Preserves `docs/memory/` and does not wipe project memory.
- [ ] Supports dry-run and replacement modes for `opencode.json`.
- [ ] Produces a clear operational summary for the user.
