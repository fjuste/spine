---
# Recommended next step, written by /spine-harvest and /spine-plan; shown by spine.py brief and the digest.
next_step: Plan the highest-ICE candidate, I8 (git pre-commit memory validation, 320)
next_command: /spine-plan I8
next_alternatives:
  - Ask a fresh agent session "where are we?" to confirm it shows spine.py brief verbatim
  - Close legacy tasks 008–014 (add status or move to completed_tasks/)
  - /spine-plan I36 (narrative budget 3,000 → 12,000; G1, cheap)
---
# Progress

## Current state
- In flight: none. 025-pilot-brief delivered (2026-11-16): `spine.py brief` prints where the project is, recent deliveries with `why:`, what waits on the pilot and the next command; agents show it verbatim on request (roadmap I15 Done).
- Blocked: nothing.
- Next: see the recorded next step (`spine.py brief`). Open: close Spine's 7 legacy tasks without status (008–014; human decision); G1 idea I36 (narrative budget 3,000 → 12,000). Candidate tasks: `vendor` refuses the Spine repo as project; fence-aware `memory._section`; validator counts `related_learnings` as tags; harvest step 7 summary format does not fit open-task and ledger warnings; brief hint for legacy delivery logs.
- Legacy sections below (`O que funciona` … `Issues Conhecidos`) predate Memory Bank v2.1 and are kept for history.

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
