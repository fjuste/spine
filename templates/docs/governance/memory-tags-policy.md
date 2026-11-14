# Memory Tags Policy

Operational classification for correlating tasks, deliveries, and recurring incidents across the memory bank.

**Not the same as `domain-glossary.md`:** the glossary holds ubiquitous **domain language**; tags are **operational labels** for navigation and recurrence detection.

## Format

| Rule | Detail |
|------|--------|
| **Syntax** | Lowercase `kebab-case`; optional prefix `area/`, `type/`, `stack/` |
| **Cardinality** | 1–5 tags per artifact; reuse existing tags before inventing new ones |
| **Task files** | YAML frontmatter `tags:` list (Obsidian-compatible) |
| **Ledger entries** | YAML frontmatter `tags:` list in each `ledger/{decisions,learnings,deliveries}/` entry file; the generated `INDEX.md` shows them per row |

## When to tag

| Command | Action |
|---------|--------|
| `/spine-plan` | Required in task frontmatter |
| `/spine-harvest` | Copy tags to the delivery entry and to learning entries |
| `/spine-harvest` | Required on new `LEARN-NNN` entries |

## Recurrence matching

Before creating a new `LEARN-NNN`, search `ledger/learnings/INDEX.md` (and a legacy `ledger/learnings.md` if the project still has one) by **tags** and **symptoms**. If the same tag cluster matches, update **Recurrences** on the existing entry instead of duplicating.

## Starter set

Reuse these before inventing project-specific tags:

| Tag | Use when |
|-----|----------|
| `type/feature` | New capability |
| `type/bug` | Defect fix |
| `type/incident` | Production or critical incident |
| `type/refactor` | Structural change, no behavior change |
| `type/infra` | Infrastructure, CI, deployment |
| `type/docs` | Documentation-only delivery |
| `area/auth` | Authentication, authorization, sessions |
| `area/checkout` | Cart, payment, order flow |
| `area/api` | HTTP/RPC endpoints |
| `area/data` | Schema, migrations, queries |
| `area/infra` | Hosting, networking, observability |
| `area/ui` | Frontend, UX |
| `stack/python` | Python codebase |
| `stack/terraform` | IaC |
| `stack/ansible` | Configuration management |

Projects extend this list in-place as needed. Document new recurring tags here when they appear in three or more deliveries.

## Discovery

```bash
# Task frontmatter
rg -n "^tags:|^- area/|^- type/" docs/memory/active_tasks/

# Ledger entries (frontmatter tags; INDEX.md lists them per row)
rg -n "^  - (area|type|stack)/" docs/memory/ledger/
```

Obsidian users may query frontmatter fields with Dataview.
