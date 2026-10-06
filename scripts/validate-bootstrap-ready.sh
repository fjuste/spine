#!/usr/bin/env bash
set -uo pipefail

# Validate consumer project readiness for /spine-bootstrap (setup artifacts only).
# Thin wrapper: logic lives in spine_validate.py (cross-platform).
#
# Usage (from project root):
#   python3 .spine/scripts/spine_validate.py bootstrap
#   bash .spine/scripts/validate-bootstrap-ready.sh
#   bash .spine/scripts/validate-bootstrap-ready.sh --dry-run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$(command -v python3 || command -v python || true)"
[[ -n "$PY" ]] || { echo "ERROR: python3 not found (required by Spine validators)" >&2; exit 1; }
exec "$PY" "$SCRIPT_DIR/spine_validate.py" bootstrap "$@"
