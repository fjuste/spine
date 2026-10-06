---
description: "[SPINE-INTERNAL] Commit, push develop, and cascade merge to staging, production, and main"
agent: build
---

# Slash Command: /spine-promote [$ARGUMENTS]
Act as a Spine Maintainer with full merge privileges.

**WARNING:** This command is **internal to the Spine repository only**. It must never be exposed to consumer projects via `spine.py install` or any template. It assumes direct push/merge rights to protected branches.

**Goal:** Create a high-quality commit on `develop`, push it, and cascade-promote the changes through `staging`, `production`, and `main`, finally returning to `develop`.

**Optional context (`$ARGUMENTS`):**
- If non-empty, treat it as the commit subject line (Conventional Commit prefix is still required).
- If empty, ask for the commit message interactively.

---

## 1. Pre-flight Validation
- Run:
  - `git rev-parse --show-toplevel`
  - Verify the repo basename is `spine` (or contains `spine/scripts/spine.py` and `commands/spine-commit.md`).
  - If validation fails, STOP with: "This command is restricted to the Spine maintainer repository."
- Run:
  - `git status --short --branch`
  - `git log --oneline -n 5`

## 2. Branch Gate
- Detect current branch: `git rev-parse --abbrev-ref HEAD`
- If **not** on `develop`, STOP with:
  - "You must be on the `develop` branch to run `/spine-promote`. Current branch: `<branch>`."
- Verify remote `origin` exists and `develop` is tracked.

## 3. Change Detection and Staging
- If working tree is clean (no staged or unstaged changes), STOP with:
  - "No local changes to commit."
- If there are unstaged changes:
  - List them.
  - Ask: "Stage all unstaged changes? (yes/no)"
  - If no, STOP and instruct the user to stage manually.
  - If yes, run `git add -A`.
- If there are already staged changes, proceed without re-staging unless the user requested to include new unstaged files.

## 4. Commit Message Quality (mandatory)
- **Auto-analysis prerequisite:** Before composing the message, run `git diff --staged --stat` and `git diff --staged` to understand exactly what is being committed. Use this analysis to auto-generate the commit content.
- **Auto-generate the commit body fields** based on the diff analysis:
  - `Why:` infer the intent from the nature of changes (new files = feature addition, deletions = cleanup/removal, modifications = fix/refactor/update)
  - `What changed:` list the key files and behavioral impact based on the actual diff; group related changes
  - `Validation:` suggest tests/checks that should have been run based on the affected areas
  - `Notes:` flag any risks, follow-ups, breaking changes, or migration notes visible in the diff
- **Subject line handling:**
  - If `$ARGUMENTS` is provided, use it as the **subject line**.
    - Validate that it follows Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
    - If missing the prefix, reject and ask for a valid prefix.
  - If `$ARGUMENTS` is empty, auto-suggest a subject line and commit type based on the diff analysis, then ask interactively:
    - "Suggested commit type: `<type>`. Confirm or change? (feat/fix/docs/refactor/test/chore)"
    - "Suggested subject line: `<subject>`. Confirm or edit:"
- **Confirmation gate:** Present the fully composed message (type + subject + auto-generated body) to the user for confirmation or editing. Do not commit until the user explicitly approves.
- Compose the final message:
  ```
  <type>: <subject>

  Why: <...>
  What changed: <...>
  Validation: <...>
  Notes: <...>
  ```

## 5. Commit Execution
- Create the commit: `git commit -m "<composed_message>"`
- Verify: `git show --name-only --oneline HEAD`

## 6. Push to develop
- Push: `git push origin develop`
- Verify with `git status --short --branch` and `git log --oneline -n 3`

## 7. Cascade Promotion (direct merge, no PRs)
Execute in strict order. After each merge, verify with `git log --oneline -n 3` and push immediately.

### 7.1 staging
- `git checkout staging`
- `git pull origin staging`
- `git merge develop --no-edit` (or `--ff-only` if policy enforces fast-forward)
- `git push origin staging`

### 7.2 production
- `git checkout production`
- `git pull origin production`
- `git merge staging --no-edit`
- `git push origin production`

### 7.3 main
- `git checkout main`
- `git pull origin main`
- `git merge production --no-edit`
- `git push origin main`

## 8. Return to develop
- `git checkout develop`
- Verify: `git status --short --branch`

## 9. Mandatory Final Report
Provide a concise summary including:
- Final branch (`develop`).
- Commit hash and full commit message.
- Files included.
- Promotion status per branch:
  - `develop` -> pushed
  - `staging` -> merged & pushed
  - `production` -> merged & pushed
  - `main` -> merged & pushed
- Any errors or warnings encountered.

## 10. Safety Guardrails
- **Never** run if not inside the Spine repository.
- **Never** run if not on `develop`.
- **Never** use `git push --force`.
- If any merge step produces conflicts, STOP immediately:
  - Do not resolve automatically.
  - Report the conflicted files and branch.
  - Instruct the user to resolve manually and re-run `/spine-promote` from `develop` after resolution.
- If any push is rejected (non-fast-forward), STOP and report which branch needs investigation.

(End of file)
