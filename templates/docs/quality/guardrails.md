# Guard Rails de Qualidade

## Objetivo
Garantir controle de entrega com testes e prevenção de regressão.

## Regra Base
Toda tarefa deve incluir:
1. Plano de execução.
2. Plano de testes.
3. Evidência de execução dos testes.

## Plano de Testes Mínimo por Tarefa
- **Caso positivo**: caminho esperado funciona.
- **Caso negativo**: entrada inválida/erro controlado.
- **Regressão**: valida que comportamento antigo crítico não quebrou.

## Tipos de Teste (aplicar conforme escopo)
- Unitário: regra de negócio e funções críticas.
- Integração: serviços, banco e contratos.
- E2E/funcional: fluxos críticos de usuário (quando aplicável).
- Smoke pós-release: sanidade em produção/staging.

## Gate de Merge
- Critério de aceite atendido.
- Plano de testes executado.
- Sem falhas críticas abertas.
- Memory-bank atualizado com aprendizado.

## Registro de Aprendizado Obrigatório
Para incidentes, bugs e retrabalhos, registrar em `docs/memory/ledger/learnings/` (um arquivo por `LEARN-NNN`, com `tags:` no frontmatter per `docs/governance/memory-tags-policy.md`; depois `python3 .spine/scripts/spine.py memory index`):
- Causa-raiz.
- Como detectar cedo.
- Teste que evita recorrência.
- Regra operacional adicionada/ajustada.
