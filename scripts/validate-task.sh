#!/usr/bin/env bash
set -uo pipefail

# Validate a Memory Bank active task file against the v2.1 contract.
# Thin wrapper: logic lives in spine_validate.py (cross-platform).
#
# Usage (from consumer project root):
#   python3 .spine/scripts/spine_validate.py task docs/memory/active_tasks/007-foo.md
#   bash .spine/scripts/validate-task.sh docs/memory/active_tasks/007-foo.md
#   bash .spine/scripts/validate-task.sh --dry-run path/to/task.md

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
[[ -n "$PY" ]] || { echo "ERROR: python3 not found (required by Spine validators)" >&2; exit 1; }
exec "$PY" "$SCRIPT_DIR/spine_validate.py" task "$@"
