---
id: 2026-04-21-adicionar-update-com-cleanup-de-dangling
date: 2026-04-21
title: Adicionar `--update` com cleanup de dangling
summary: Adicionar `--update` com cleanup de dangling
tags: []
task:
superseded_by:
---

**Decision:** Adicionar `--update` com cleanup de dangling

**Why:** `git pull` resolve conteúdo mas não cria/remove symlinks estruturais; `--update` faz install idempotente + limpa órfãos

**Alternatives considered:** Script separado `update.sh` (mais um arquivo para manter), exigir reinstall completo (perde estado)
