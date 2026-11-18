---
description: Create a high-quality commit for current changes with safe branch checks
agent: build
---

# Slash Command: /spine-commit
Act as a Senior Software Engineer focused on clean history and safe Git flow decisions.

Goal: commit the latest local changes with a clear message that explains why and impact.

**Optional context (`$ARGUMENTS`):**
- If `$ARGUMENTS` is empty, run in `commit-only` mode.
- If `$ARGUMENTS` includes words like `push`, `commit and push`, or `commit+push`, run in `commit-and-push` mode.
- If `$ARGUMENTS` is ambiguous, ask for confirmation before pushing.

1. **Pre-flight Context:**
   - Run:
     - `git status --short --branch`
     - `git diff --staged`
     - `git diff`
     - `git log --oneline -n 10`
   - If there are no staged or unstaged changes, STOP and report:
     - "No local changes to commit."

2. **Branch Safety and Decision Gate:**
   - Detect current branch and whether `develop` exists:
     - `git rev-parse --abbrev-ref HEAD`
     - `git branch --list develop`
   - If current branch is `main`, `master`, `production`, or `staging`:
     - If `develop` exists:
       - Ask confirmation to create `feature/<descriptive-name>` from `develop` and move work there before commit.
     - If `develop` does not exist:
       - Ask confirmation and present options:
         - Option A: create `feature/<descriptive-name>` from current branch and commit there.
         - Option B: initialize `develop` from current branch, then create `feature/<descriptive-name>` from `develop`.
   - If current branch starts with `feature/`, `hotfix/`, or `release/`, continue.

3. **Commit Scope Discipline:**
   - Stage only files relevant to this delivery.
   - Do not include unrelated noise.
   - If there are unrelated changes, list them and ask whether to exclude.

4. **Commit Message Quality (mandatory):**
   - Use Conventional Commits:
     - `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
   - Subject line must be concise and meaningful.
   - Body must be explicit and useful for future audits:
     - `Why:` problem or intent
     - `What changed:` key files and behavior impact
     - `Validation:` tests/checks executed
     - `Notes:` risks, follow-ups, or migration notes (if any)
   - Prefer message quality over shortness.

5. **Commit Execution:**
   - Create the commit.
   - If the git `pre-commit` hook rejects it (`spine_validate.py staged` prints `ERROR:` lines and `Commit blocked: …`): fix each file it names in `docs/memory/` (stale `INDEX.md` → `python3 .spine/scripts/spine.py memory index`), `git add` the fixed files, and commit again. Never retry with `--no-verify`. `WARNING:` lines do not block; mention them in the final report.
   - Show:
     - `git show --name-only --oneline HEAD`
     - `git status --short --branch`

6. **Optional Push (when requested via `$ARGUMENTS`):**
   - If mode is `commit-and-push`:
     - Ensure upstream exists for current branch; if not, push with `-u`.
     - Push current branch to `origin`.
     - Show:
       - `git status --short --branch`
       - tracking branch (`branch -vv` or equivalent)
   - If mode is `commit-only`, skip push.

7. **Solo workflow (default for SPINE):**
   - **Do not** recommend opening a Pull Request as the default next step. Solo developers should not be nudged into self-approval PR loops.
   - After `git push`, GitHub (or similar) may print a `.../pull/new/...` URL. Treat it as **informational only** unless the user explicitly asks to open a PR or the project policy requires PR-based review.
   - **After push** (when on a `feature/*`, `hotfix/*`, or `release/*` branch), prefer this sequence instead of PR:
     1. Confirm push succeeded and branch is tracked on `origin`.
     2. Ask **interactive validation questions** before any merge, for example:
        - Were the tests or checks listed in the active task run? Anything else to run?
        - Ready to merge `<current-branch>` into `develop` locally?
     3. **Only after explicit human confirmation**, perform or describe the local merge (for example: `git checkout develop && git merge <branch>`). Do not merge without approval.
   - If the user or `docs/` explicitly defines a **team / PR-required** workflow, then suggesting a PR link is acceptable; otherwise default to the solo path above.

8. **Mandatory Final Report:**
   - Final branch used.
   - Commit hash + full commit message.
   - Files included in the commit.
   - Push result (performed or skipped).
   - **Next step (solo default):** summarize push outcome; offer **optional** merge into `develop` **only as questions** (validation first, then merge only if the user confirms). Do **not** list “open PR” as the recommended step unless the user asked for it or policy requires it.
