# System Patterns

## Optional Complementary Tooling

- **Graphify** is an optional consumer-project retrieval layer for **code structure** (modules, flows, entry points).
- Graphify is **not a dependency** of Spine. `docs/memory/` remains the operational source of truth for scope, decisions, and delivery.
- **Spine** owns conceptual/documentary context; **Graphify** accelerates where to look in source (see `02-memory-bank.md` § Graphify Discovery Protocol).
- When active: read `graphify-out/GRAPH_REPORT.md`, then `graphify query "<question>" --graph graphify-out/graph.json`, then targeted file reads.
- Co-install (Cursor + OpenCode + Claude Code): answer yes at Graphify prompt during `python3 .spine/scripts/spine.py install` (non-interactive: `--with-graphify`)
- Verify: `python3 .spine/scripts/spine_validate.py graphify`
- Full guide: [Spine README — Optional: Graphify](https://github.com/fjuste/spine#optional-graphify).

- **MkDocs** is an optional public-facing documentation layer for consumer projects. When active (`docs/mkdocs/mkdocs.yml`), agents maintain `docs/mkdocs/*.md` alongside code changes, following the `documentation-driven-development` skill.
- MkDocs is **not a dependency** of Spine. `docs/memory/` remains the operational source of truth.
- Enable by answering yes at the MkDocs prompt during `python3 .spine/scripts/spine.py install` (non-interactive: `--with-mkdocs`).
- Verify: `python3 .spine/scripts/spine_validate.py mkdocs`
- Full guide: [Spine README — Optional: MkDocs](https://github.com/fjuste/spine#optional-mkdocs).

## Architecture
[Fill in]

## Design Patterns
[Fill in]

## Dependencies
[Fill in]

## Project-Specific Alterations

Deviations from platform/framework/vendor defaults. Agents must not revert these to "standard" behavior without explicit approval.

| Area | Platform/default expectation | What this project does | Code paths | Decision ref |
|------|------------------------------|------------------------|------------|--------------|
| [area] | [default] | [custom behavior] | `path/to/code` | decision-log § YYYY-MM-DD |
