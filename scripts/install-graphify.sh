#!/usr/bin/env bash
set -uo pipefail

# Graphify + Spine co-install for consumer projects (Cursor, OpenCode, Claude Code).
#
# Usage:
#   bash scripts/install-graphify.sh --project-root=PATH [--init-graph] [--targets=cursor,opencode,claude]
#   bash scripts/install-graphify.sh --project-root=PATH --uninstall [--targets=...] [--purge-graphify]

PROJECT_ROOT=""
INIT_GRAPH=false
UNINSTALL=false
PURGE_GRAPHIFY=false
GRAPHIFY_HOOKS=false
DRY_RUN=false
TARGETS="cursor,opencode,claude"
MIN_GRAPHIFY_VERSION="0.7.16"

for arg in "$@"; do
    case "$arg" in
        --project-root=*) PROJECT_ROOT="${arg#--project-root=}" ;;
        --init-graph) INIT_GRAPH=true ;;
        --targets=*) TARGETS="${arg#--targets=}" ;;
        --graphify-hooks) GRAPHIFY_HOOKS=true ;;
        --uninstall) UNINSTALL=true ;;
        --purge-graphify) PURGE_GRAPHIFY=true ;;
        --dry-run) DRY_RUN=true ;;
        -h|--help)
            echo "Usage: bash scripts/install-graphify.sh --project-root=PATH [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --init-graph         Build graph (graphify update) and run platform co-install"
            echo "  --targets=LIST       Comma-separated: cursor,opencode,claude (default: all three)"
            echo "  --graphify-hooks     Run graphify hook install (post-commit graph refresh)"
            echo "  --uninstall          Remove Graphify platform artifacts (not graphify-out by default)"
            echo "  --purge-graphify     With --uninstall, also remove graphify-out/ and .graphifyignore"
            echo "  --dry-run            Preview without making changes"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$PROJECT_ROOT" ]]; then
    echo "ERROR: --project-root is required." >&2
    exit 1
fi

if [[ ! -d "$PROJECT_ROOT" ]]; then
    echo "ERROR: Project root not found: $PROJECT_ROOT" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPINE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE="$SPINE_DIR/templates/dot.graphifyignore"
TARGET="$PROJECT_ROOT/.graphifyignore"
MERGE_SCRIPT="$SPINE_DIR/scripts/merge-graphify-opencode.py"

INSTALL_CURSOR=false
INSTALL_OPENCODE=false
INSTALL_CLAUDE=false
IFS=',' read -ra TARGET_ARRAY <<< "$TARGETS"
for target in "${TARGET_ARRAY[@]}"; do
    case "$target" in
        cursor) INSTALL_CURSOR=true ;;
        opencode) INSTALL_OPENCODE=true ;;
        claude) INSTALL_CLAUDE=true ;;
        *) echo "WARNING: unknown target '$target', skipping" >&2 ;;
    esac
done

run_cmd() {
    if $DRY_RUN; then
        echo "    [DRY-RUN] Would run: $*"
        return 0
    fi
    (cd "$PROJECT_ROOT" && "$@")
}

graphify_version_ok() {
    if ! command -v graphify >/dev/null 2>&1; then
        return 1
    fi
    local version
    version="$(graphify --version 2>/dev/null || true)"
    if [[ -z "$version" ]]; then
        return 0
    fi
    if [[ "$version" =~ ^([0-9]+)\.([0-9]+) ]]; then
        local v_major="${BASH_REMATCH[1]}" v_minor="${BASH_REMATCH[2]}"
        local min_major="${MIN_GRAPHIFY_VERSION%%.*}"
        local rest="${MIN_GRAPHIFY_VERSION#*.}"
        local min_minor="${rest%%.*}"
        if (( v_major < min_major )) || { (( v_major == min_major )) && (( v_minor < min_minor )); }; then
            echo "    WARNING: graphifyy $version < recommended $MIN_GRAPHIFY_VERSION" >&2
            return 1
        fi
    fi
    return 0
}

uninstall_graphify_platforms() {
    echo "  - Graphify platform uninstall (targets: $TARGETS)"

    if $INSTALL_CURSOR; then
        echo "    Cursor:"
        if command -v graphify >/dev/null 2>&1; then
            run_cmd graphify cursor uninstall || echo "      WARNING: graphify cursor uninstall failed" >&2
        else
            echo "      skipped: graphify CLI not available"
        fi
    fi

    if $INSTALL_OPENCODE; then
        echo "    OpenCode:"
        if command -v graphify >/dev/null 2>&1; then
            run_cmd graphify opencode uninstall || echo "      WARNING: graphify opencode uninstall failed" >&2
        fi
        if [[ -f "$MERGE_SCRIPT" ]] && [[ -f "$PROJECT_ROOT/opencode.json" ]]; then
            if $DRY_RUN; then
                echo "    [DRY-RUN] Would strip graphify plugin from opencode.json"
            else
                python3 "$MERGE_SCRIPT" strip "$PROJECT_ROOT/opencode.json" || true
            fi
        fi
    fi

    if $INSTALL_CLAUDE; then
        echo "    Claude Code:"
        if command -v graphify >/dev/null 2>&1; then
            run_cmd graphify claude uninstall || echo "      WARNING: graphify claude uninstall failed" >&2
        else
            echo "      skipped: graphify CLI not available"
        fi
    fi

    if $PURGE_GRAPHIFY; then
        echo "  - Purge graph artifacts"
        if $DRY_RUN; then
            echo "    [DRY-RUN] Would remove graphify-out/ and .graphifyignore"
        else
            rm -rf "$PROJECT_ROOT/graphify-out"
            rm -f "$TARGET"
            echo "    removed graphify-out/ and .graphifyignore"
        fi
    else
        echo "  - Preserved graphify-out/ and .graphifyignore (use --purge-graphify to remove)"
    fi
}

install_graphify_platforms() {
    echo "  - Graphify platform co-install (targets: $TARGETS)"

    if $INSTALL_CURSOR; then
        echo "    Cursor (graphify.mdc):"
        run_cmd graphify cursor install || echo "      WARNING: graphify cursor install failed" >&2
        # Antigravity reads workspace rules from .agents/rules/ — mirror graphify.mdc
        if [[ -f "$PROJECT_ROOT/.cursor/rules/graphify.mdc" ]]; then
            if $DRY_RUN; then
                echo "    [DRY-RUN] Would mirror graphify.mdc -> .agents/rules/"
            else
                mkdir -p "$PROJECT_ROOT/.agents/rules"
                cp -a "$PROJECT_ROOT/.cursor/rules/graphify.mdc" "$PROJECT_ROOT/.agents/rules/graphify.mdc"
                echo "    mirrored graphify.mdc -> .agents/rules/ (Antigravity)"
            fi
        fi
    fi

    if $INSTALL_OPENCODE; then
        echo "    OpenCode (skill + plugin):"
        run_cmd graphify install --platform opencode || echo "      WARNING: graphify install --platform opencode failed" >&2
        run_cmd graphify opencode install || echo "      WARNING: graphify opencode install failed" >&2
        if [[ -f "$MERGE_SCRIPT" ]] && [[ -f "$PROJECT_ROOT/opencode.json" ]]; then
            if $DRY_RUN; then
                echo "    [DRY-RUN] Would merge graphify plugin into opencode.json"
            else
                local local_oc="$PROJECT_ROOT/.opencode/opencode.json"
                if [[ -f "$local_oc" ]]; then
                    python3 "$MERGE_SCRIPT" merge "$PROJECT_ROOT/opencode.json" "$local_oc" || true
                else
                    python3 "$MERGE_SCRIPT" merge "$PROJECT_ROOT/opencode.json" || true
                fi
            fi
        fi
    fi

    if $INSTALL_CLAUDE; then
        echo "    Claude Code (CLAUDE.md + PreToolUse hook):"
        run_cmd graphify claude install || echo "      WARNING: graphify claude install failed" >&2
    fi

    if $GRAPHIFY_HOOKS; then
        echo "  - Git hooks (graphify hook install)"
        run_cmd graphify hook install || echo "    WARNING: graphify hook install failed" >&2
    fi
}

if $UNINSTALL; then
    echo "Graphify uninstall:"
    uninstall_graphify_platforms
    exit 0
fi

echo "  - Graphify CLI check"
if command -v graphify >/dev/null 2>&1; then
    echo "    graphify detected: $(command -v graphify) ($(graphify --version 2>/dev/null || echo 'version unknown'))"
    graphify_version_ok || true
else
    echo "    WARNING: graphify CLI not found."
    echo "    Install globally (recommended):"
    echo "      uv tool install graphifyy  # minimum recommended: $MIN_GRAPHIFY_VERSION"
    echo "    Alternatives:"
    echo "      pipx install graphifyy"
    echo "      pip install graphifyy"
fi

echo "  - .graphifyignore"
if [[ ! -f "$TEMPLATE" ]]; then
    echo "    WARNING: template not found: $TEMPLATE"
else
    if [[ -f "$TARGET" ]]; then
        echo "    exists, preserving: $TARGET"
    else
        if $DRY_RUN; then
            echo "    [DRY-RUN] Would copy $TEMPLATE -> $TARGET"
        else
            cp "$TEMPLATE" "$TARGET"
            echo "    copied: $TARGET"
        fi
    fi
fi

if $INIT_GRAPH; then
    echo "  - initial graph build"
    if ! command -v graphify >/dev/null 2>&1; then
        echo "    skipped: graphify CLI not available"
    else
        run_cmd graphify update . || {
            echo "    WARNING: initial graph build failed. You can rerun manually: graphify update ." >&2
        }
        if [[ -f "$PROJECT_ROOT/graphify-out/graph.json" ]]; then
            echo "    graph: graphify-out/graph.json"
        fi
        if [[ -f "$PROJECT_ROOT/graphify-out/GRAPH_REPORT.md" ]]; then
            echo "    report: graphify-out/GRAPH_REPORT.md"
        fi
    fi

    install_graphify_platforms

    echo "  - integration verify"
    validate_script="$SPINE_DIR/scripts/validate-graphify-integration.sh"
    if [[ -f "$validate_script" ]] && ! $DRY_RUN; then
        bash "$validate_script" --targets="$TARGETS" || echo "    WARNING: validate-graphify-integration.sh reported issues" >&2
    fi
fi
