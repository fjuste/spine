---
task_id: 017
title: Rsync mode — canonical host Spine clone + relative IDE symlinks
goal: Suporte a um terceiro modo de instalação (rsync mode) como alternativa ao symlink mode, onde .spine/ é um diretório real populado via rsync de um clone canônico do Spine no host, enquanto .cursor/, .agents/, .claude/, .opencode/ mantêm symlinks relativos versionáveis.
status: DONE
tags:
  - type/feature
  - area/infra
  - stack/bash
branch: feature/rsync-mode
base: develop
execution_skill: executing-plans
roadmap_idea:
created_at: 2026-07-28
updated_at: 2026-07-28
completed_at: 2026-07-28
related_learnings: []

## Delivery summary

**Delivered:** `scripts/spine-init.sh` (new), `install.sh` (relaxed), `scripts/update.sh` (adapted), `tests/unit/test_rsync_mode.py` (7 tests).

**What changed:**
- New rsync install mode: `.spine/` as real directory via rsync from canonical host Spine clone
- Canonical path resolution: `--spine-dir` → `SPINE_CANONICAL_PATH` env var → `~/Workspace/ide/spine` → auto-detect
- `install.sh` now accepts `.spine/` as real directory in addition to symlink
- `update.sh` handles both symlink and rsync mode (pull canonical + rsync + reconcile)
- All IDE trees (`.cursor/`, `.agents/`, `.opencode/`, `.claude/`) keep relative symlinks unchanged

**Tests:** 101/102 pass. 7 new tests, 0 regressions. 1 pre-existing fail (`test_validate_mkdocs_integration_script_exists` — expects `pip install mkdocs` but script uses `uv`, unrelated).

**Graphify:** not active. **MkDocs:** not active.

**Learnings:** none — straightforward feature addition, no incidents or rework.

---
# 017-rsync-mode

## Discovery notes

Escopo definido diretamente na análise pré-plano. Sem ambiguidades. Não requer `@grill-me`.

**Contexto:** O modo symlink atual funciona bem em Linux/macOS, mas `.spine` como symlink absoluto para fora do repo quebra em Docker, CI e NFS. O modo vendor (cópia completa de tudo) resolve isso mas é pesado. O rsync mode é um meio-termo: só `.spine/` é materializado como diretório real; as IDE trees continuam com symlinks relativos (que já são versionáveis e funcionam perfeitamente no git).

**Decisão de design:** Sem JSON de registro. Resolução do caminho canônico por:
1. Flag `--spine-dir=PATH`
2. Env var `SPINE_CANONICAL_PATH`
3. Convenção `~/Workspace/ide/spine`
4. Auto-detecção (`SCRIPT_DIR/..` quando executado de dentro do clone canônico com `.git/`)

**Não escopo:**
- Alterar o modo vendor existente
- Alterar o modo symlink como default
- Adicionar JSON de registro de instalações
- Criar comando `/spine-init` (slash command) — só script bash por enquanto

## Objective

Adicionar um terceiro modo de instalação (`rsync mode`) ao Spine que elimina o único symlink frágil da arquitetura atual — `.spine` — substituindo-o por um diretório real populado via `rsync` de um clone canônico do Spine no host. As IDE trees (`.cursor/`, `.agents/`, `.claude/`, `.opencode/`) mantêm a estrutura atual de symlinks relativos apontando para `../../.spine/...`, que são comprovadamente versionáveis e portáteis entre máquinas.

Fluxo do novo modo:
1. Dev clona o Spine uma vez no host (`~/Workspace/ide/spine`)
2. No projeto consumer: `bash ~/Workspace/ide/spine/scripts/spine-init.sh`
3. O script rsync `.spine/` do canônico → `install.sh` cria symlinks relativos nas IDE trees
4. Para atualizar: `bash .spine/scripts/update.sh` (pull no canônico + rsync + reconcile)

## Inputs

- `scripts/link-spine.sh` — referência para estrutura do script de init
- `install.sh` — funções `require_spine_symlink()`, `validate_health()`, `uninstall_project()`, `print_project_summary()`
- `scripts/update.sh` — lógica de atualização (atualmente assume symlink)
- `scripts/install-vendor.sh` — referência para rsync patterns e flags
- `tests/unit/test_install_seed.py` — padrão de testes de contrato
- `tests/unit/test_install_vendor.py` — padrão de testes para script de instalação

## Expected Outputs

- `scripts/spine-init.sh` — novo script (criar)
- `install.sh` — funções relaxadas para aceitar `.spine/` como diretório real (modificar)
- `scripts/update.sh` — adaptado para modo rsync (modificar)
- `tests/unit/test_rsync_mode.py` — testes de contrato (criar)

## Acceptance Criteria (verifiable, TDD-ready)

- [ ] `scripts/spine-init.sh` existe e documenta rsync mode
  - Test: `test_spine_init_script_exists` — verifica arquivo existe, contém "rsync", "SPINE_CANONICAL_PATH", e "--spine-dir="
- [ ] `spine-init.sh` resolve o caminho canônico por 4 estratégias em cascata
  - Test: `test_spine_init_resolves_canonical_path` — verifica presença das funções `resolve_canonical_spine`, `is_spine_root`, referências a `$SPINE_CANONICAL_PATH`, `$HOME/Workspace/ide/spine`
- [ ] `spine-init.sh` chama `install.sh` após o rsync
  - Test: `test_spine_init_calls_install_sh` — verifica que o script referencia `install.sh` como passo seguinte
- [ ] `install.sh` aceita `.spine/` como diretório real (não apenas symlink)
  - Test: `test_install_sh_accepts_real_spine_directory` — verifica que `require_spine_symlink` contém branch para diretório real (`elif [[ -d "$spine_path" ]]`)
- [ ] `install.sh` faz health check correto em ambos os modos
  - Test: `test_install_sh_health_check_supports_rsync_mode` — verifica que `validate_health` contém "rsync mode" ou branch para diretório real
- [ ] `update.sh` aceita `.spine/` como diretório real
  - Test: `test_update_sh_supports_rsync_mode` — verifica que `update.sh` NÃO faz exit na falta de symlink (aceita `-d` também), e referencia `SPINE_CANONICAL_PATH` ou `rsync`
- [ ] `install.sh` faz uninstall correto de `.spine/` em modo rsync
  - Test: `test_install_sh_uninstall_handles_real_spine_dir` — verifica que `uninstall_project` ou `remove_symlink_or_dir` trata diretório real não-vazio para `.spine`
- [ ] Testes existentes continuam passando (sem regressão)
  - Test: `pytest tests/` — full suite passa (atualmente 89 passando)

## Test Strategy

- **Positive:** Contrato dos novos scripts e funções adaptadas — verificações de string contra conteúdo dos arquivos
- **Negative:** N/A (testes de contrato não executam os scripts)
- **Regression:** Full suite `pytest tests/` antes e depois das mudanças
- **Command:** `pytest tests/unit/test_rsync_mode.py tests/ -v`

## Implementation Plan

### Task 1: Criar `scripts/spine-init.sh`

**Files:**
- Create: `scripts/spine-init.sh`
- Test: `tests/unit/test_rsync_mode.py` (a criar no Task 4)

**Step 1:** Criar o script com estrutura defensiva (`set -uo pipefail`), parsing de flags (`--spine-dir`, `--force`, `--dry-run`, `--project-root`), e função `is_spine_root()` (reutilizar pattern do `install-vendor.sh`).

**Step 2:** Implementar `resolve_canonical_spine()` com as 4 estratégias em cascata: flag explícita → env var `SPINE_CANONICAL_PATH` → convenção `~/Workspace/ide/spine` → auto-detecção via `SCRIPT_DIR/..` (só se tiver `.git/`).

**Step 3:** Implementar a lógica principal: encontrar project root, validar caminho canônico, verificar conflitos (symlink existente → `--force`), executar `rsync -a --delete --exclude='.git/' $CANONICAL/ $PROJECT/.spine/`, remover `.git` residual, chamar `bash .spine/install.sh`.

**Step 4:** Commit com `feat: add spine-init.sh for rsync mode`.

### Task 2: Relaxar `install.sh` para aceitar `.spine/` como diretório real

**Files:**
- Modify: `install.sh:383-403` (`require_spine_symlink` → renomear para `require_spine_path`)
- Modify: `install.sh:912-921` (`validate_health` — branch `.spine` check)
- Modify: `install.sh:1477` (`uninstall_project` — `.spine` como diretório real)
- Modify: `install.sh:1536` (`print_project_summary` — label condicional)
- Modify: `install.sh:1568,1575,1582,1588,1595` (chamadas a `require_spine_symlink` → `require_spine_path`)

**Step 1:** Renomear `require_spine_symlink()` para `require_spine_path()`. Substituir o check `[[ ! -L "$spine_link" ]] || [[ ! -d "$spine_link" ]]` por lógica que aceita symlink com target válido OU diretório real com `rules/`, `skills/`, `commands/`. Atualizar mensagens de erro.

**Step 2:** Atualizar `validate_health()` — adicionar branch `elif [[ -d "$project_root/.spine" ]]` após o check `-L`. Para diretório real, verificar `rules/` e `skills/` diretamente (sem `readlink`). Label: "rsync mode" em vez de "symlink".

**Step 3:** Atualizar `uninstall_project()` — antes de chamar `remove_symlink_or_dir` para `.spine`, adicionar branch: se é diretório real não-vazio (não symlink), usar `rm -rf` com aviso. O `remove_symlink_or_dir` existente só remove diretórios vazios.

**Step 4:** Atualizar `print_project_summary()` — detectar `[[ -L .spine ]]` vs `[[ -d .spine ]]` e mostrar label apropriado (`-> (Spine repository)` vs `(rsync mode)`).

**Step 5:** Atualizar todas as chamadas a `require_spine_symlink` (linhas 1568, 1575, 1582, 1588, 1595) para o novo nome `require_spine_path`.

**Step 6:** Commit com `refactor: relax install.sh to accept .spine as real directory`.

### Task 3: Adaptar `scripts/update.sh` para modo rsync

**Files:**
- Modify: `scripts/update.sh:54` (check de symlink)
- Modify: `scripts/update.sh:61` (SPINE_DIR resolve)
- Modify: `scripts/update.sh:82-91` (git pull step)

**Step 1:** Substituir `if [[ ! -L "$SPINE_LINK" ]]` por check que aceita symlink OU diretório real. Se for diretório real, buscar caminho canônico de `.spine/.spine-canonical-source` ou `$SPINE_CANONICAL_PATH`.

**Step 2:** No step de pull: se modo symlink → `git -C "$SPINE_DIR" pull` como antes. Se modo rsync → `git -C "$CANONICAL_PATH" pull` seguido de `rsync -a --delete "$CANONICAL_PATH/" "$PROJECT_ROOT/.spine/"`.

**Step 3:** Commit com `feat: adapt update.sh for rsync mode`.

### Task 4: Criar testes de contrato

**Files:**
- Create: `tests/unit/test_rsync_mode.py`

**Step 1:** Criar o arquivo de teste seguindo o padrão dos testes existentes (`pathlib.Path`, funções `_read(path)`).

**Step 2:** Implementar os 7 testes listados nos Acceptance Criteria.

**Step 3:** Executar `pytest tests/ -v` e garantir que todos os 89 testes existentes + 7 novos passam.

**Step 4:** Commit com `test: add contract tests for rsync mode`.
