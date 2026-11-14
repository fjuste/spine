# 011-graphify-integration

## Objetivo
Introduzir o Graphify como ferramenta recomendada (não dependência) no ecossistema Spine, garantindo que comandos, regras e templates do Spine tenham ciência da sua presença para evitar ambiguidade e sobreposição.

## Inputs
- `templates/AGENTS.md`
- `templates/docs/memory/global/system-patterns.md`
- `commands/spine-install.md`
- `commands/spine-bootstrap.md`
- Estrutura atual de `tests/`

## Outputs Esperados
- `templates/dot.graphifyignore` — template de ignore padrão para projetos Spine
- `templates/AGENTS.md` atualizado com seção sobre ferramentas opcionais
- `commands/spine-install.md` atualizado com nota de coexistência Graphify
- `commands/spine-bootstrap.md` atualizado para reconhecer `graphify-out/` e `.graphifyignore`
- `templates/docs/memory/global/system-patterns.md` atualizado com menção ao Graphify
- `tests/unit/test_graphify_integration.py` — teste de regressão
- `docs/memory/ledger/progress.md` atualizado

## Criterio de Aceite
- [ ] `templates/dot.graphifyignore` existe e exclui artefatos Spine (`AGENTS.md`, `.spine`, `.agents/`, `.cursor/`, `.opencode/`, `docs/translations/`)
- [ ] `templates/AGENTS.md` contém seção sobre Graphify como ferramenta opcional recomendada
- [ ] `commands/spine-install.md` menciona que Graphify pode coexistir e que `opencode.json` faz merge seguro de plugins
- [ ] `commands/spine-bootstrap.md` reconhece `graphify-out/` e `.graphifyignore` durante assessment
- [ ] `templates/docs/memory/global/system-patterns.md` menciona Graphify como ferramenta complementar de code intelligence
- [ ] Teste em `tests/unit/test_graphify_integration.py` passa validando existência e conteúdo do template `.graphifyignore`
- [ ] `docs/memory/ledger/progress.md` atualizado com o novo estado

## Status: PLANNING

---

# Graphify Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Graphify as a recommended optional tool to the Spine framework with explicit coexistence rules and no ambiguity.

**Architecture:** Extend Spine templates and command specs to recognize Graphify artifacts, provide a default `.graphifyignore`, and document the relationship so agents never conflict.

**Tech Stack:** Markdown, Python (pytest), Bash

---

## Suggested execution skill: @executing-plans

## Branch: feature/graphify-integration
## Base: develop

---

### Task 1: Create `templates/dot.graphifyignore`

**Files:**
- Create: `templates/dot.graphifyignore`
- Test: `tests/unit/test_graphify_integration.py`

**Step 1: Write the failing test**

```python
def test_graphifyignore_template_exists():
    from pathlib import Path
    template = Path("templates/dot.graphifyignore")
    assert template.exists(), "templates/dot.graphifyignore must exist"
    content = template.read_text()
    assert "AGENTS.md" in content
    assert ".spine" in content
    assert ".agents/" in content
    assert ".cursor/" in content
    assert ".opencode/" in content
    assert "docs/translations/" in content
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_graphify_integration.py::test_graphifyignore_template_exists -v`
Expected: FAIL with "templates/dot.graphifyignore must exist"

**Step 3: Write minimal implementation**

Create `templates/dot.graphifyignore`:
```
# Spine ecosystem files — do not extract agent instructions as knowledge
AGENTS.md
CLAUDE.md
GEMINI.md
AGENTS-original.md

# Spine per-project symlinks and local tooling
.spine
.agents/
.cursor/
.claude/
.opencode/
.copilot/
.kiro/
.trae/
.factory/

# Generated translations and machine-specific configs
docs/translations/

# Graphify local-only files (optional: keep for shared speed)
graphify-out/cache/
graphify-out/manifest.json
graphify-out/cost.json
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_graphify_integration.py::test_graphifyignore_template_exists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add templates/dot.graphifyignore tests/unit/test_graphify_integration.py
git commit -m "feat: add graphifyignore template for Spine projects"
```

---

### Task 2: Update `templates/AGENTS.md` with optional tools section

**Files:**
- Modify: `templates/AGENTS.md`
- Test: `tests/unit/test_graphify_integration.py`

**Step 1: Write the failing test**

```python
def test_agents_md_has_graphify_section():
    from pathlib import Path
    agents = Path("templates/AGENTS.md").read_text()
    assert "## 10." in agents or "Optional Tools" in agents or "graphify" in agents.lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_graphify_integration.py::test_agents_md_has_graphify_section -v`
Expected: FAIL

**Step 3: Write minimal implementation**

Append to `templates/AGENTS.md` before the final line (if any):
```markdown
---

## 10. Optional Tools

### Graphify (recommended)

This project may use [Graphify](https://github.com/safishamsi/graphify) as a complementary code-intelligence tool.

Rules when Graphify is present:
- `graphify-out/GRAPH_REPORT.md` may be read before answering architecture questions.
- After modifying code files, run `graphify update .` to keep the graph current (AST-only, no API cost).
- `graphify-out/` should be committed to git (except `cache/`, `manifest.json`, `cost.json`).
- The `.graphifyignore` file controls what Graphify extracts. A default template is available at `templates/dot.graphifyignore`.

Graphify is **not** a dependency of Spine. It is an optional enhancement.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_graphify_integration.py::test_agents_md_has_graphify_section -v`
Expected: PASS

**Step 5: Commit**

```bash
git add templates/AGENTS.md tests/unit/test_graphify_integration.py
git commit -m "docs: add graphify as optional recommended tool in AGENTS template"
```

---

### Task 3: Update `commands/spine-install.md` for Graphify coexistence

**Files:**
- Modify: `commands/spine-install.md`

**Step 1: Add note in opencode.json handling section**

In `commands/spine-install.md`, after the `opencode.json` handling section (around line 90-92), add:

```markdown
#### Graphify coexistence note

If the project already uses Graphify, its `opencode.json` may contain a `"plugin"` key (e.g. `[".opencode/plugins/graphify.js"]`). The merge above must preserve this key alongside `"instructions"`. Do not remove or overwrite `"plugin"`.
```

**Step 2: Commit**

```bash
git add commands/spine-install.md
git commit -m "docs: document graphify coexistence in spine-install command"
```

---

### Task 4: Update `commands/spine-bootstrap.md` to recognize Graphify artifacts

**Files:**
- Modify: `commands/spine-bootstrap.md`

**Step 1: Add Graphify detection in assessment step**

In the "Initial assessment" section (step 1), add a bullet:
- Detect whether Graphify is already in use: check for `graphify-out/`, `.graphifyignore`, or `graphify-out/GRAPH_REPORT.md`. If present, note it in the assessment summary and do not treat these as project source artifacts to be reorganized.

**Step 2: Add Graphify handling in AGENTS.md population**

In step 2 (AGENTS.md population), after the existing instructions, add:
- If `AGENTS.md` already contains a `## graphify` section (from a previous Graphify install), preserve it. Do not remove or overwrite it during bootstrap.

**Step 3: Commit**

```bash
git add commands/spine-bootstrap.md
git commit -m "docs: recognize graphify artifacts during spine-bootstrap assessment"
```

---

### Task 5: Update `templates/docs/memory/global/system-patterns.md`

**Files:**
- Modify: `templates/docs/memory/global/system-patterns.md`

**Step 1: Add Graphify mention in stack or patterns**

After the "Stack" section, add a short subsection:

```markdown
## Optional Complementary Tools

- **Graphify** — Knowledge-graph generator for codebases (AST + semantic extraction). Recommended for projects > 20 files. Not a dependency; install via `pip install graphifyy` if needed.
```

**Step 2: Commit**

```bash
git add templates/docs/memory/global/system-patterns.md
git commit -m "docs: mention graphify as optional complementary tool in system-patterns"
```

---

### Task 6: Run full test suite and validate

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass.

**Step 2: Commit (if any test fixes needed)**

```bash
git commit -m "test: validate graphify integration tests"
```

---

### Task 7: Update ledger and create decision log entry

**Files:**
- Modify: `docs/memory/ledger/progress.md`
- Modify: `docs/memory/global/decision-log.md`

**Step 1: Update progress**

Add under "O que funciona":
- Graphify documentado como ferramenta opcional recomendada no Spine, com `.graphifyignore` template e regras de coexistência.

**Step 2: Update decision log**

Add row:
| 2026-04-22 | Adotar Graphify como ferramenta opcional recomendada no Spine | Ganho de code intelligence sem acoplamento; evita conflitos entre regras do Spine e do Graphify | Rejeitar: tornar Graphify dependência obrigatória (acoplamento excessivo) |

**Step 3: Commit**

```bash
git add docs/memory/ledger/progress.md docs/memory/global/decision-log.md
git commit -m "docs: update ledger and decision log for graphify integration"
```

---

## Test Strategy

- **Positive:** `test_graphifyignore_template_exists` valida que o template existe e contém exclusões corretas.
- **Positive:** `test_agents_md_has_graphify_section` valida que o template AGENTS.md menciona Graphify.
- **Negative:** Se o template `.graphifyignore` for deletado acidentalmente, o teste falha imediatamente.
- **Regression:** Futuras modificações em `templates/AGENTS.md` não devem remover a seção de Graphify sem que o teste capture.

Execution command:
```bash
pytest tests/unit/test_graphify_integration.py -v
```

---

## Scope Validation

This plan covers **1 domain** (framework documentation & compatibility) with **7 acceptance criteria**.
It requires **1 execution skill** (`@executing-plans`).
It fits within a single execution session.

Proceed as-is.
