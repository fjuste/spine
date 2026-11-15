---
name: grill-me
description: "Interview relentlessly about a plan or design until shared understanding; sharpen domain language and promote terms to the memory bank. Use during /spine-plan when scope is ambiguous, multi-domain, or explicitly requested."
risk: low
source: community
author: mattpocock
date_added: "2026-06-03"
---

# Grill Me

## When to Use

- Scope is ambiguous, broad, or spans multiple domains
- Major architectural, security, auth, schema, or infrastructure decisions are unresolved
- User explicitly opts in (`grill me`, `grill:`, `grill with docs`, `grill:docs`, `stress-test`, `challenge this`)
- User asks mid-session to be grilled before the plan is written

## When to Skip

- Scope is clear, specific, and single-domain
- User explicitly opts out (`skip discovery`, `no grill`, `direct plan`)

## Protocol

Interview the user relentlessly about every aspect of the plan until shared understanding is reached. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

**Announce at start:** "I'm using the grill-me skill for discovery."

For each question:

- Ask **one question at a time**
- Provide your **recommended answer**
- If the answer can be found by exploring the codebase, explore the codebase instead of asking

## Domain awareness

During codebase exploration, also read existing memory bank documentation:

- `docs/memory/global/domain-glossary.md` (create lazily on first resolved term — see [DOMAIN-GLOSSARY-FORMAT.md](./DOMAIN-GLOSSARY-FORMAT.md))
- `docs/memory/global/product-context.md`
- `docs/memory/global/system-patterns.md`
- `docs/memory/ledger/decisions/INDEX.md` (open only the decision entries that matter; skip rows marked superseded)

When `grill with docs` or `grill:docs` was requested, expect inline updates to the glossary and new decision entries as decisions crystallise.

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `domain-glossary.md`, call it out immediately. Example: "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. Example: "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update domain-glossary.md inline

When a term is resolved, update `docs/memory/global/domain-glossary.md` right there. Do not batch these up — capture them as they happen. Use the format in [DOMAIN-GLOSSARY-FORMAT.md](./DOMAIN-GLOSSARY-FORMAT.md).

The glossary must be totally devoid of implementation details. Do not treat it as a spec, scratch pad, or repository for implementation decisions. It is a glossary and nothing else.

### Offer decision entries sparingly

Only offer to add a decision entry to `docs/memory/ledger/decisions/` (one file, see `02-memory-bank.md` § Ledger entries) when **all three** are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the decision entry. Reversible or obvious decisions stay in `## Discovery notes` only.

## Knowledge promotion

| Scope | What goes here | When |
|---|---|---|
| Task | MVP, out-of-scope, domain, trade-offs | Always → `## Discovery notes` in the active task file |
| Project | Canonical domain terms | When resolved during discovery → `domain-glossary.md` |
| Project | Architectural decisions | When all three decision criteria are met → `ledger/decisions/` entry |

Record links in `## Discovery notes` when the glossary or decision entries were updated (e.g. "Promoted: **PartialRefund** to domain-glossary.md").

## Exit Criteria

Discovery is complete when all of the following are resolved:

- Minimum viable deliverable (what makes this task done)
- Explicit out-of-scope boundaries
- Primary domain (e.g., backend API, frontend UI, infrastructure, database)
- Major trade-offs and architectural branches with no open blockers

**Principle:** one plan should be completable in a single execution session. If scope feels too large, suggest splitting into multiple plans upfront.

## Output

Record resolved decisions in the active task file under `## Discovery notes` before proceeding to `@writing-plans`.

Suggest operational `tags` for `/spine-plan` frontmatter based on domain, stack, and incident type (per `docs/governance/memory-tags-policy.md`). Tags belong in YAML frontmatter at plan time — not as inline metadata in the task body.

Do **not** write the full implementation plan until discovery is complete.
