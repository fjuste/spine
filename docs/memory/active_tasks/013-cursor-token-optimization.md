# 013-cursor-token-optimization

> **Suggested execution skill:** @executing-plans

## Branch: feature/cursor-token-optimization
## Base: develop

## Status: IN_PROGRESS

## Objetivo

Aplicar ao Cursor a mesma otimização de tokens feita para o OpenCode: filtrar quais rules são carregadas (apenas 3 core), limpar symlinks obsoletos durante updates, e corrigir `copy_templates()` que tenta copiar `AGENTS.md` já eliminado.

## Inputs

- `install.sh` — script de instalação (1409 linhas)
- `templates/opencode.json` — template atualizado (3 rules)
- Resultado da task 012 (eliminação de AGENTS.md)

## Outputs Esperados

- `install.sh` atualizado com:
  - Allowlist de rules core para Cursor
  - Limpeza de symlinks obsoletos em `--update`
  - `copy_templates()` sem referência a AGENTS.md

## Mapa de Problemas

| Problema | Localização | Impacto |
|---|---|---|
| Cursor carrega 6 rules (deveria ser 3) | `install_project_cursor()` linha 706 | Tokens desperdiçados |
| `--update` não remove symlinks obsoletos | `cleanup_dangling_symlinks()` | Symlinks de rules antigas permanecem |
| `copy_templates()` referencia AGENTS.md | linha 1100 | Tenta copiar arquivo inexistente |
| `print_project_summary()` menciona AGENTS.md | linha 1278 | Informação desatualizada |
| `uninstall_project()` menciona AGENTS.md | linha 1225 | Informação desatualizada |

## Criterio de Aceite

- [ ] Cursor recebe apenas 3 rules core (01-core-protocol, 02-memory-bank, 04-code-quality)
- [ ] `--update` remove symlinks de rules que não são mais core
- [ ] `copy_templates()` não referencia AGENTS.md
- [ ] `print_project_summary()` não menciona AGENTS.md
- [ ] `uninstall_project()` não menciona AGENTS.md
- [ ] `--targets=cursor` funciona isoladamente
- [ ] `--targets=opencode` continua funcionando
- [ ] `--targets=cursor,opencode,claude` funciona (default)
- [ ] Script passa em `bash -n install.sh` (syntax check)

## Tasks

### Task 1: Adicionar allowlist de rules core no install.sh

**Files:**
- Modify: `install.sh`

**Step 1:** Adicionar função `get_core_rules()` após `get_command_files()` (linha ~169):

```bash
get_core_rules() {
    echo "01-core-protocol.md
02-memory-bank.md
04-code-quality.md"
}
```

**Step 2:** Commit

```bash
git add install.sh
git commit -m "feat: add get_core_rules() allowlist to install.sh"
```

---

### Task 2: Filtrar rules no Cursor (install + update)

**Files:**
- Modify: `install.sh`

**Step 1:** Na função `install_project_cursor()` (linha 706), substituir `get_rule_files` por `get_core_rules`:

```bash
# Antes:
for rule_file in $(get_rule_files); do

# Depois:
for rule_file in $(get_core_rules); do
```

**Step 2:** Na função `cleanup_dangling_symlinks()`, adicionar limpeza de rules obsoletas em `.cursor/rules/`. Após a limpeza de dangling (linha ~983), adicionar:

```bash
# Remove rule symlinks that are not in the core allowlist
sub="$(cleanup_obsolete_rules "$project_root/.cursor/rules")"
total=$((total + sub))
```

**Step 3:** Adicionar função `cleanup_obsolete_rules()`:

```bash
cleanup_obsolete_rules() {
    local dir_path="$1"
    local count=0

    if [[ ! -d "$dir_path" ]]; then
        return 0
    fi

    local core_rules
    core_rules="$(get_core_rules)"

    local link rule_name
    for link in "$dir_path"/*; do
        [[ -L "$link" ]] || continue
        rule_name="$(basename "$link")"
        if ! echo "$core_rules" | grep -qxF "$rule_name"; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove obsolete rule: $rule_name"
            else
                rm "$link"
                log_linked "removed obsolete rule: $rule_name"
            fi
            count=$((count + 1))
        fi
    done

    echo "$count"
}
```

**Step 4:** Commit

```bash
git add install.sh
git commit -m "refactor: filter Cursor rules to core allowlist, cleanup obsolete on update"
```

---

### Task 3: Corrigir copy_templates()

**Files:**
- Modify: `install.sh`

**Step 1:** Na função `copy_templates()` (linha 1100), remover `"AGENTS.md"` do array:

```bash
# Antes:
local template_files=("opencode.json" "AGENTS.md")

# Depois:
local template_files=("opencode.json")
```

**Step 2:** Commit

```bash
git add install.sh
git commit -m "fix: remove AGENTS.md from copy_templates — file eliminated"
```

---

### Task 4: Limpar referências a AGENTS.md em mensagens

**Files:**
- Modify: `install.sh`

**Step 1:** Na função `uninstall_project()` (linha 1225), atualizar mensagem:

```bash
# Antes:
echo "  Note: opencode.json and AGENTS.md were NOT removed."
echo "  Remove them manually if no longer needed."

# Depois:
echo "  Note: opencode.json was NOT removed."
echo "  Remove it manually if no longer needed."
```

**Step 2:** Na função `print_project_summary()` (linha 1278), verificar se há menção a AGENTS.md e remover se existir.

**Step 3:** Rodar validação:

```bash
bash -n install.sh
```

**Step 4:** Commit

```bash
git add install.sh
git commit -m "chore: remove stale AGENTS.md references from install.sh messages"
```

## Test Strategy

- **Syntax check**: `bash -n install.sh` deve passar sem erros
- **Dry-run install**: `bash install.sh --project --dry-run --targets=cursor` deve mostrar apenas 3 rules
- **Dry-run update**: `bash install.sh --project --update --dry-run` deve mostrar limpeza de rules obsoletas
- **Grep validation**: `grep -n "AGENTS.md" install.sh` deve retornar vazio
- **Grep core rules**: `grep -n "get_core_rules" install.sh` deve mostrar as 3 referências

## Ordem de Execução

1 → 2 → 3 → 4 (sequencial, cada task depende da anterior)
