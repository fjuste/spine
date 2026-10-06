#!/usr/bin/env bash
set -uo pipefail

# Validate MkDocs + Spine integration in a consumer project.
# Thin wrapper: logic lives in spine_validate.py (cross-platform).
#
# Usage (from project root):
#   python3 .spine/scripts/spine_validate.py mkdocs
#   bash .spine/scripts/validate-mkdocs-integration.sh
#   bash .spine/scripts/validate-mkdocs-integration.sh --dry-run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
[[ -n "$PY" ]] || { echo "ERROR: python3 not found (required by Spine validators)" >&2; exit 1; }
exec "$PY" "$SCRIPT_DIR/spine_validate.py" mkdocs "$@"
