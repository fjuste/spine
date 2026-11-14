---
id: 2026-04-10-instalacao-per-project-via-url-opt-in
date: 2026-04-10
title: Instalação per-project via URL (opt-in)
summary: Instalação per-project via URL (opt-in)
tags: []
task:
superseded_by:
---

**Decision:** Instalação per-project via URL (opt-in)

**Why:** Spine como framework público exige que cada projeto opte explicitamente; URLs remotas eliminam symlinks locais, são portáteis e auto-atualizáveis

**Alternatives considered:** Symlink local (amarra ao filesystem), git submodule (complexo para iniciantes), path absoluto (não portátil)
