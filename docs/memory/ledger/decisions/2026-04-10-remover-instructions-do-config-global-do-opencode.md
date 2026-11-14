---
id: 2026-04-10-remover-instructions-do-config-global-do-opencode
date: 2026-04-10
title: Remover `instructions` do config global do OpenCode
summary: Remover `instructions` do config global do OpenCode
tags: []
task:
superseded_by:
---

**Decision:** Remover `instructions` do config global do OpenCode

**Why:** Config global é mergeado em todos os projetos, forçando regras do Spine em projetos não-Spine

**Alternatives considered:** Manter global com override por projeto (frágil, esquecimento)
