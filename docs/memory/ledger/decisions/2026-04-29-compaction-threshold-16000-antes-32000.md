---
id: 2026-04-29-compaction-threshold-16000-antes-32000
date: 2026-04-29
title: Compaction threshold 16000 (antes 32000)
summary: Compaction threshold 16000 (antes 32000)
tags: []
task:
superseded_by:
---

**Decision:** Compaction threshold 16000 (antes 32000)

**Why:** Threshold maior acumulava histórico desnecessário; 16k é suficiente para contexto de sessão

**Alternatives considered:** Manter 32k (acumulava lixo), reduzir para 8k (perdia contexto cedo demais)
