---
summary: >-
  Why Spine exists: one reusable, consistent workflow across local projects;
  problems it solves (process drift, lost learnings, uncurated skills, missing
  test guard rails); high-level task cycle, UX goals and Known Opportunities
  (unplanned). Open before changing product direction or user-facing workflow.
---

# Product Context

## Por que este projeto existe?
Para servir como base de instruções coesas e reutilizáveis entre projetos locais, reduzindo variação de processo e retrabalho.

## Problemas que resolve
- Falta de padrão único de workflow.
- Dificuldade de manter aprendizado entre ciclos.
- Excesso de skills sem curadoria.
- Entregas sem guard rails de testes consistentes.

## Como deve funcionar (visao de alto nivel)
Cada tarefa segue um ciclo simples: branch de feature -> plano de execução e testes -> implementação -> validação -> registro no memory-bank -> promoção de ambientes.

## Experiencia do Usuario (UX Goals)
- Fluxo operacional claro, direto e repetível.
- Fricção mínima para iniciar e concluir entregas.
- Documentação curta, útil e acionável.

## Known Opportunities (unplanned)
- Fence-aware `memory._section`: the digest and budget checks end a section at a `## ` line inside a fenced code block. Never seen in a real Current state yet; `spine_cli/migrate.py` already has a fence-aware section finder (`_outside_fences`). Task 022.
- `spine_validate.py task` counts every indented `- ` item in the frontmatter as a tag, so a block-list `related_learnings` with 3+ items trips "too many tags". Workaround: inline `[LEARN-…]`. Fix: count only items under `tags:`. Task 022.
