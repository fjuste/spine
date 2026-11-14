---
name: handoff-protocol
description: "Multi-agent handoff protocol — when working with multiple agents or planning/execution separation"
risk: low
source: spine
date_added: "2026-04-29"
---

# Handoff Protocol

## When to Use
- When separating Planner and Executor roles
- When handing off context between agents
- When working in multi-agent mode (not solo)

## Solo Mode (Default)
The active task file (`<seq>-<name>.md`) is the execution contract.
Same agent plans, executes, and harvests.
Mandatory updates at harvest: delivery entry in `ledger/deliveries/` + `progress.md` Current state, `ledger/learnings/` and `ledger/decisions/` entries (when applicable), `spine.py memory index`; task moved to `completed_tasks/`.

## Multi-Agent Mode (Optional)
- Separate Planner/Executor only when it provides real value
- Not mandatory to use `docs/discovery/` or `docs/contracts/` in every task
- Minimum: clear active task + tests + ledger update

## Handoff Flow
```
Scope → <seq>-<name>.md → Execution → Tests → Harvest
```

## Rules
1. Every execution needs `docs/memory/active_tasks/<seq>-<name>.md`
2. Structural changes to `global/` must be explicit and justified
3. Decision conflicts are escalated to the human
4. Set frontmatter `status: DONE` and `git mv` task to `completed_tasks/` when finished
5. Skill selection must respect `docs/governance/skills-policy.md`

## Reference
Core execution protocol: rule `01-core-protocol.md`
