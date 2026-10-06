"""Shared installer constants.

``DOCS_SEED_PATHS`` is the single seed list. ``spine_validate`` imports it
from here so the validator and the installer cannot drift.
"""

from __future__ import annotations

CORE_SKILLS: tuple[str, ...] = (
    "writing-plans",
    "executing-plans",
    "test-driven-development",
    "systematic-debugging",
    "verification-before-completion",
)

CORE_RULES: tuple[str, ...] = (
    "01-core-protocol.md",
    "02-memory-bank.md",
    "03-code-quality.md",
)

DEFAULT_TARGETS = "cursor,opencode,claude,antigravity"
KNOWN_TARGETS: frozenset[str] = frozenset(
    {"cursor", "opencode", "claude", "antigravity"}
)

# Paths relative to the consumer project root. Templates live under
# templates/docs/<path-without-docs-prefix>.
DOCS_SEED_PATHS: tuple[str, ...] = (
    "docs/memory/global/project-brief.md",
    "docs/memory/global/product-context.md",
    "docs/memory/global/domain-glossary.md",
    "docs/memory/global/system-patterns.md",
    "docs/memory/global/tech-context.md",
    "docs/memory/global/decision-log.md",
    "docs/memory/ledger/roadmap.md",
    "docs/memory/ledger/progress.md",
    "docs/memory/ledger/learnings.md",
    "docs/memory/active_tasks/_task-template.md",
    "docs/governance/skills-policy.md",
    "docs/governance/memory-tags-policy.md",
    "docs/governance/ice-scoring-guide.md",
    "docs/quality/guardrails.md",
    "docs/workflow/gitflow-operacional.md",
    "docs/workflow/ciclo-de-entrega.md",
)

DOCS_SEED_DIRS: tuple[str, ...] = (
    "docs/documentation",
    "docs/memory/active_tasks",
    "docs/memory/completed_tasks",
)

DOCS_GITKEEP_PATHS: tuple[str, ...] = (
    "docs/memory/active_tasks/.gitkeep",
    "docs/memory/completed_tasks/.gitkeep",
)

SYMLINK_GITIGNORE_ADD: tuple[str, ...] = (".spine", ".agents/")
COPY_GITIGNORE_ADD: tuple[str, ...] = (".spine",)
SYMLINK_GITIGNORE_REMOVE: tuple[str, ...] = (
    ".cursor/",
    ".claude/",
    ".opencode/",
    ".spine-vendor",
)
COPY_GITIGNORE_REMOVE: tuple[str, ...] = SYMLINK_GITIGNORE_REMOVE + (
    ".agents/",
    ".agents",
)

VENDOR_GITIGNORE_STRIP: tuple[str, ...] = (
    ".spine",
    ".agents/",
    ".cursor/",
    ".claude/",
    ".opencode/",
)

# Directory names skipped anywhere in a vendored or rsync copy.
COPY_SKIP_ANYWHERE: frozenset[str] = frozenset(
    {
        ".git",
        ".cursor",
        ".claude",
        ".opencode",
        ".agents",
        "graphify-out",
        "node_modules",
        ".venv",
        "__pycache__",
        ".spine-vendor",
    }
)

# Skipped only at the root of an rsync-mode copy (templates/docs must remain).
RSYNC_SKIP_ROOT: frozenset[str] = frozenset({"docs", ".spine"})

# Vendor copy also drops root ``docs/`` (consumer memory bank is not Spine).
VENDOR_SKIP_ROOT: frozenset[str] = frozenset({"docs"})

CANONICAL_SOURCE_FILE = ".spine-canonical-source"
VENDOR_MARKER = ".spine-vendor"
MKDOCS_GITIGNORE_ENTRY = "docs/mkdocs/site/"
MIN_GRAPHIFY_VERSION = (0, 7, 16)
