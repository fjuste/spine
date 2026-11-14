# 010-spine-promote-auto-description

## Objetivo
Adicionar ao comando `/spine-promote` a capacidade de auto-gerar a descrição do commit (Why, What changed, Validation, Notes) analisando automaticamente o diff das mudanças staged.

## Inputs
- `commands/spine-promote.md` (arquivo atual)

## Outputs Esperados
- `commands/spine-promote.md` atualizado com instrução de análise automática do diff
- Task registrada e ledger atualizado

## Criterio de Aceite
- [ ] Comando instrui agente a executar `git diff --staged` antes de compor a mensagem
- [ ] Campos do commit body (Why, What changed, Validation, Notes) são pré-preenchidos automaticamente baseado na análise do diff
- [ ] Subject line e commit type são sugeridos automaticamente se `$ARGUMENTS` estiver vazio
- [ ] Usuário mantém controle: confirmação obrigatória antes do commit final
- [ ] `docs/memory/ledger/progress.md` atualizado

## Status: DONE
