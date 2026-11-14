---
summary: >-
  Dev setup (feature/* from develop, promotion chain), main dependencies of
  target projects, technical constraints (no overengineering, curated skills,
  tests + memory update per delivery) and example env vars. Open before
  changing workflow constraints or setup.
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
