#!/usr/bin/env bash
set -uo pipefail

# =============================================================================
# Spine — Vendor Mode Install (copy, no symlinks)
#
# Copies Spine into the consumer project as a real .spine/ directory and
# materializes IDE trees as real files so they can be committed and shared
# via git clone. Does not change the default symlink install path.
#
# Usage:
#   bash /path/to/spine/scripts/install-vendor.sh --spine-dir=/path/to/spine
#   bash /path/to/spine/scripts/install-vendor.sh --update --spine-dir=/path/to/spine
#   bash /path/to/spine/scripts/install-vendor.sh --force --spine-dir=/path/to/spine
#   bash .spine/scripts/install-vendor.sh --uninstall
# =============================================================================

FORCE=false
DRY_RUN=false
UPDATE_MODE=false
UNINSTALL_MODE=false
SPINE_DIR_CUSTOM=""
SKILLS_ARG=""
TARGETS="cursor,opencode,claude,antigravity"
PROJECT_ROOT_CUSTOM=""

VENDOR_GITIGNORE_ENTRIES=(
    ".spine"
    ".agents/"
    ".cursor/"
    ".claude/"
    ".opencode/"
)

CORE_SKILLS=(
    "writing-plans"
    "executing-plans"
    "test-driven-development"
    "systematic-debugging"
    "verification-before-completion"
)

COPIED=0
SKIPPED=0
WARNINGS=0
REMOVED=0

for arg in "$@"; do
    case "$arg" in
        --force)          FORCE=true ;;
        --dry-run)        DRY_RUN=true ;;
        --core)           SKILLS_ARG=core ;;
        --update)         UPDATE_MODE=true ;;
        --uninstall)      UNINSTALL_MODE=true ;;
        --spine-dir=*)    SPINE_DIR_CUSTOM="${arg#--spine-dir=}" ;;
        --skills=*)       SKILLS_ARG="${arg#--skills=}" ;;
        --targets=*)      TARGETS="${arg#--targets=}" ;;
        --project-root=*) PROJECT_ROOT_CUSTOM="${arg#--project-root=}" ;;
        -h|--help)
            echo "Usage: bash scripts/install-vendor.sh [OPTIONS]"
            echo ""
            echo "Vendor mode: copy Spine and IDE artifacts as real files (no symlinks)."
            echo "Commit the resulting trees so teammates get Spine via git clone."
            echo ""
            echo "Options:"
            echo "  --spine-dir=PATH     Spine source repository (required for install/update;"
            echo "                       optional with --force if .spine is already a symlink)"
            echo "  --update             Overwrite vendored trees from --spine-dir"
            echo "  --uninstall          Remove vendor marker, .spine/, and materialized IDE trees"
            echo "  --skills=core|all|a,b,c  Skill selection (default: all)"
            echo "  --core               Install core skills only (alias for --skills=core)"
            echo "  --targets=LIST       Comma-separated: cursor,opencode,claude,antigravity (default: all)"
            echo "  --project-root=PATH  Consumer project root (default: git toplevel)"
            echo "  --force              Convert from symlink install; replace conflicting links"
            echo "  --dry-run            Preview without making changes"
            echo ""
            echo "Symlink mode conflict:"
            echo "  If .spine is a symlink (or IDE paths are symlinks without .spine-vendor),"
            echo "  the script exits unless you pass --force to convert intentionally."
            echo ""
            echo "Examples:"
            echo "  bash ~/Workspace/ide/spine/scripts/install-vendor.sh --spine-dir=~/Workspace/ide/spine"
            echo "  bash .spine/scripts/install-vendor.sh --update --spine-dir=~/Workspace/ide/spine"
            echo "  bash ~/Workspace/ide/spine/scripts/install-vendor.sh --force --spine-dir=~/Workspace/ide/spine"
            echo "  bash .spine/scripts/install-vendor.sh --uninstall"
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
SCRIPT_SPINE_CANDIDATE="$(cd "$SCRIPT_DIR/.." && pwd)"

# Expand leading ~ in user-supplied paths (shell does not expand inside --flag=~/...).
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

log_ok()     { printf "  \033[32m+\033[0m %s\n" "$1"; }
log_skipped(){ printf "  \033[34m=\033[0m %s\n" "$1"; }
log_warn()   { printf "  \033[33m!\033[0m %s\n" "$1"; }
log_err()    { printf "  \033[31m✗\033[0m %s\n" "$1" >&2; }
log_info()   { printf "  \033[36mℹ\033[0m %s\n" "$1"; }

mkdir_p() {
    local dir="$1"
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would create directory: $dir"
    else
        mkdir -p "$dir"
    fi
}

is_spine_root() {
    local dir="$1"
    [[ -d "$dir/rules" && -d "$dir/skills" && -d "$dir/commands" ]]
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

get_core_rules() {
    echo "01-core-protocol.md
02-memory-bank.md
03-code-quality.md"
}

get_command_files() {
    local commands_dir="$1/commands"
    [[ -d "$commands_dir" ]] || return 0
    local command_file
    for command_file in "$commands_dir"/*.md; do
        [[ -f "$command_file" ]] && basename "$command_file"
    done | sort
}

get_agent_files() {
    local agents_dir="$1/agents"
    [[ -d "$agents_dir" ]] || return 0
    local agent_file
    for agent_file in "$agents_dir"/*.md; do
        [[ -f "$agent_file" ]] && basename "$agent_file"
    done | sort
}

get_available_skills() {
    local skills_dir="$1/skills"
    [[ -d "$skills_dir" ]] || return 0
    local skill_dir
    for skill_dir in "$skills_dir"/*/; do
        [[ -d "$skill_dir" ]] || continue
        basename "$skill_dir"
    done | sort
}

resolve_skills() {
    local source_root="$1"
    local skills_arg="$2"
    if [[ -z "$skills_arg" || "$skills_arg" == "all" ]]; then
        get_available_skills "$source_root"
    elif [[ "$skills_arg" == "core" ]]; then
        printf '%s\n' "${CORE_SKILLS[@]}"
    else
        echo "$skills_arg" | tr ',' '\n'
    fi
}

target_enabled() {
    local name="$1"
    [[ ",$TARGETS," == *",$name,"* ]]
}

get_docs_seed_paths() {
    cat <<'EOF'
memory/global/project-brief.md
memory/global/product-context.md
memory/global/domain-glossary.md
memory/global/system-patterns.md
memory/global/tech-context.md
memory/global/decision-log.md
memory/ledger/roadmap.md
memory/ledger/progress.md
memory/ledger/learnings.md
memory/active_tasks/_task-template.md
governance/skills-policy.md
governance/memory-tags-policy.md
governance/ice-scoring-guide.md
quality/guardrails.md
workflow/gitflow-operacional.md
workflow/ciclo-de-entrega.md
EOF
}

rsync_available() {
    command -v rsync >/dev/null 2>&1
}

copy_tree() {
    # copy_tree src dest [--delete]
    local src="$1"
    local dest="$2"
    local delete_flag="${3:-}"

    if [[ ! -e "$src" ]]; then
        log_warn "Source missing, skip: $src"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy: $src -> $dest ${delete_flag}"
        COPIED=$((COPIED + 1))
        return 0
    fi

    mkdir -p "$(dirname "$dest")"
    if rsync_available; then
        if [[ "$delete_flag" == "--delete" ]]; then
            rsync -a --delete "$src" "$dest"
        else
            rsync -a "$src" "$dest"
        fi
    else
        if [[ -d "$src" ]]; then
            mkdir -p "$dest"
            if [[ "$delete_flag" == "--delete" ]]; then
                rm -rf "$dest"
                mkdir -p "$dest"
            fi
            cp -a "$src"/. "$dest"/
        else
            cp -a "$src" "$dest"
        fi
    fi
    COPIED=$((COPIED + 1))
    return 0
}

copy_file() {
    local src="$1"
    local dest="$2"
    if [[ ! -f "$src" ]]; then
        log_warn "File missing, skip: $src"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy file: $dest"
        COPIED=$((COPIED + 1))
        return 0
    fi
    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
    COPIED=$((COPIED + 1))
    return 0
}

resolve_symlink_target() {
    local link_path="$1"
    local current resolved
    current="$(readlink "$link_path")"
    if [[ "$current" = /* ]]; then
        echo "${current%/}"
    else
        resolved="$(cd "$(dirname "$link_path")" && cd "$(dirname "$current")" 2>/dev/null && pwd)/$(basename "$current")"
        echo "$resolved"
    fi
}

has_symlink_ide_trees() {
    local project_root="$1"
    local path
    for path in \
        "$project_root/.cursor/skills" \
        "$project_root/.claude/skills" \
        "$project_root/.agents/skills"/* \
        "$project_root/.cursor/commands"/* \
        "$project_root/.cursor/rules"/* \
        "$project_root/.opencode/commands"/* \
        "$project_root/.opencode/agents"/*; do
        [[ -e "$path" || -L "$path" ]] || continue
        if [[ -L "$path" ]]; then
            return 0
        fi
    done
    return 1
}

remove_symlink_trees() {
    local project_root="$1"
    local path

    echo ""
    echo "Removing symlink-mode artefacts:"

    for path in \
        "$project_root/.agents/skills"/* \
        "$project_root/.cursor/rules"/* \
        "$project_root/.cursor/commands"/* \
        "$project_root/.opencode/commands"/* \
        "$project_root/.opencode/agents"/*; do
        [[ -L "$path" ]] || continue
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would remove symlink: ${path#"$project_root/"}"
        else
            rm "$path"
            log_ok "removed symlink: ${path#"$project_root/"}"
        fi
        REMOVED=$((REMOVED + 1))
    done

    for path in \
        "$project_root/.cursor/skills" \
        "$project_root/.claude/skills" \
        "$project_root/.spine"; do
        if [[ -L "$path" ]]; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove symlink: ${path#"$project_root/"}"
            else
                rm "$path"
                log_ok "removed symlink: ${path#"$project_root/"}"
            fi
            REMOVED=$((REMOVED + 1))
        fi
    done
}

detect_and_handle_symlink_mode() {
    local project_root="$1"
    local spine_path="$project_root/.spine"
    local marker="$project_root/.spine-vendor"
    local symlink_spine=false
    local symlink_ide=false

    if [[ -L "$spine_path" ]]; then
        symlink_spine=true
    fi
    if [[ ! -f "$marker" ]] && has_symlink_ide_trees "$project_root"; then
        symlink_ide=true
    fi

    if ! $symlink_spine && ! $symlink_ide; then
        return 0
    fi

    if ! $FORCE; then
        log_err "Symlink-mode Spine detected in $project_root"
        if $symlink_spine; then
            echo "       .spine is a symlink -> $(readlink "$spine_path")" >&2
        fi
        if $symlink_ide; then
            echo "       IDE paths contain symlinks and .spine-vendor is missing." >&2
        fi
        echo "       Vendor install refuses to mix modes." >&2
        echo "       Re-run with --force to convert to vendor mode (copies real files)." >&2
        echo "       Example:" >&2
        echo "         bash $SCRIPT_DIR/install-vendor.sh --force --spine-dir=/path/to/spine" >&2
        exit 3
    fi

    if $symlink_spine && [[ -z "$SPINE_DIR_CUSTOM" ]]; then
        SPINE_DIR_CUSTOM="$(resolve_symlink_target "$spine_path")"
        log_info "Using symlink target as --spine-dir: $SPINE_DIR_CUSTOM"
    fi

    remove_symlink_trees "$project_root"
}

resolve_source_spine_dir() {
    local project_root="$1"
    local dest_spine="$project_root/.spine"
    local source=""

    if [[ -n "$SPINE_DIR_CUSTOM" ]]; then
        if [[ ! -d "$SPINE_DIR_CUSTOM" ]]; then
            echo "ERROR: --spine-dir not found: $SPINE_DIR_CUSTOM" >&2
            exit 1
        fi
        source="$(cd "$SPINE_DIR_CUSTOM" && pwd)"
    elif $UPDATE_MODE; then
        echo "ERROR: --update requires --spine-dir=PATH (source must differ from vendored .spine)." >&2
        exit 1
    elif is_spine_root "$SCRIPT_SPINE_CANDIDATE"; then
        # Running from an upstream Spine clone (or from vendored .spine — guarded below).
        source="$SCRIPT_SPINE_CANDIDATE"
    else
        echo "ERROR: --spine-dir=PATH is required." >&2
        exit 1
    fi

    if ! is_spine_root "$source"; then
        echo "ERROR: Cannot find rules/, skills/, or commands/ in $source" >&2
        exit 1
    fi

    # Prevent update/install from using the destination tree as its own source.
    if [[ -d "$dest_spine" && ! -L "$dest_spine" ]]; then
        local dest_resolved source_resolved
        dest_resolved="$(cd "$dest_spine" && pwd)"
        source_resolved="$(cd "$source" && pwd)"
        if [[ "$dest_resolved" == "$source_resolved" ]]; then
            echo "ERROR: --spine-dir points at the project's vendored .spine ($dest_resolved)." >&2
            echo "       Pass the upstream Spine clone path, e.g. --spine-dir=~/Workspace/ide/spine" >&2
            exit 1
        fi
    fi

    echo "$source"
}

copy_spine_into_project() {
    local source="$1"
    local dest="$2"
    local delete_flag=""

    if $UPDATE_MODE || [[ -d "$dest" ]]; then
        delete_flag="--delete"
    fi

    echo ""
    echo "Vendoring Spine -> .spine/:"

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would rsync $source/ -> $dest/ (exclude .git, docs, IDE dirs, caches)"
        COPIED=$((COPIED + 1))
        return 0
    fi

    mkdir -p "$dest"

    if rsync_available; then
        local -a rsync_opts=(-a)
        [[ -n "$delete_flag" ]] && rsync_opts+=(--delete)
        rsync "${rsync_opts[@]}" \
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
            "$source"/ "$dest"/
    else
        log_warn "rsync not found; using cp (no --delete pruning of removed upstream files)"
        WARNINGS=$((WARNINGS + 1))
        # Best-effort: copy key trees
        local name
        for name in agents commands rules scripts skills templates tests install.sh AGENTS.md README.md; do
            if [[ -e "$source/$name" ]]; then
                if [[ -d "$source/$name" ]]; then
                    mkdir -p "$dest/$name"
                    cp -a "$source/$name"/. "$dest/$name"/
                else
                    cp -a "$source/$name" "$dest/$name"
                fi
            fi
        done
        # Ensure no nested git metadata was copied
        rm -rf "$dest/.git"
    fi

    # Safety: never leave a nested git repo inside the consumer project.
    if [[ -e "$dest/.git" ]]; then
        rm -rf "$dest/.git"
        log_ok "removed nested .git from .spine/"
    fi

    log_ok ".spine/ vendored from $source"
    COPIED=$((COPIED + 1))
}

materialize_skills() {
    local project_root="$1"
    local vendored_spine="$2"
    local skill_list="$3"
    local agents_skills="$project_root/.agents/skills"
    local skill

    echo ""
    echo "Skills (.agents/skills/ as real directories):"
    mkdir_p "$agents_skills"

    if $UPDATE_MODE && ! $DRY_RUN; then
        # Drop skills no longer selected
        if [[ -d "$agents_skills" ]]; then
            local existing
            for existing in "$agents_skills"/*/; do
                [[ -d "$existing" ]] || continue
                local name
                name="$(basename "$existing")"
                if ! printf '%s\n' "$skill_list" | grep -qxF "$name"; then
                    rm -rf "$existing"
                    log_ok "removed skill (not in selection): $name"
                    REMOVED=$((REMOVED + 1))
                fi
            done
        fi
    fi

    while IFS= read -r skill; do
        [[ -z "$skill" ]] && continue
        local src="$vendored_spine/skills/$skill"
        if [[ ! -d "$src" ]]; then
            log_warn "Skill '$skill' not found in vendored .spine, skipping"
            WARNINGS=$((WARNINGS + 1))
            continue
        fi
        local dest="$agents_skills/$skill"
        if rsync_available && ! $DRY_RUN; then
            mkdir -p "$dest"
            rsync -a --delete "$src"/ "$dest"/
            log_ok "skill: $skill"
            COPIED=$((COPIED + 1))
        else
            copy_tree "$src/" "$dest/" --delete
            log_ok "skill: $skill"
        fi
    done <<< "$skill_list"
}

materialize_cursor() {
    local project_root="$1"
    local vendored_spine="$2"
    local cursor_rules="$project_root/.cursor/rules"
    local cursor_commands="$project_root/.cursor/commands"
    local cursor_skills="$project_root/.cursor/skills"

    echo ""
    echo "=== Cursor (copied files) ==="
    mkdir_p "$cursor_rules"
    mkdir_p "$cursor_commands"

    local rule_file
    for rule_file in $(get_core_rules); do
        copy_file "$vendored_spine/rules/$rule_file" "$cursor_rules/$rule_file"
        log_ok "rule: $rule_file"
    done

    local command_file
    for command_file in $(get_command_files "$vendored_spine"); do
        copy_file "$vendored_spine/commands/$command_file" "$cursor_commands/$command_file"
        log_ok "command: $command_file"
    done

    echo ""
    echo "Skills hub (.cursor/skills/ copy of .agents/skills/):"
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy .agents/skills/ -> .cursor/skills/"
    else
        mkdir -p "$cursor_skills"
        if rsync_available; then
            rsync -a --delete "$project_root/.agents/skills"/ "$cursor_skills"/
        else
            rm -rf "$cursor_skills"
            mkdir -p "$cursor_skills"
            cp -a "$project_root/.agents/skills"/. "$cursor_skills"/
        fi
        log_ok ".cursor/skills/"
        COPIED=$((COPIED + 1))
    fi
}

materialize_claude() {
    local project_root="$1"
    local claude_skills="$project_root/.claude/skills"

    echo ""
    echo "=== Claude Code (copied files) ==="
    echo "Skills hub (.claude/skills/ copy of .agents/skills/):"
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy .agents/skills/ -> .claude/skills/"
    else
        mkdir -p "$claude_skills"
        if rsync_available; then
            rsync -a --delete "$project_root/.agents/skills"/ "$claude_skills"/
        else
            rm -rf "$claude_skills"
            mkdir -p "$claude_skills"
            cp -a "$project_root/.agents/skills"/. "$claude_skills"/
        fi
        log_ok ".claude/skills/"
        COPIED=$((COPIED + 1))
    fi
}

materialize_opencode() {
    local project_root="$1"
    local vendored_spine="$2"
    local oc_commands="$project_root/.opencode/commands"
    local oc_agents="$project_root/.opencode/agents"

    echo ""
    echo "=== OpenCode (copied files) ==="
    mkdir_p "$oc_commands"
    mkdir_p "$oc_agents"

    local command_file
    for command_file in $(get_command_files "$vendored_spine"); do
        copy_file "$vendored_spine/commands/$command_file" "$oc_commands/$command_file"
        log_ok "command: $command_file"
    done

    local agent_file
    for agent_file in $(get_agent_files "$vendored_spine"); do
        copy_file "$vendored_spine/agents/$agent_file" "$oc_agents/$agent_file"
        log_ok "agent: $agent_file"
    done
}

materialize_antigravity() {
    local project_root="$1"
    local vendored_spine="$2"
    local agents_rules="$project_root/.agents/rules"
    local agents_workflows="$project_root/.agents/workflows"
    local cursor_rules="$project_root/.cursor/rules"

    echo ""
    echo "=== Antigravity (copied files) ==="
    mkdir_p "$agents_rules"
    mkdir_p "$agents_workflows"

    local rule_file
    for rule_file in $(get_core_rules); do
        copy_file "$vendored_spine/rules/$rule_file" "$agents_rules/$rule_file"
        log_ok "agy-rule: $rule_file"
    done

    # Mirror project-local Cursor rules (graphify.mdc, ansible.mdc, …)
    if [[ -d "$cursor_rules" ]]; then
        local core_rules src name
        core_rules="$(get_core_rules)"
        for src in "$cursor_rules"/*; do
            [[ -f "$src" ]] || continue
            name="$(basename "$src")"
            if printf '%s\n' "$core_rules" | grep -qxF "$name"; then
                continue
            fi
            copy_file "$src" "$agents_rules/$name"
            log_ok "agy-rule (project): $name"
        done
    fi

    local command_file
    for command_file in $(get_command_files "$vendored_spine"); do
        copy_file "$vendored_spine/commands/$command_file" "$agents_workflows/$command_file"
        log_ok "agy-workflow: $command_file"
    done
}

seed_docs_templates() {
    local project_root="$1"
    local source_spine="$2"
    local templates_docs="$source_spine/templates/docs"
    local rel dest src
    local seeded=0 skipped=0 missing=0

    echo ""
    echo "Docs templates:"

    if [[ ! -d "$templates_docs" ]]; then
        log_warn "templates/docs/ not found in $source_spine"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi

    while IFS= read -r rel; do
        [[ -z "$rel" ]] && continue
        src="$templates_docs/$rel"
        dest="$project_root/docs/$rel"

        if [[ ! -f "$src" ]]; then
            log_warn "template missing: templates/docs/$rel"
            missing=$((missing + 1))
            continue
        fi

        if [[ -f "$dest" ]]; then
            log_skipped "docs/$rel (already exists, not overwriting)"
            skipped=$((skipped + 1))
            continue
        fi

        if $DRY_RUN; then
            echo "  [DRY-RUN] Would copy: docs/$rel"
            seeded=$((seeded + 1))
        else
            mkdir -p "$(dirname "$dest")"
            cp "$src" "$dest"
            log_ok "docs/$rel (seeded from templates/)"
            seeded=$((seeded + 1))
        fi
    done < <(get_docs_seed_paths)

    local dir gitkeep_path
    for dir in \
        "$project_root/docs/documentation" \
        "$project_root/docs/memory/active_tasks" \
        "$project_root/docs/memory/completed_tasks"; do
        mkdir_p "$dir"
    done

    for gitkeep_path in \
        "$project_root/docs/memory/active_tasks/.gitkeep" \
        "$project_root/docs/memory/completed_tasks/.gitkeep"; do
        if [[ -f "$gitkeep_path" ]]; then
            log_skipped "${gitkeep_path#"$project_root/"} (already exists)"
            continue
        fi
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would create: ${gitkeep_path#"$project_root/"}"
        else
            : > "$gitkeep_path"
            log_ok "${gitkeep_path#"$project_root/"} (created)"
        fi
    done

    echo ""
    echo "  Docs seed: $seeded copied, $skipped skipped (existing), $missing template gaps"
}

merge_or_copy_opencode() {
    local project_root="$1"
    local source_spine="$2"
    local template_opencode="$source_spine/templates/opencode.json"
    local project_opencode="$project_root/opencode.json"
    local merge_script="$source_spine/scripts/merge-opencode.py"

    echo ""
    echo "opencode.json:"

    if [[ ! -f "$template_opencode" ]]; then
        log_warn "templates/opencode.json not found in $source_spine"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi

    if [[ ! -f "$merge_script" ]]; then
        log_warn "merge helper not found: $merge_script"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi

    if $DRY_RUN; then
        if [[ -f "$project_opencode" ]]; then
            echo "  [DRY-RUN] Would merge Spine instructions into: opencode.json"
        else
            echo "  [DRY-RUN] Would create: opencode.json from template"
        fi
        return 0
    fi

    local output
    if output="$(python3 "$merge_script" "$template_opencode" "$project_opencode" 2>&1)"; then
        log_ok "opencode.json ($output)"
    else
        log_warn "opencode.json merge failed: $output"
        WARNINGS=$((WARNINGS + 1))
        return 1
    fi
}

adjust_gitignore_for_vendor() {
    local project_root="$1"
    local gitignore="$project_root/.gitignore"
    local entry
    local changed=0

    echo ""
    echo "Gitignore (vendor mode — trees are versioned):"

    if [[ ! -f "$gitignore" ]]; then
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would create .gitignore with vendor note (no Spine path ignores)"
        else
            cat > "$gitignore" <<'EOF'
# Spine vendor mode: .spine and IDE trees are versioned (do not ignore them)
EOF
            log_ok ".gitignore (created with vendor note)"
        fi
        return 0
    fi

    if $DRY_RUN; then
        for entry in "${VENDOR_GITIGNORE_ENTRIES[@]}"; do
            if grep -qxF "$entry" "$gitignore" 2>/dev/null; then
                echo "  [DRY-RUN] Would remove ignore entry: $entry"
                changed=$((changed + 1))
            fi
        done
        if ! grep -qF "Spine vendor mode" "$gitignore" 2>/dev/null; then
            echo "  [DRY-RUN] Would add vendor mode note to .gitignore"
        fi
        return 0
    fi

    local tmp
    tmp="$(mktemp)"
    # Drop exact Spine machine-specific ignore lines; keep everything else.
    while IFS= read -r line || [[ -n "$line" ]]; do
        local drop=false
        for entry in "${VENDOR_GITIGNORE_ENTRIES[@]}"; do
            if [[ "$line" == "$entry" ]]; then
                drop=true
                changed=$((changed + 1))
                log_ok "gitignore: removed ignore for $entry"
                break
            fi
        done
        $drop || printf '%s\n' "$line" >> "$tmp"
    done < "$gitignore"

    if ! grep -qF "Spine vendor mode" "$tmp" 2>/dev/null; then
        printf '\n# Spine vendor mode: trees are versioned (.spine, .agents, .cursor, .claude, .opencode)\n' >> "$tmp"
        log_ok "gitignore: added vendor mode note"
        changed=$((changed + 1))
    else
        log_skipped "gitignore: vendor mode note (already present)"
    fi

    mv "$tmp" "$gitignore"

    if [[ $changed -eq 0 ]]; then
        log_skipped "gitignore: no Spine path ignores to remove"
    fi
}

write_vendor_marker() {
    local project_root="$1"
    local source="$2"
    local marker="$project_root/.spine-vendor"
    local ts
    ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would write $marker"
        return 0
    fi

    cat > "$marker" <<EOF
mode=vendor
updated_at=$ts
source=$source
EOF
    log_ok ".spine-vendor (updated_at=$ts)"
}

uninstall_vendor() {
    local project_root="$1"

    echo "Spine Vendor Uninstaller"
    echo "Project: $project_root"
    echo ""

    if [[ -L "$project_root/.spine" ]]; then
        echo "ERROR: .spine is a symlink (symlink mode)." >&2
        echo "       Use: bash .spine/install.sh --uninstall" >&2
        exit 1
    fi

    local path
    for path in \
        "$project_root/.spine-vendor" \
        "$project_root/.spine" \
        "$project_root/.agents" \
        "$project_root/.cursor/rules" \
        "$project_root/.cursor/commands" \
        "$project_root/.cursor/skills" \
        "$project_root/.opencode/commands" \
        "$project_root/.opencode/agents" \
        "$project_root/.claude/skills"; do
        if [[ -e "$path" || -L "$path" ]]; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove: ${path#"$project_root/"}"
            else
                rm -rf "$path"
                log_ok "removed: ${path#"$project_root/"}"
            fi
            REMOVED=$((REMOVED + 1))
        fi
    done

    echo ""
    echo "Note: docs/ and opencode.json were NOT removed."
    echo "Done. Removed $REMOVED path(s)."
}

print_next_steps() {
    local project_root="$1"
    echo ""
    echo "==========================================="
    echo "  Vendor install complete"
    echo "==========================================="
    echo ""
    echo "  Copied : $COPIED"
    echo "  Skipped: $SKIPPED"
    echo "  Warns  : $WARNINGS"
    echo "  Removed: $REMOVED"
    echo ""
    echo "Next steps:"
    echo "  1. Review changes under:"
    echo "       .spine/ .agents/ .cursor/ .opencode/ .claude/ .spine-vendor"
    echo "  2. Commit and push so teammates get Spine via git clone / pull:"
    echo "       git add .spine .agents .cursor .opencode .claude .spine-vendor docs opencode.json .gitignore"
    echo "       git commit -m \"chore: vendor Spine into project\""
    echo "  3. Teammates: git pull (no symlink privilege or local Spine clone required for day-to-day use)."
    echo ""
    echo "Update later (maintainer with upstream Spine clone):"
    echo "  bash $project_root/.spine/scripts/install-vendor.sh --update --spine-dir=/path/to/spine"
    echo ""
    echo "Optional Graphify / MkDocs: use existing scripts under .spine/scripts/ after vendor install."
    if $DRY_RUN; then
        echo ""
        echo "This was a dry run. No changes were made."
    fi
}

# =============================================================================
# Main
# =============================================================================

PROJECT_ROOT="$(find_project_root)" || exit 1

echo "Spine Vendor Install"
echo "Project: $PROJECT_ROOT"
$FORCE && echo "Mode:   force"
$DRY_RUN && echo "Mode:   dry-run"
$UPDATE_MODE && echo "Mode:   update (overwrite)"
$UNINSTALL_MODE && echo "Mode:   uninstall"
echo ""

if $UNINSTALL_MODE; then
    uninstall_vendor "$PROJECT_ROOT"
    exit 0
fi

detect_and_handle_symlink_mode "$PROJECT_ROOT"

SOURCE_SPINE="$(resolve_source_spine_dir "$PROJECT_ROOT")" || exit 1
echo "Source: $SOURCE_SPINE"

if $UPDATE_MODE && [[ ! -f "$PROJECT_ROOT/.spine-vendor" ]] && [[ ! -d "$PROJECT_ROOT/.spine" ]]; then
    log_warn "No existing vendor install found; performing first-time vendor install."
    WARNINGS=$((WARNINGS + 1))
fi

DEST_SPINE="$PROJECT_ROOT/.spine"

copy_spine_into_project "$SOURCE_SPINE" "$DEST_SPINE"

# After copy, materialize from the vendored tree (stable relative layout).
VENDORED="$DEST_SPINE"
if $DRY_RUN; then
    VENDORED="$SOURCE_SPINE"
fi

SKILL_LIST="$(resolve_skills "$SOURCE_SPINE" "$SKILLS_ARG")"
materialize_skills "$PROJECT_ROOT" "$VENDORED" "$SKILL_LIST"

if target_enabled "cursor"; then
    materialize_cursor "$PROJECT_ROOT" "$VENDORED"
fi
if target_enabled "claude"; then
    materialize_claude "$PROJECT_ROOT"
fi
if target_enabled "opencode"; then
    materialize_opencode "$PROJECT_ROOT" "$VENDORED"
fi
if target_enabled "antigravity"; then
    materialize_antigravity "$PROJECT_ROOT" "$VENDORED"
fi

seed_docs_templates "$PROJECT_ROOT" "$SOURCE_SPINE"
merge_or_copy_opencode "$PROJECT_ROOT" "$SOURCE_SPINE"
adjust_gitignore_for_vendor "$PROJECT_ROOT"
write_vendor_marker "$PROJECT_ROOT" "$SOURCE_SPINE"

print_next_steps "$PROJECT_ROOT"
