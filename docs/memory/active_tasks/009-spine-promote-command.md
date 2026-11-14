# 009-spine-promote-command

## Objetivo
Criar um comando maintainer-only `/spine-promote` para automatizar o commit detalhado no Spine e a promoção em cascata pelas branches `develop -> staging -> production -> main`, retornando finalmente a `develop`.

## Inputs
- Estrutura existente de comandos em `commands/`
- Regras de GitFlow em `rules/06-gitflow.md`
- Padrão de qualidade de commit do `commands/spine-commit.md`

## Outputs Esperados
- `commands/spine-promote.md` — comando completo e documentado
- Task file registrado e ledger atualizado

## Criterio de Aceite
- [x] Arquivo `commands/spine-promote.md` criado com header YAML e corpo detalhado
- [x] Comando valida que está no repo `spine` antes de executar
- [x] Comando exige que o usuário esteja na branch `develop`
- [x] Commit segue Conventional Commits com body estruturado (Why, What, Validation, Notes)
- [x] Push para `origin develop` realizado
- [x] Promoção em cascata: `staging`, `production`, `main` (merge direto, sem PR)
- [x] Retorno obrigatório para `develop` ao final
- [x] Guard rails: nunca push --force, aborta em conflitos, aborta se não for repo spine
- [x] Documentação clara de que é SPINE-INTERNAL e não deve ir para consumer projects
- [x] `docs/memory/ledger/progress.md` atualizado

## Status: DONE
