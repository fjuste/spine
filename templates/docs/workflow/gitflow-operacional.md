# Gitflow Operacional (Solo Dev)

## Objetivo
Padronizar um ciclo simples, seguro e repetível para desenvolvimento solo, sem overengineering.

## Branches Oficiais
- `main`: branch canônica do código.
- `develop`: integração contínua de features concluídas.
- `staging`: validação pré-produção.
- `production`: espelho do que está em produção.

## Branches Temporárias
- `feature/<tema-curto>`: desenvolvimento de funcionalidade.
- `hotfix/<tema-curto>`: correção urgente de produção.
- `release/<versao>`: estabilização para entrega.

## Fluxo Padrão de Feature
1. Criar `feature/*` a partir de `develop`.
2. Implementar com teste (ou plano de teste) antes do merge.
3. Atualizar memory-bank (entrada em `ledger/deliveries/` + Current state em `progress.md`, entradas em `ledger/learnings/` e `ledger/decisions/` quando aplicável, `spine.py memory index`; task em `completed_tasks/` após harvest).
4. Merge de `feature/*` em `develop`.
5. Promover `develop` para `staging`.
6. Validar checklist de release.
7. Promover `staging` para `production`.
8. Sincronizar `production` com `main`.

## Fluxo de Hotfix
1. Criar `hotfix/*` a partir de `production` (ou `main` se for o espelho de produção).
2. Corrigir + criar teste de regressão.
3. Merge em `production` e `main`.
4. Reaplicar em `develop` para evitar divergência.

## Regras de Segurança
- Sem commit direto em `main`/`production`/`staging`.
- Toda entrega precisa de evidência de teste.
- Toda entrega precisa atualizar memory-bank.
- Se não há critério de aceite claro, a tarefa não inicia.

## Convenções de Nome
- Feature: `feature/auth-login-social`
- Hotfix: `hotfix/carrinho-timeout`
- Release: `release/2026.04.0`

## Checklist de Promoção (staging -> production)
- Testes do escopo executados.
- Regressão mínima executada.
- Memory-bank atualizado.
- Aprendizado de ciclo registrado.
