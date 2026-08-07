#!/usr/bin/env bash
set -uo pipefail

# =============================================================================
# Spine — Rsync-mode Init (populate .spine as real directory via rsync)
#
# Populates PROJECT_ROOT/.spine as a real directory via rsync from a canonical
# Spine clone on the host. Then runs install.sh to create IDE tree relative
# symlinks (.cursor/, .agents/, .opencode/, .claude/).
#
# This is a third install mode (alongside symlink and vendor). It replaces the
# fragile absolute .spine symlink with a real directory while keeping IDE trees
# as lightweight relative symlinks that are versionable in git.
#
# Usage:
#   bash ~/Workspace/ide/spine/scripts/spine-init.sh
#   bash .spine/scripts/spine-init.sh --spine-dir=/path/to/spine
#   bash scripts/spine-init.sh --force --dry-run
#   bash scripts/spine-init.sh --project-root=/path/to/project
# =============================================================================

FORCE=false
DRY_RUN=false
SPINE_DIR_CUSTOM=""
PROJECT_ROOT_CUSTOM=""

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
        --spine-dir=*) SPINE_DIR_CUSTOM="${arg#--spine-dir=}" ;;
        --project-root=*) PROJECT_ROOT_CUSTOM="${arg#--project-root=}" ;;
        -h|--help)
            echo "Usage: bash scripts/spine-init.sh [OPTIONS]"
            echo ""
            echo "Populates .spine/ as a real directory via rsync from a canonical"
            echo "Spine clone, then runs install.sh for IDE tree relative symlinks."
            echo ""
            echo "Canonical path resolution (first match wins):"
            echo "  1. --spine-dir=PATH (explicit)"
            echo "  2. \$SPINE_CANONICAL_PATH environment variable"
            echo "  3. ~/Workspace/ide/spine (convention)"
            echo "  4. Auto-detect from script location (if run from a Spine clone with .git/)"
            echo ""
            echo "Options:"
            echo "  --spine-dir=PATH     Canonical Spine clone path (overrides auto-detection)"
            echo "  --project-root=PATH  Consumer project root (default: git toplevel from cwd)"
            echo "  --force              Replace existing .spine (symlink or directory)"
            echo "  --dry-run            Preview without making changes"
            echo ""
            echo "Examples:"
            echo "  cd /path/to/my-project"
            echo "  bash ~/Workspace/ide/spine/scripts/spine-init.sh"
            echo "  bash ~/Workspace/ide/spine/scripts/spine-init.sh --spine-dir=~/spine-v2"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Expand leading ~ in user-supplied paths.
expand_user_path() {
    local p="$1"
    if [[ "$p" == "~" ]]; then
        echo "$HOME"
    elif [[ "$p" == "~/"* ]]; then
        echo "$HOME/${p#~/}"
    else
        echo "$p"
    fi
}

if [[ -n "$SPINE_DIR_CUSTOM" ]]; then
    SPINE_DIR_CUSTOM="$(expand_user_path "$SPINE_DIR_CUSTOM")"
fi
if [[ -n "$PROJECT_ROOT_CUSTOM" ]]; then
    PROJECT_ROOT_CUSTOM="$(expand_user_path "$PROJECT_ROOT_CUSTOM")"
fi

is_spine_root() {
    local dir="$1"
    [[ -d "$dir/rules" && -d "$dir/skills" && -d "$dir/commands" ]]
}

resolve_canonical_spine() {
    # 1. Explicit flag
    if [[ -n "$SPINE_DIR_CUSTOM" ]]; then
        if [[ ! -d "$SPINE_DIR_CUSTOM" ]]; then
            echo "ERROR: --spine-dir not found: $SPINE_DIR_CUSTOM" >&2
            exit 1
        fi
        if ! is_spine_root "$SPINE_DIR_CUSTOM"; then
            echo "ERROR: --spine-dir is missing rules/, skills/, or commands/: $SPINE_DIR_CUSTOM" >&2
            exit 1
        fi
        echo "$(cd "$SPINE_DIR_CUSTOM" && pwd)"
        return 0
    fi

    # 2. Environment variable
    if [[ -n "${SPINE_CANONICAL_PATH:-}" ]] && [[ -d "$SPINE_CANONICAL_PATH" ]]; then
        if is_spine_root "$SPINE_CANONICAL_PATH"; then
            echo "$(cd "$SPINE_CANONICAL_PATH" && pwd)"
            return 0
        fi
    fi

    # 3. Convention: ~/Workspace/ide/spine
    if [[ -d "$HOME/Workspace/ide/spine" ]]; then
        local convention="$HOME/Workspace/ide/spine"
        if is_spine_root "$convention"; then
            echo "$(cd "$convention" && pwd)"
            return 0
        fi
    fi

    # 4. Auto-detect from script location (only if inside a git-tracked Spine clone)
    local parent
    parent="$(cd "$SCRIPT_DIR/.." && pwd)"
    if [[ -d "$parent/.git" ]] && is_spine_root "$parent"; then
        echo "$parent"
        return 0
    fi

    echo "ERROR: Cannot resolve canonical Spine path." >&2
    echo "" >&2
    echo "  The canonical Spine clone is where rsync will copy .spine/ from." >&2
    echo "  Resolve by one of:" >&2
    echo "    1. Pass --spine-dir=PATH" >&2
    echo "    2. export SPINE_CANONICAL_PATH=/path/to/spine" >&2
    echo "    3. Clone Spine to ~/Workspace/ide/spine" >&2
    echo "    4. Run this script from inside the Spine clone itself" >&2
    exit 1
}

find_project_root() {
    if [[ -n "$PROJECT_ROOT_CUSTOM" ]]; then
        if [[ ! -d "$PROJECT_ROOT_CUSTOM" ]]; then
            echo "ERROR: --project-root not found: $PROJECT_ROOT_CUSTOM" >&2
            return 1
        fi
        (cd "$PROJECT_ROOT_CUSTOM" && pwd)
        return 0
    fi
    local root
    root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -z "$root" ]]; then
        echo "ERROR: Not inside a git repository." >&2
        echo "       Run from your consumer project root or pass --project-root=PATH." >&2
        return 1
    fi
    echo "$root"
}

rsync_available() {
    command -v rsync >/dev/null 2>&1
}

log_ok()     { printf "  \033[32m+\033[0m %s\n" "$1"; }
log_warn()   { printf "  \033[33m!\033[0m %s\n" "$1"; }
log_info()   { printf "  \033[36mℹ\033[0m %s\n" "$1"; }
log_err()    { printf "  \033[31m✗\033[0m %s\n" "$1" >&2; }

# =============================================================================
# Main
# =============================================================================

CANONICAL="$(resolve_canonical_spine)" || exit 1
PROJECT_ROOT="$(find_project_root)" || exit 1

echo "Spine Rsync-Mode Init"
echo "Canonical: $CANONICAL"
echo "Project:   $PROJECT_ROOT"
$FORCE && echo "Mode:      force"
$DRY_RUN && echo "Mode:      dry-run"
echo ""

SPINE_PATH="$PROJECT_ROOT/.spine"

if [[ -L "$SPINE_PATH" ]]; then
    current="$(readlink "$SPINE_PATH")"
    if $FORCE; then
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would remove symlink: .spine -> $current"
        else
            rm "$SPINE_PATH"
            log_warn ".spine symlink removed (was: -> $current)"
        fi
    else
        log_err ".spine is a symlink (symlink mode)."
        echo "       Re-run with --force to replace with rsync mode directory." >&2
        echo "       Or use: bash .spine/scripts/update.sh  (keep symlink mode)" >&2
        exit 3
    fi
elif [[ -d "$SPINE_PATH" ]]; then
    if $FORCE; then
        log_info ".spine directory exists — will be overwritten by rsync (--force)."
    else
        log_err ".spine already exists as a real directory."
        echo "       Re-run with --force to replace (rsync will overwrite)." >&2
        echo "       Or use: bash .spine/scripts/update.sh  (if already rsync mode)" >&2
        exit 3
    fi
elif [[ -e "$SPINE_PATH" ]]; then
    log_err ".spine exists and is not a symlink or directory."
    echo "       Remove it and re-run." >&2
    exit 3
fi

if ! rsync_available; then
    log_err "rsync is not available. Install rsync to use rsync mode."
    exit 1
fi

echo ""
echo "Rsync .spine/ from canonical clone:"

if $DRY_RUN; then
    echo "  [DRY-RUN] Would rsync: $CANONICAL/ -> $SPINE_PATH/"
    echo "  [DRY-RUN] Would run: bash $SPINE_PATH/install.sh"
else
    rsync -a --delete \
        --exclude='.git/' \
        --exclude='/docs/' \
        --exclude='.cursor/' \
        --exclude='.claude/' \
        --exclude='.opencode/' \
        --exclude='.agents/' \
        --exclude='.spine' \
        --exclude='.spine/' \
        --exclude='graphify-out/' \
        --exclude='node_modules/' \
        --exclude='.venv/' \
        --exclude='__pycache__/' \
        --exclude='.spine-vendor' \
        "$CANONICAL"/ "$SPINE_PATH"/

    if [[ -e "$SPINE_PATH/.git" ]]; then
        rm -rf "$SPINE_PATH/.git"
    fi

    log_ok ".spine/ populated from $CANONICAL"

    # Record canonical source for update.sh
    echo "$CANONICAL" > "$SPINE_PATH/.spine-canonical-source"

    echo ""
    echo "Running install.sh to create IDE tree relative symlinks:"
    bash "$SPINE_PATH/install.sh"
fi

echo ""
echo "==========================================="
echo "  Rsync-mode init complete"
echo "==========================================="
echo ""
echo "  Canonical: $CANONICAL"
echo "  Project:   $PROJECT_ROOT"
echo ""
echo "Project structure:"
echo "  .spine/         (rsync mode — real directory)"
echo "  .agents/skills/    (relative symlinks -> .spine/skills/)"
echo "  .cursor/           (relative symlinks -> .spine/)"
echo "  .opencode/         (relative symlinks -> .spine/)"
echo "  .claude/           (relative symlinks -> .spine/)"
echo ""
echo "Update later:"
echo "  bash .spine/scripts/update.sh"
echo "  (pulls canonical clone, then rsyncs .spine/ + reconciles symlinks)"
echo ""
if $DRY_RUN; then
    echo "This was a dry run. No changes were made."
fi
