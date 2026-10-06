# Skills Policy (Allowlist Mínima)

Tag policy for tasks, progress, and learnings: `docs/governance/memory-tags-policy.md`.

## Objetivo
Reduzir complexidade operacional e manter somente skills com valor recorrente no seu workflow.

## Instalação vs allowlist (Spine v1.3+)

- **Installed** (`python3 .spine/scripts/spine.py install`): symlinks the full skill catalog by default. Use `--core` for the minimal 5-skill profile, or `--remove-skill` to trim disk symlinks.
- **Active allowlist** (below): which skills agents should invoke in workflow (target 5–8). Installation breadth and operational allowlist are separate concerns.

## Modelo de Curadoria
- **Allowlist ativa**: skills liberadas para uso padrão.
- **Trial**: skills novas testadas por 2 ciclos.
- **Bloqueadas por padrão**: todas as demais skills fora da allowlist.
- **Limite por projeto**: manter entre 5 e 8 skills ativas para reduzir ruído (core obrigatório + skills de domínio/workflow opt-in). Skills Trial instaladas, como `grill-me`, **contam** nesse limite.
- **Ferramentas complementares**: utilitários como Graphify podem ser adotados por projeto consumidor sem virar dependência obrigatória do framework.

## Critérios de Entrada na Allowlist
- Uso recorrente no trabalho real (mínimo de 2 usos úteis em 30 dias).
- Redução mensurável de retrabalho, risco ou tempo.
- Alinhamento com stack principal do projeto.

## Critérios de Remoção
- Sem uso recorrente nos últimos 30 dias.
- Gera ruído, ambiguidade ou sobreposição com skill já ativa.
- Induz overengineering para tarefas simples.

## Níveis de Ativação

### Core obrigatório
- `writing-plans`
- `executing-plans`
- `test-driven-development`
- `systematic-debugging`
- `verification-before-completion`

### Trial (entrada)
- Skill nova entra como `Trial` por 2 ciclos.
- Promoção para allowlist exige:
  - 2 ou mais usos úteis em 30 dias
  - ganho claro em tempo/qualidade
  - ausência de conflito com skills já ativas

### Trial (Workflow — planejamento)
- `grill-me` — descoberta iterativa antes de `@writing-plans` em `/spine-plan` (escopo ambíguo, multi-domínio ou opt-in explícito). Inclui domain awareness: desafia termos contra `docs/memory/global/domain-glossary.md`, afia linguagem vaga, stress-testa cenários, cruza código com afirmações do usuário, e promove termos/decisões para o memory bank. Instalar com `python3 .spine/scripts/spine.py install --add-skill=grill-me`.
- **Promoção prevista:** após 2 ciclos de Trial com critérios atendidos, mover para **Workflow e Qualidade** (permanece opt-in por projeto; não entra no core).
- **Não substitui** `writing-plans` nem `handoff-protocol`: `grill-me` resolve decisões antes do plano; `writing-plans` estrutura tarefas; `handoff-protocol` governa repasse entre agentes na execução.

## Perfis por Stack

### Perfil cloudflare-api
- Core obrigatório
- `cloudflare-workers-expert`
- `bash-defensive-patterns` (quando houver scripts de deploy/ops)

### Perfil cloudflare-astro
- Core obrigatório
- `cloudflare-workers-expert`
- `astro`
- `playwright-cli` (default para exploração e validação UI/E2E)
- `playwright-skill` (escalar apenas para fluxo multi-etapas ou reexecução frequente)

### Perfil backend-py-php
- Core obrigatório
- `python-patterns` e/ou `php-pro`
- `postgresql`, `postgres-best-practices`, `sql-pro` (quando houver banco)
- `linux-troubleshooting` (quando houver operação local/servidor)

## Allowlist Base Recomendada

### Backend Python/PHP
- `python-patterns`
- `fastapi-pro`
- `django-pro`
- `php-pro`

### Banco e Dados
- `postgresql`
- `postgres-best-practices`
- `sql-pro`

### Infra e Operação
- `terraform-infrastructure`
- `bash-defensive-patterns`
- `linux-troubleshooting`

### Workflow e Qualidade
- `gitflow`
- `testing-guidelines`
- `handoff-protocol`
- `grill-me` (após promoção de Trial; opcional — ver Diretriz Operacional: Planejamento)
- `documentation-driven-development` (quando MkDocs ativo no projeto; opcional — ver [README § Optional: MkDocs](https://github.com/fjuste/spine#optional-mkdocs))

### Frontend Assistido (principal)
- `frontend-dev-guidelines`
- `astro` (quando Astro no projeto)
- `playwright-cli` (default para UI/E2E curto e iterativo)
- `playwright-skill` (escalar apenas quando houver complexidade real)

### Frontend (opcional, quando React/Next)
- `react-best-practices`

### Cloudflare
- `cloudflare-workers-expert`

## Diretriz Operacional: Planejamento

Use esta regra para evitar ambiguidade entre descoberta e estruturação de planos:

- **Pipeline fixo:** `@grill-me` (descoberta, condicional) → `@writing-plans` (preenche `_task-template.md`, obrigatório) → gate `/spine-plan`.
- **Contrato de tarefa:** frontmatter YAML + seções fixas; detalhe Task/Step opcional em `## Implementation Plan` (omitir se ≤3 critérios de aceite).
- **Default simples:** escopo claro e single-domain → pular `@grill-me`, ir direto para `@writing-plans`.
- **Escalar descoberta:** usar `@grill-me` quando escopo for ambíguo, multi-domínio, ou houver decisões arquiteturais/segurança/schema/infra em aberto.

### Quando usar `@grill-me`
- Escopo ambíguo ou amplo (ex.: "melhorar performance").
- Múltiplos domínios na mesma entrega (ex.: backend + infra + UI).
- Decisões arquiteturais ou de segurança ainda não resolvidas.
- Opt-in explícito em `/spine-plan`: `grill me`, `grill:`, `grill -`, `grill with docs`, `grill:docs`, `stress-test`, `challenge this`.
- Opt-in com documentação de domínio: `grill with docs` ou `grill:docs` — mesma skill, com expectativa de atualização inline de `domain-glossary.md` e `decision-log.md`.
- Opt-in conversacional: usuário pede para ser "grilled" antes do plano ser escrito.

### Quando pular `@grill-me`
- Escopo claro, entregável único, single-domain.
- Opt-out explícito: `skip discovery`, `no grill`, `direct plan`.

### Regra de desempate (anti-overengineering)
- Se o escopo já define MVP, out-of-scope e domínio principal, não use `@grill-me`.
- `@grill-me` faz uma pergunta por vez; não escreva o plano completo até a descoberta terminar.
- Registre decisões em `## Discovery notes` no arquivo de tarefa ativa antes de `@writing-plans`.
- **Promoção de conhecimento:** decisões de escopo da tarefa → `## Discovery notes`; termos canônicos de domínio → `domain-glossary.md`; decisões arquiteturais (critério triplo: difícil reverter, surpreendente sem contexto, trade-off real) → `decision-log.md`.

### Relação com outras skills de workflow
- **`writing-plans`:** sempre após descoberta (ou após skip). Preenche `_task-template.md` (frontmatter + seções); Task/Step só em `## Implementation Plan`.
- **`executing-plans`:** lê frontmatter e Implementation Plan; para em `REVIEW` — `/spine-harvest` fecha a entrega.
- **`handoff-protocol`:** aplica-se na execução multi-agente, não substitui descoberta de escopo.

## Diretriz Operacional: Playwright

Use esta regra curta para evitar ambiguidade e overengineering:

- **Default simples:** comece com `playwright-cli`.
- **Escalar apenas quando necessário:** use `playwright-skill` somente quando a tarefa exigir script custom, fluxo multi-etapas (E2E), validações múltiplas ou reexecução frequente.

### Quando usar `playwright-cli`
- Exploração rápida de UI.
- Debug pontual de interação/estado.
- Ações curtas e iterativas (abrir, clicar, snapshot, validar elemento).

### Quando usar `playwright-skill`
- Fluxo E2E completo (ex.: login -> navegação -> validações).
- Cenários repetíveis que se beneficiam de script em `/tmp`.
- Casos com controle mais robusto (tratamento de erro, múltiplas etapas e artefatos).

### Regra de desempate (anti-overengineering)
- Se a tarefa puder ser resolvida em poucos comandos interativos, mantenha `playwright-cli`.
- Migre para `playwright-skill` apenas ao encontrar complexidade real durante a execução.

## Processo Mensal de Revisão
1. Listar skills efetivamente usadas no mês (frequência e contexto).
   - Para Playwright, usar os registros do `/spine-harvest` (skill escolhida, motivo e evidência de ganho).
   - Para planejamento (`grill-me`), contar sessões em que `## Discovery notes` foi preenchido em `docs/memory/active_tasks/` ou o usuário registrou opt-in/opt-out explícito em `/spine-plan`. Incluir atualizações a `domain-glossary.md` e `decision-log.md` originadas de sessões de grill.
2. Confirmar quais skills reduziram tempo/retrabalho.
3. Remover as não recorrentes ou redundantes.
4. Promover/demover Trial conforme critérios objetivos.
   - `grill-me`: promover para Workflow e Qualidade se ≥2 usos úteis em 30 dias **e** planos resultantes tiverem menos retrabalho de escopo (menos splits tardios, menos critérios de aceite reescritos pós-execução).
5. Atualizar este documento.

## Sincronização em Projetos Consumidor

Este arquivo é copiado para `docs/governance/skills-policy.md` pelo `python3 .spine/scripts/spine.py install`. Atualizações posteriores no template Spine **não** sobrescrevem automaticamente o arquivo local. Após pull do Spine, revisar manualmente diferenças entre `templates/docs/governance/skills-policy.md` (Spine) e `docs/governance/skills-policy.md` (projeto) e incorporar mudanças relevantes.