# Progress

## O que funciona
- Comando `/spine-bootstrap` documenta seed automático: resolve template via caminho real do arquivo do comando (symlink-aware), copia recursivamente `docs/` do repositório Spine para o projeto alvo quando ausente, depois assessment incremental.
- Estratégia de workflow definida para solo dev sem overengineering.
- Estrutura de governança documental criada (workflow, policy e qualidade).
- Direcionamento de curadoria de skills por allowlist mínima.
- Instalação per-project via URL: regras do Spine carregadas via `instructions` em `opencode.json` do projeto, sem vazar para projetos não-Spine.
- `/spine-bootstrap` atualizado para criar `opencode.json` com URLs remotas das regras.
- `install.sh --project` hardening: default `--skills=core` (não `all`), cleanup de dangling symlinks via `--update`, health check pós-install, flag `--uninstall`.
- Comando `/spine-promote` criado (maintainer-only): commit detalhado em `develop` com promoção em cascata para `staging`, `production` e `main`, retornando a `develop`. Restrito ao repo Spine, não exposto a consumer projects.
- `/spine-promote` melhorado com auto-geração da descrição do commit via análise de `git diff --staged`, sugerindo subject, type, Why, What changed, Validation e Notes automaticamente antes da confirmação do usuário.
- **Otimização de tokens (task 012):** Eliminado `templates/AGENTS.md` (duplicava rules + memory bank). System prompt de consumidor reduzido de ~25KB para ~5.3KB (-79%). Rules movidas para skills sob demanda: `gitflow`, `testing-guidelines`, `handoff-protocol`. Compaction threshold ajustado para 16000.
- **Otimização Cursor (task 013):** `install.sh` atualizado com `get_core_rules()` allowlist. Cursor agora carrega 3 rules (antes 6), consistente com OpenCode. `--update` limpa symlinks obsoletos. `copy_templates()` sem referência a AGENTS.md.
- **Adoção Graphify para consumidores (task 014):** comandos e rules agora orientam uso condicional de `graphify-out/graph.json` para exploração (graph-first), preservando `docs/memory/` como fonte obrigatória e sem tornar Graphify dependência do Spine.
- **Atualização de consumidores simplificada (task 014):** novo `scripts/update.sh` + comando `/spine-update` para atualizar projetos já instalados (pull de `.spine`, reconcile de symlinks, sync de `opencode.json`, preservação de `docs/memory/`).
- **Rules core consolidadas:** removidas rules não usadas (`03-handoff`, `05-testing`, `06-gitflow`) e renomeada `04-code-quality.md` para `03-code-quality.md`.
- **Rsync mode (task 017):** terceiro modo de instalação. `scripts/spine-init.sh` popula `.spine/` como diretório real via rsync de um clone canônico do Spine no host. `install.sh` aceita `.spine/` como diretório real (não só symlink). `update.sh` adaptado para pull canônico + rsync + reconcile. IDE trees mantêm symlinks relativos versionáveis.

## Em andamento
- Nenhuma task ativa no momento.

## O que falta
- Executar ciclo completo real (feature -> produção -> aprendizado).
- Refinar allowlist com base em uso real de 30 dias.
- Consolidar checklist de release no uso diário.
- Publicar versão com as otimizações de token para projetos consumidores existentes.
- Consolidar rollout de Graphify opcional em projetos consumidores e medir delta de tokens por task.
- Publicar release v1.4.0 com `/spine-roadmap` e demais features recentes.
- Documentar rsync mode no README (instruções de uso para consumidores).

## Issues Conhecidos
- Catálogo de skills muito grande para uso irrestrito.
- Risco de dispersão em frontend sem skill principal padronizada.

## Delivery log (newest first)
### 2026-07-28 — Rsync mode — canonical host Spine clone + relative IDE symlinks
**Task:** 017-rsync-mode | **Branch:** feature/rsync-mode
**Tags:** type/feature, area/infra, stack/bash
**Description:** Added rsync mode as third install option (alongside symlink and vendor). New `scripts/spine-init.sh` populates `.spine/` as real directory via rsync from a canonical host Spine clone, resolving path via 4-strategy cascade (flag → env var `SPINE_CANONICAL_PATH` → convention `~/Workspace/ide/spine` → auto-detect). `install.sh` relaxed: `require_spine_symlink()` → `require_spine_path()` (accepts real dir), `validate_health()` detects both modes, `uninstall_project()` handles real dirs with `rm -rf`, `print_project_summary()` shows mode-aware label. `update.sh` adapted: detects symlink vs rsync mode; in rsync mode, pulls canonical clone + rsyncs `.spine/` before reconciling symlinks. 7 contract tests added (`tests/unit/test_rsync_mode.py`). Full suite: 101/102 pass (1 pre-existing MkDocs failure, unrelated). Graphify and MkDocs not active.

### 2026-07-08 — Sync opencode template tests with current schema
**Task:** 016-opencode-template-test-sync | **Branch:** feature/opencode-template-test-sync
**Tags:** type/bug, area/testing, area/config
**Description:** Fixed 5 stale assertions in `test_opencode_template.py` to match the current `templates/opencode.json` schema. Removed 2 tests for `agent.build`/`agent.plan` (no longer in template — IDE-level config). Updated model assertion to `qwen3.7-max`, compaction check to `auto`/`prune`/`tail_turns`. Full suite: 89 passed, 0 failed. Graphify and MkDocs not active.

### 2026-07-08 — Add /spine-roadmap command with GIST-informed template
**Task:** 015-spine-roadmap-command | **Branch:** feature/spine-roadmap-command
**Tags:** type/feature, area/workflow, area/docs, area/governance
**Description:** Wired up the long-reserved `/spine-roadmap` slot. Created the command with fill, `--review`, and `--add-ideas` modes using grill-me strategic discovery. Replaced roadmap stub with GIST-informed template (Goals + Idea Bank with ICE scoring). Added `templates/docs/governance/ice-scoring-guide.md` with objective 1-10 scoring criteria. Updated bootstrap, rules, install/validate scripts, task template (`roadmap_idea` field), harvest (passive review suggestion), plan (idea-ID linking), README, and AGENTS.md. 13 files changed/created. 86/91 tests pass (5 pre-existing failures in `test_opencode_template.py` unrelated). Graphify and MkDocs inactive — not applicable.
