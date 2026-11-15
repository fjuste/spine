---
summary: >-
  Target stacks Spine serves (Python/PHP backends, MySQL/Postgres, IaC) and
  the pragmatic patterns it pushes (service layer, optional repository, TDD);
  repo directory layout. Open before changing architecture or repo structure.
---

# System Patterns

## Stack
- **Linguagens**: PHP, Python, JavaScript (frontend), Shellscript
- **Frameworks Backend**: FastAPI, Flask, Django, Magento 1/2, WordPress
- **ORM/Modelagem Python**: SQLAlchemy, SQLModel, Pydantic
- **Banco de dados**: MySQL, PostgreSQL (SQLite apenas secundário)
- **Infra/Serviços**: Nginx, PHP-FPM, Redis, Elasticsearch
- **IaC/Automação**: Terraform, Ansible

## Arquitetura
Arquitetura pragmática orientada a backend, com foco em simplicidade operacional, testabilidade e entrega incremental.

## Padroes de Design
- Service Layer para regras de negócio.
- Repositório/DAO quando a complexidade de acesso a dados justificar.
- TDD aplicado em partes críticas para controle de regressão.

## Estrutura de Diretorios
```
docs/
  workflow/   # Gitflow operacional e ciclo de entrega
  governance/ # Policy de skills e governança leve
  quality/    # Guard rails de testes e qualidade
  memory/     # Contexto global, roadmap, progresso e decisões
skills/
  ...         # Catálogo bruto (uso controlado por allowlist)
templates/
  opencode.json  # Template para projetos consumidores (3 rules + compaction)
  docs/          # Templates do memory bank para bootstrap
commands/        # Slash commands (/spine-plan, /spine-execute, etc.)
rules/           # Rules fonte (core-protocol, memory-bank, code-quality)
scripts/         # Scripts operacionais (ex.: update de projetos consumidores)
```
