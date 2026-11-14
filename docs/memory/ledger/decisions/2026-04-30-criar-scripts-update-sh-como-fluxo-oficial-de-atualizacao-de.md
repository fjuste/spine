---
id: 2026-04-30-criar-scripts-update-sh-como-fluxo-oficial-de-atualizacao-de
date: 2026-04-30
title: Criar `scripts/update.sh` como fluxo oficial de atualização de projetos consumidores
summary: Criar `scripts/update.sh` como fluxo oficial de atualização de projetos consumidores
tags: []
task:
superseded_by:
---

**Decision:** Criar `scripts/update.sh` como fluxo oficial de atualização de projetos consumidores

**Why:** Separar instalação inicial de manutenção contínua reduz risco operacional; update reconcilia symlinks, sincroniza `opencode.json` e preserva `docs/memory/`

**Alternatives considered:** Reutilizar apenas `install.sh --update` (mistura responsabilidades), atualização manual ad-hoc (erro-prone)
