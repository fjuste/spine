---
id: 2026-04-29-eliminar-templates-agents-md-e-consolidar-em-3-rules
date: 2026-04-29
title: Eliminar `templates/AGENTS.md` e consolidar em 3 rules
summary: Eliminar `templates/AGENTS.md` e consolidar em 3 rules
tags: []
task:
superseded_by:
---

**Decision:** Eliminar `templates/AGENTS.md` e consolidar em 3 rules

**Why:** AGENTS.md duplicava conteúdo de rules (01-core-protocol, 02-memory-bank, code-quality) e docs/memory/. System prompt de ~25KB caiu para ~5.3KB (-79%)

**Alternatives considered:** Manter AGENTS.md como "atalho" (mantinha duplicação), mover rules para AGENTS.md (inverte dependência)
