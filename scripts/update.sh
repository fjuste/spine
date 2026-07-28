#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=false
NO_PULL=false
REPLACE_OPENCODE=false
WITH_GRAPHIFY=false
GRAPHIFY_INIT=false
WITH_MKDOCS=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --no-pull) NO_PULL=true ;;
        --replace-opencode) REPLACE_OPENCODE=true ;;
        --with-graphify) WITH_GRAPHIFY=true ;;
        --graphify-init) WITH_GRAPHIFY=true; GRAPHIFY_INIT=true ;;
        --with-mkdocs) WITH_MKDOCS=true ;;
        -h|--help)
            cat <<'EOF'
Usage: bash .spine/scripts/update.sh [OPTIONS]

Updates a consumer project that already uses Spine (symlink or rsync mode):
1) Pull latest Spine: git pull via symlink, or pull canonical + rsync .spine/
2) Reconcile project symlinks via install.sh --update --force
3) Sync opencode.json with current template (merge by default)
4) Preserve docs/ memory bank

Options:
  --dry-run            Preview actions without making changes
  --no-pull            Skip git pull / rsync step
  --replace-opencode   Replace opencode.json with template (default is merge)
  --with-graphify      Also run optional Graphify project setup
   --graphify-init      Also build initial graph (implies --with-graphify)
   --with-mkdocs        Also run MkDocs project setup
EOF
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$PROJECT_ROOT" ]]; then
    echo "ERROR: Not inside a git repository." >&2
    exit 1
fi

SPINE_PATH="$PROJECT_ROOT/.spine"

if [[ -L "$SPINE_PATH" ]]; then
    SPINE_MODE="symlink"
    SPINE_DIR="$(cd "$SPINE_PATH" && pwd)"
elif [[ -d "$SPINE_PATH" ]]; then
    SPINE_MODE="rsync"
    SPINE_DIR="$(cd "$SPINE_PATH" && pwd)"
else
    echo "ERROR: .spine not found in project root: $PROJECT_ROOT" >&2
    echo "Run: bash <path-to-spine>/scripts/link-spine.sh   (symlink mode)" >&2
    echo " or: bash <path-to-spine>/scripts/spine-init.sh   (rsync mode)" >&2
    exit 1
fi

INSTALL_SCRIPT="$SPINE_DIR/install.sh"
TEMPLATE_OPENCODE="$SPINE_DIR/templates/opencode.json"
PROJECT_OPENCODE="$PROJECT_ROOT/opencode.json"

if [[ ! -f "$INSTALL_SCRIPT" ]]; then
    echo "ERROR: install.sh not found via .spine: $INSTALL_SCRIPT" >&2
    exit 1
fi

if [[ ! -f "$TEMPLATE_OPENCODE" ]]; then
    echo "ERROR: templates/opencode.json not found: $TEMPLATE_OPENCODE" >&2
    exit 1
fi

# Resolve canonical path for rsync mode
CANONICAL_PATH=""
if [[ "$SPINE_MODE" == "rsync" ]]; then
    if [[ -f "$SPINE_PATH/.spine-canonical-source" ]]; then
        CANONICAL_PATH="$(head -1 "$SPINE_PATH/.spine-canonical-source")"
    elif [[ -n "${SPINE_CANONICAL_PATH:-}" ]]; then
        CANONICAL_PATH="$SPINE_CANONICAL_PATH"
    fi
    if [[ -z "$CANONICAL_PATH" || ! -d "$CANONICAL_PATH" ]]; then
        echo "ERROR: Cannot resolve canonical Spine path for rsync mode." >&2
        echo "       The canonical path was recorded in .spine/.spine-canonical-source" >&2
        echo "       or set SPINE_CANONICAL_PATH environment variable." >&2
        exit 1
    fi
fi

echo "Spine Project Updater"
echo "Project: $PROJECT_ROOT"
echo "Mode:    $SPINE_MODE"
echo "Spine:   $SPINE_DIR"
if [[ -n "$CANONICAL_PATH" ]]; then
    echo "Canonical: $CANONICAL_PATH"
fi
$DRY_RUN && echo "Mode:    dry-run"
echo ""

if ! $NO_PULL; then
    if [[ "$SPINE_MODE" == "symlink" ]]; then
        echo "Step 1/4: Update Spine repository (git pull via symlink)"
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would run: git -C \"$SPINE_DIR\" pull"
        else
            git -C "$SPINE_DIR" pull
        fi
    else
        echo "Step 1/4: Update canonical Spine + rsync .spine/"
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would run: git -C \"$CANONICAL_PATH\" pull"
            echo "  [DRY-RUN] Would run: rsync -a --delete \"$CANONICAL_PATH\"/ \"$SPINE_PATH\"/"
        else
            git -C "$CANONICAL_PATH" pull
            rsync -a --delete \
                --exclude='.git/' \
                --exclude='docs/' \
                --exclude='.cursor/' \
                --exclude='.claude/' \
                --exclude='.opencode/' \
                --exclude='.agents/' \
                --exclude='graphify-out/' \
                --exclude='node_modules/' \
                --exclude='.venv/' \
                --exclude='__pycache__/' \
                --exclude='.spine-vendor' \
                "$CANONICAL_PATH"/ "$SPINE_PATH"/
            if [[ -e "$SPINE_PATH/.git" ]]; then
                rm -rf "$SPINE_PATH/.git"
            fi
            echo "  Canonical: $CANONICAL_PATH"
        fi
    fi
else
    echo "Step 1/4: Skipped Spine pull (--no-pull)"
fi

echo ""
echo "Step 2/4: Reconcile project symlinks"
INSTALL_CMD=(bash "$INSTALL_SCRIPT" --update --force)
if $WITH_GRAPHIFY; then
    INSTALL_CMD+=(--with-graphify)
fi
if $GRAPHIFY_INIT; then
    INSTALL_CMD+=(--graphify-init)
fi
if $WITH_MKDOCS; then
    INSTALL_CMD+=(--with-mkdocs)
fi
if $DRY_RUN; then
    INSTALL_CMD+=(--dry-run)
fi
"${INSTALL_CMD[@]}"

echo ""
echo "Step 3/4: Sync opencode.json"
if $REPLACE_OPENCODE; then
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would replace: $PROJECT_OPENCODE"
    else
        cp "$TEMPLATE_OPENCODE" "$PROJECT_OPENCODE"
        echo "  Replaced with template: $PROJECT_OPENCODE"
    fi
else
    MERGE_SCRIPT="$SPINE_DIR/scripts/merge-opencode.py"
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would merge Spine instructions into: $PROJECT_OPENCODE"
    elif [[ ! -f "$MERGE_SCRIPT" ]]; then
        echo "  ERROR: merge helper not found: $MERGE_SCRIPT" >&2
        exit 1
    else
        output="$(python3 "$MERGE_SCRIPT" "$TEMPLATE_OPENCODE" "$PROJECT_OPENCODE")"
        echo "  $output"
    fi
fi

echo ""
echo "Step 4/4: Memory bank"
if [[ -d "$PROJECT_ROOT/docs/memory" ]]; then
    echo "  docs/memory/ present (install.sh seeds missing templates without overwriting)"
else
    echo "  Note: docs/memory/ still missing — run: bash .spine/install.sh --update"
fi

echo ""
echo "Update complete."
