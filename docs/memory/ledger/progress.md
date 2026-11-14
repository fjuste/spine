# Progress

## Current state
- In flight: none. 021-per-entry-ledger delivered (2026-11-14): decisions, learnings and deliveries are one file per entry in `ledger/{decisions,learnings,deliveries}/` with a generated `INDEX.md` (`spine.py memory index`); new entries go there. `global/decision-log.md`, `ledger/learnings.md` and the delivery log below are legacy and frozen.
- Blocked: nothing.
- Next: plan the migrate task (`spine.py memory migrate`: split legacy files into entries, mechanical `summary:`, dry run by default, report unparsed text) — roadmap I25 stays In Progress until it ships. Then `/spine-roadmap --review` (I5/I6 vs I25; recalibrate the 3,000-char narrative budget). Candidate task: `vendor` refuses the Spine repo as project.
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

## Delivery log (newest first)
### 2026-11-14 — Memory budgets — digest-first limits in the validator and Current state compaction at harvest
**Task:** 020-memory-budgets | **Branch:** feature/memory-budgets
**Tags:** type/feature, area/memory, stack/python
**Description:** New `spine_validate.py memory` (`--project-root`, `--dry-run`) measures `docs/memory/` against named constants in `spine_cli/memory.py` (`check_budgets`, `BudgetCheck`): digest ≤ 8,000, Current state ≤ 1,500, narrative body ≤ 3,000, `decision-log.md` ≤ 5,000, `progress.md`/`learnings.md` ≤ 6,000. Over-budget scopes are `WARNING:` lines with a remedy hint (exit 0); the digest warning lists its sections largest first; a missing `docs/memory/` is the only error. The digest output is unchanged. `/spine-harvest` gains step 4a.1 (compact Current state, list other warnings as follow-ups, no `global/` edit without a human-approved diff); `02-memory-bank.md` § Memory budgets, README and AGENTS.md document it. Evidence: `pytest tests/` 248 passed (19 new in `test_memory_budgets.py`). Manual read-only runs by the agent on 2026-11-13 at `e4abadb`: onboarding-hub 10 warnings (digest 13,553, Current state 5,434), agenthub 9 (digest 10,522, Current state 6,563), intelligence-engine 10 (digest and Current state within budget), Spine 1 (`progress.md` 9,370); `git status docs/memory` unchanged in each; per-project table in the task's Execution evidence. Graphify and MkDocs not active.

### 2026-11-12 — Self-install keeps IDE trees ignored in the Spine repository
**Task:** 019-self-install-gitignore | **Branch:** feature/self-install-gitignore
**Tags:** type/bug, area/infra, stack/python
**Description:** `spine.py install`/`update` detect a self-install (project root is the Spine clone, `same_path(project, spine)`) and keep `.spine`, `.agents/`, `.cursor/`, `.claude/` and `.opencode/` ignored instead of removing the IDE-tree ignores consumer installs drop (`SELF_INSTALL_GITIGNORE_KEEP`, `adjust_install_gitignore(..., self_install=)`). `AGENTS.md` § 6 documents the self-install (`install --core --project-root=.`, working-tree caveat). Before the task, commit `1b85e7e` untracked the committed absolute `.spine` symlink. Evidence: `pytest -q tests/` 229 passed (7 new in `test_spine_cli.py`). Manual runs by the agent on 2026-11-12 at `ab0c327`: dry run with 0 ignore removals and 0 conflicts; real `install --core` exit 0, 0 conflicts, 0 warnings, `.gitignore` unchanged, no new untracked trees (raw output in the session scratchpad, temporary). Graphify and MkDocs not active.

### 2026-11-12 — Memory digest — summary-first Core SYNC for growing memory banks
**Task:** 018-memory-digest | **Branch:** feature/memory-digest
**Tags:** type/feature, area/memory, stack/python
**Description:** New stdlib-only `spine.py memory stats|digest` (`scripts/spine_cli/memory.py`). `digest` prints progress Current state, one line per open task (`NNN | STATUS | title — goal`), narrative `summary:` frontmatter or a capped outline, log entry counts with the newest 5 titles (heading and table-row formats), Extended-tier pointers, and a paced `SETUP:` block (largest-first, `--budget` default 60,000 chars) asking the agent to write missing summaries. `stats` prints per-file chars, the legacy Core total and the digest size. `rules/02-memory-bank.md` Core tier is digest-first with the legacy list as fallback, plus a new § Narrative summaries; `01-core-protocol.md`, `/spine-bootstrap`, the 5 narrative templates (`summary:` placeholder), README and AGENTS.md updated. Evidence: `pytest -q tests/` 222 passed (52 new in `test_memory_digest.py`). Manual read-only runs by the agent on 2026-11-11 at `b1ea53f`: onboarding-hub 421,762 → 13,039 chars (97%), intelligence-engine 209,066 → 5,076 (98%), agenthub 129,093 → 10,522 (92%); raw output was in the session scratchpad (temporary), reproducible with the same commands. Roadmap I3 → Done. Graphify and MkDocs not active.

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
