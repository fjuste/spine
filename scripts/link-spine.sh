#!/usr/bin/env bash
set -uo pipefail

# =============================================================================
# Spine — Link consumer project to Spine repository
#
# Creates PROJECT_ROOT/.spine -> absolute path to the Spine repository.
# Run from a git project root, or pass --project-root explicitly.
#
# Usage:
#   bash scripts/link-spine.sh
#   bash scripts/link-spine.sh --spine-dir=/path/to/spine
#   bash scripts/link-spine.sh --project-root=/path/to/project --force
#   bash scripts/link-spine.sh --dry-run
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
            echo "Usage: bash scripts/link-spine.sh [OPTIONS]"
            echo ""
            echo "Creates .spine symlink in a consumer project pointing to the Spine repo."
            echo ""
            echo "Options:"
            echo "  --spine-dir=PATH     Spine repository root (default: parent of scripts/)"
            echo "  --project-root=PATH  Consumer project root (default: git toplevel from cwd)"
            echo "  --force              Replace existing .spine symlink if target differs"
            echo "  --dry-run            Preview without making changes"
            echo ""
            echo "Examples:"
            echo "  cd /path/to/my-project"
            echo "  bash ~/Workspace/ide/spine/scripts/link-spine.sh"
            echo "  bash ~/Workspace/ide/spine/scripts/link-spine.sh --force --dry-run"
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
SPINE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -n "$SPINE_DIR_CUSTOM" ]]; then
    SPINE_DIR="$(cd "$SPINE_DIR_CUSTOM" 2>/dev/null && pwd || echo "")"
    if [[ -z "$SPINE_DIR" ]]; then
        echo "ERROR: --spine-dir not found: $SPINE_DIR_CUSTOM" >&2
        exit 1
    fi
fi

if [[ ! -d "$SPINE_DIR/rules" || ! -d "$SPINE_DIR/skills" || ! -d "$SPINE_DIR/commands" ]]; then
    echo "ERROR: Cannot find rules/, skills/, or commands/ in $SPINE_DIR" >&2
    echo "       Make sure --spine-dir points to the Spine repository root." >&2
    exit 1
fi

SPINE_DIR="$(cd "$SPINE_DIR" && pwd)"

if [[ -n "$PROJECT_ROOT_CUSTOM" ]]; then
    PROJECT_ROOT="$(cd "$PROJECT_ROOT_CUSTOM" 2>/dev/null || echo "")"
    if [[ -z "$PROJECT_ROOT" ]]; then
        echo "ERROR: --project-root not found: $PROJECT_ROOT_CUSTOM" >&2
        exit 1
    fi
else
    PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [[ -z "$PROJECT_ROOT" ]]; then
        echo "ERROR: Not inside a git repository." >&2
        echo "       Run from your project root or pass --project-root=PATH." >&2
        exit 1
    fi
fi

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
SPINE_LINK="$PROJECT_ROOT/.spine"

log_linked()   { printf "  \033[32m+\033[0m %s\n" "$1"; }
log_skipped()  { printf "  \033[34m=\033[0m %s\n" "$1"; }
log_conflict() { printf "  \033[31m✗\033[0m %s\n" "$1"; }
log_warn()     { printf "  \033[33m!\033[0m %s\n" "$1"; }

echo "Spine Link"
echo "Spine repo: $SPINE_DIR"
echo "Project:    $PROJECT_ROOT"
$FORCE && echo "Mode:       force"
$DRY_RUN && echo "Mode:       dry-run"
echo ""

RESULT=0

if [[ -L "$SPINE_LINK" ]]; then
    current="$(readlink "$SPINE_LINK")"
    if [[ "$current" = /* ]]; then
        resolved="${current%/}"
    else
        resolved="$(cd "$PROJECT_ROOT" && cd "$(dirname "$current")" 2>/dev/null && pwd)/$(basename "$current")"
    fi

    if [[ "$resolved" == "$SPINE_DIR" ]]; then
        log_skipped ".spine symlink (already linked to $SPINE_DIR)"
    else
        if $FORCE; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would replace .spine symlink: $current -> $SPINE_DIR"
            else
                rm "$SPINE_LINK"
                ln -s "$SPINE_DIR" "$SPINE_LINK"
                log_warn ".spine (replaced: $current -> $SPINE_DIR)"
            fi
        else
            log_warn ".spine (points to $current, expected $SPINE_DIR)"
            echo "             Use --force to replace." >&2
            RESULT=2
        fi
    fi
elif [[ -d "$SPINE_LINK" ]]; then
    log_conflict ".spine"
    echo "             $SPINE_LINK is a real directory, not a symlink." >&2
    echo "             Remove it and re-run link-spine.sh." >&2
    RESULT=3
elif [[ -e "$SPINE_LINK" ]]; then
    log_conflict ".spine"
    echo "             $SPINE_LINK exists and is not a symlink." >&2
    echo "             Remove it and re-run link-spine.sh." >&2
    RESULT=3
else
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would link: $SPINE_LINK -> $SPINE_DIR"
    else
        ln -s "$SPINE_DIR" "$SPINE_LINK"
        log_linked ".spine -> $SPINE_DIR"
    fi
fi

echo ""
if [[ $RESULT -eq 0 ]]; then
    echo "Next step: bash .spine/install.sh"
    if $DRY_RUN; then
        echo ""
        echo "This was a dry run. No changes were made."
    fi
else
    exit "$RESULT"
fi
