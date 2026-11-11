---
name: documentation-driven-development
description: "Update public-facing MkDocs documentation alongside code changes. Use when a task introduces public APIs, architectural patterns, or user-facing features in a project with MkDocs enabled."
risk: unknown
source: community
date_added: "2026-07-08"
---

# Documentation-Driven Development

## Overview

Documentation is part of the Definition of Done. When MkDocs is active (`docs/mkdocs/mkdocs.yml` exists), update `docs/mkdocs/*.md` during development, not at the end. This skill formalizes the practice.

**Core principle:** Write or update documentation BEFORE implementing — same discipline as TDD. If you can't explain the change to a new developer in `docs/mkdocs/`, you don't understand it well enough.

**Announce at start:** "I'm using the documentation-driven-development skill to keep docs in sync with code."

## Step 1: Assess documentation impact

Before writing implementation code, review the task:

1. Does this task introduce new public APIs or endpoints?
2. Does it establish or change an architectural pattern?
3. Does it add user-facing behavior?
4. Does it change project setup, configuration, or dependencies?

If **none** of the above apply (e.g., pure refactoring, internal optimization, bug fix with no behavioral change), skip documentation updates — the harvest prompt (step 4e) will confirm this decision.

## Step 2: Identify affected files

Map the task scope to `docs/mkdocs/` files:

| Task scope | File to update |
|------------|---------------|
| New API endpoints / schemas | `api/` directory or `index.md` |
| Architectural decisions | `architecture.md` |
| Project setup / onboarding | `index.md` |
| New patterns or conventions | `architecture.md` |
| Configuration changes | `index.md` |

Create new `.md` files under `docs/mkdocs/` when a new section is needed. Update `mkdocs.yml` `nav` if new pages are added.

## Step 3: Write documentation first

For each affected file:

1. Write the documentation describing the end state (what will exist after implementation)
2. Use clear, concrete examples
3. Link to code paths using backticks: `` `src/services/auth.py:42` ``
4. Keep it concise — public documentation, not memory bank verbosity

**Do NOT copy memory bank content verbatim into MkDocs.** The memory bank is operational metadata for agents. MkDocs is for humans reading the project.

## Step 4: Implement and verify

1. Implement the code change
2. Verify docs build (prefer uv; bare `mkdocs` is often not on PATH):
   `uv run --extra docs mkdocs build -f docs/mkdocs/mkdocs.yml --strict`
3. Include `docs/mkdocs/*.md` changes in the commit with `docs:` prefix
4. Preview if needed: `uv run --extra docs mkdocs serve -f docs/mkdocs/mkdocs.yml`

## Step 5: Harvest checklist

At `/spine-harvest`:

- [ ] `uv run --extra docs mkdocs build -f docs/mkdocs/mkdocs.yml --strict` passes (step 3.6)
- [ ] Documentation reflects the delivered state (step 4e)
- [ ] New architectural decisions are captured in `architecture.md`
- [ ] `docs:` commit includes MkDocs file changes

## When to Use

When `docs/mkdocs/mkdocs.yml` exists in the project root AND the task:
- Has `tags: type/documentation` in frontmatter
- Introduces new public APIs, endpoints, or schemas
- Establishes architectural patterns
- Adds user-facing features
- Is flagged by harvest step 4e as needing documentation

## When to skip

- Pure refactoring (no behavioral change)
- Internal bug fixes
- CI/CD, build tooling, or dev-only changes
- Memory bank updates only (those are separate)

## Preview / build commands

```bash
# Install docs extra once (with other extras as needed)
uv sync --extra docs --extra dev

# From project root (preferred — do not assume mkdocs on PATH)
uv run --extra docs mkdocs build -f docs/mkdocs/mkdocs.yml --strict
uv run --extra docs mkdocs serve -f docs/mkdocs/mkdocs.yml
```
