# 008-install-sh-hardening

## Objetivo
Hardening do `install.sh --project`: torná-lo idempotente, com default conservador para skills, cleanup de dangling symlinks, flag `--update`, validação de saúde pós-install, cópia de templates e comando `--uninstall`.

## Inputs
- `install.sh` (modo projeto atual)
- Análise de edge cases (symlinks órfãos, default de skills, falta de templates)

## Outputs Esperados
- `install.sh` atualizado com todas as melhorias implementadas
- Tests passando

## Criterio de Aceite
- [ ] `--skills` default é `core` (não `all`)
- [ ] Cleanup de dangling symlinks funciona
- [ ] Flag `--update` faz install + cleanup
- [ ] Validação de saúde pós-install verifica symlinks
- [ ] `--project` copia `opencode.json` e `AGENTS.md` dos templates
- [ ] Flag `--uninstall` remove todos os artefatos do Spine do projeto
- [ ] Comportamento backward-compatible (sem breaking changes para usuários existentes)

## Status: DONE

Branch: feature/install-sh-hardening
Base: develop