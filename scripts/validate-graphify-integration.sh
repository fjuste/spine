#!/usr/bin/env bash
set -uo pipefail

# Validate Graphify + Spine tri-platform integration in a consumer project.
#
# Usage (from project root):
#   bash .spine/scripts/validate-graphify-integration.sh
#   bash .spine/scripts/validate-graphify-integration.sh --targets=cursor,opencode,claude
#   bash .spine/scripts/validate-graphify-integration.sh --dry-run

DRY_RUN=false
TARGETS="cursor,opencode,claude"
MIN_GRAPHIFY_VERSION="0.7.16"

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --targets=*) TARGETS="${arg#--targets=}" ;;
        -h|--help)
            echo "Usage: bash .spine/scripts/validate-graphify-integration.sh [--targets=LIST] [--dry-run]"
            echo "Checks graph artifacts and Cursor, OpenCode, Claude Code Graphify integration."
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

if $DRY_RUN; then
    echo "[DRY-RUN] Would validate Graphify integration from: $(pwd)"
fi

errors=0
warnings=0
fail() { echo "ERROR: $*" >&2; errors=$((errors + 1)); }
warn() { echo "WARNING: $*" >&2; warnings=$((warnings + 1)); }
ok() { echo "  $1: OK ($2)"; }

INSTALL_CURSOR=false
INSTALL_OPENCODE=false
INSTALL_CLAUDE=false
IFS=',' read -ra TARGET_ARRAY <<< "$TARGETS"
for target in "${TARGET_ARRAY[@]}"; do
    case "$target" in
        cursor) INSTALL_CURSOR=true ;;
        opencode) INSTALL_OPENCODE=true ;;
        claude) INSTALL_CLAUDE=true ;;
        *) warn "unknown target '$target', skipping" ;;
    esac
done

echo "Graphify integration report"
echo "  Targets: $TARGETS"

# --- Graph artifacts ---
if [[ -f graphify-out/graph.json ]]; then
    ok "Graph" "graphify-out/graph.json"
else
    fail "missing graphify-out/graph.json (run bash .spine/install.sh and answer yes at Graphify prompt; non-interactive: --with-graphify)"
fi

if [[ -f graphify-out/GRAPH_REPORT.md ]]; then
    ok "Report" "graphify-out/GRAPH_REPORT.md"
else
    if [[ -f graphify-out/graph.json ]]; then
        warn "missing graphify-out/GRAPH_REPORT.md (stale or partial build?)"
    fi
fi

if [[ -f .graphifyignore ]]; then
    ok "Ignore" ".graphifyignore"
else
    warn "missing .graphifyignore"
fi

# --- CLI ---
if command -v graphify >/dev/null 2>&1; then
    version="$(graphify --version 2>/dev/null || true)"
    if [[ -z "$version" ]]; then
        version="(unknown version)"
        ok "CLI" "graphify on PATH — $version"
    else
        ok "CLI" "graphify $version"
        # Best-effort semver compare when version string is parseable
        if [[ "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
            v_major="${BASH_REMATCH[1]}"
            v_minor="${BASH_REMATCH[2]}"
            min_major="${MIN_GRAPHIFY_VERSION%%.*}"
            rest="${MIN_GRAPHIFY_VERSION#*.}"
            min_minor="${rest%%.*}"
            if (( v_major < min_major )) || { (( v_major == min_major )) && (( v_minor < min_minor )); }; then
                warn "graphifyy $version < recommended $MIN_GRAPHIFY_VERSION"
            fi
        fi
    fi
else
    fail "graphify CLI not on PATH (uv tool install graphifyy)"
fi

# --- Cursor ---
if $INSTALL_CURSOR; then
    if [[ -f .cursor/rules/graphify.mdc ]]; then
        ok "Cursor" ".cursor/rules/graphify.mdc"
    else
        fail "missing .cursor/rules/graphify.mdc (run graphify cursor install)"
    fi
    if [[ -L .cursor/rules/02-memory-bank.md ]] || [[ -f .cursor/rules/02-memory-bank.md ]]; then
        ok "Cursor" "Spine memory-bank rule present"
    else
        warn "Spine .cursor/rules/02-memory-bank.md not found (run bash .spine/install.sh)"
    fi
    # Antigravity consumes the same Graphify always-on rule via .agents/rules/
    if [[ -d .agents/rules ]]; then
        if [[ -f .agents/rules/graphify.mdc ]]; then
            ok "Antigravity" ".agents/rules/graphify.mdc"
        else
            warn "missing .agents/rules/graphify.mdc (re-run install-graphify or mirror from .cursor/rules/)"
        fi
    fi
fi

# --- OpenCode ---
if $INSTALL_OPENCODE; then
    if [[ -f .opencode/plugins/graphify.js ]]; then
        ok "OpenCode" ".opencode/plugins/graphify.js"
    else
        fail "missing .opencode/plugins/graphify.js (run graphify opencode install)"
    fi
    if [[ -f opencode.json ]] && grep -q graphify opencode.json 2>/dev/null; then
        ok "OpenCode" "graphify plugin registered in opencode.json"
    else
        fail "graphify plugin not registered in project opencode.json (run merge-graphify-opencode.py)"
    fi
    if [[ -f opencode.json ]] && grep -q "02-memory-bank.md" opencode.json 2>/dev/null; then
        ok "OpenCode" "Spine instructions present in opencode.json"
    else
        warn "Spine instructions missing from opencode.json"
    fi
fi

# --- Claude Code ---
if $INSTALL_CLAUDE; then
    claude_ok=false
    if [[ -f CLAUDE.md ]] && grep -qi graphify CLAUDE.md 2>/dev/null; then
        ok "Claude" "CLAUDE.md graphify section"
        claude_ok=true
    fi
    if [[ -f .claude/settings.json ]] && grep -qi graphify .claude/settings.json 2>/dev/null; then
        ok "Claude" "PreToolUse hook in .claude/settings.json"
        claude_ok=true
    fi
    if ! $claude_ok; then
        fail "missing Claude graphify integration (run graphify claude install)"
    fi
    if [[ -L .claude/skills ]] || [[ -d .claude/skills ]]; then
        ok "Claude" ".claude/skills present"
    else
        warn ".claude/skills not found (run bash .spine/install.sh --targets=claude)"
    fi
fi

if [[ $errors -gt 0 ]]; then
    echo "Graphify integration check failed with $errors error(s), $warnings warning(s)." >&2
    exit 1
fi

if [[ $warnings -gt 0 ]]; then
    echo "OK: Graphify integration passed with $warnings warning(s)."
else
    echo "OK: Graphify integration complete for targets: $TARGETS"
fi
exit 0
