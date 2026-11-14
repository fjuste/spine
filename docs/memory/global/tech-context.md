---
summary: >-
  Dev setup (feature/* from develop, promotion chain), main dependencies of
  target projects, technical constraints (no overengineering, curated skills,
  tests + memory update per delivery), example env vars and Known Risks (partly
  tracked docs/memory). Open before changing workflow constraints or setup.
---

# Tech Context

## Setup de Desenvolvimento
- Repositório usado como base documental reutilizável por links simbólicos.
- Fluxo principal de trabalho: branch `feature/*` a partir de `develop`.
- Promoção entre ambientes: `develop` -> `staging` -> `production` -> `main`.

## Dependencias Principais
- Python: FastAPI, Flask, Django, Pydantic, SQLModel, SQLAlchemy.
- PHP: Magento 1, Magento 2, WordPress.
- Infra: Terraform, Ansible, Nginx, PHP-FPM, Redis, Elasticsearch.
- Banco: MySQL e PostgreSQL.

## Constraints Tecnicos
- Evitar overengineering em processos e arquitetura.
- Evitar expansão de skills sem curadoria e evidência de uso.
- Toda entrega precisa de plano de testes e atualização de memória.

## Variaveis de Ambiente
| Variavel | Descricao | Exemplo |
|---|---|---|
| APP_ENV | Ambiente atual | development |
| DB_DRIVER | Banco principal do projeto alvo | postgresql |
| WORKFLOW_MODE | Modo do ciclo | solo-gitflow |

## Known Risks
- Spine's `docs/` is gitignored, but some memory files are force-tracked (globals, `progress.md`, `roadmap.md`, ledger `INDEX.md` files and harvested entries). Task files and new entry files stay untracked unless added with `git add -f`; changes to tracked files under `docs/` stage with `git add -u -- <paths>`. A plain `git add docs/...` fails with an "ignored" error. Task 022.
