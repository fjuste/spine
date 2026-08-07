#!/usr/bin/env bash
set -uo pipefail

# =============================================================================
# Spine — Project Installation Script
#
# Installs per-project wiring using .agents/ as the cross-tool hub.
# Default: relative symlinks. With --copy: physical file copies (hybrid mode).
#
# Prerequisite: .spine symlink in the project root (use scripts/link-spine.sh).
# --copy requires .spine to be a symlink (not a vendored real directory).
#
# Usage:
#   bash .spine/install.sh                       # Install all skills (default, symlinks)
#   bash .spine/install.sh --copy                # Hybrid: physical copies, .spine stays symlink
#   bash .spine/install.sh --core                # Install core skills only (5)
#   bash .spine/install.sh --skills=core|a,b,c   # Explicit skill selection
#   bash .spine/install.sh --add-skill=x         # Add a skill to existing project
#   bash .spine/install.sh --remove-skill=x      # Remove a skill from project
#   bash .spine/install.sh --list-skills         # List available/installed skills
#   bash .spine/install.sh --update              # Update: install + cleanup dangling
#   bash .spine/install.sh --uninstall           # Remove applied artefacts (keeps .spine symlink)
#   bash .spine/install.sh --dry-run             # Preview without changes
# =============================================================================

# ---------------------------------------------------------------------------
# Parse Arguments
# ---------------------------------------------------------------------------

FORCE=false
DRY_RUN=false
UPDATE_MODE=false
UNINSTALL_MODE=false
COPY_MODE=false
SPINE_DIR_CUSTOM=""
SKILLS_ARG=""
ADD_SKILL=""
REMOVE_SKILL=""
LIST_SKILLS=false
TARGETS="cursor,opencode,claude,antigravity"
WITH_GRAPHIFY=false
GRAPHIFY_INIT=false
GRAPHIFY_HOOKS=false
GRAPHIFY_UNINSTALL=false
NO_GRAPHIFY_PROMPT=false
WITH_MKDOCS=false
MKDOCS_INIT=false
MKDOCS_UNINSTALL=false
NO_MKDOCS_PROMPT=false

for arg in "$@"; do
    case "$arg" in
        --force)          FORCE=true ;;
        --dry-run)        DRY_RUN=true ;;
        --core)           SKILLS_ARG=core ;;
        --update)         UPDATE_MODE=true ;;
        --uninstall)      UNINSTALL_MODE=true ;;
        --copy)           COPY_MODE=true ;;
        --global|--project)
            echo "ERROR: --global and --project were removed in v1.3.0." >&2
            echo "       Install is project-only. Run scripts/link-spine.sh first." >&2
            exit 1
            ;;
        --spine-dir=*)    SPINE_DIR_CUSTOM="${arg#--spine-dir=}" ;;
        --skills=*)       SKILLS_ARG="${arg#--skills=}" ;;
        --add-skill=*)    ADD_SKILL="${arg#--add-skill=}" ;;
        --remove-skill=*) REMOVE_SKILL="${arg#--remove-skill=}" ;;
        --list-skills)    LIST_SKILLS=true ;;
        --targets=*)      TARGETS="${arg#--targets=}" ;;
        --with-graphify)  WITH_GRAPHIFY=true; GRAPHIFY_INIT=true ;;
        --graphify-init)  WITH_GRAPHIFY=true; GRAPHIFY_INIT=true ;;
        --graphify-hooks) GRAPHIFY_HOOKS=true ;;
        --graphify-uninstall) GRAPHIFY_UNINSTALL=true ;;
        --no-graphify-prompt) NO_GRAPHIFY_PROMPT=true ;;
        --with-mkdocs)    WITH_MKDOCS=true; MKDOCS_INIT=true ;;
        --mkdocs-uninstall) MKDOCS_UNINSTALL=true ;;
        --no-mkdocs-prompt) NO_MKDOCS_PROMPT=true ;;
        -h|--help)
            echo "Usage: bash install.sh [OPTIONS]"
            echo ""
            echo "Prerequisite: .spine symlink in project root (scripts/link-spine.sh)."
            echo ""
            echo "Options:"
            echo "  --copy               Hybrid mode: copy rules/skills/commands into the project"
            echo "                       (.spine stays a gitignored symlink to the Spine repo)"
            echo "  --update             Install missing + cleanup dangling symlinks"
            echo "  --uninstall          Remove applied Spine artefacts (keeps .spine symlink)"
            echo "  --spine-dir=PATH     Path to Spine repository (default: auto-detect)"
            echo "  --skills=core|all|a,b,c  Skill selection (default: all)"
            echo "  --core               Install core skills only (alias for --skills=core)"
            echo "  --add-skill=NAME     Add a single skill to existing project"
            echo "  --remove-skill=NAME  Remove a single skill from project"
            echo "  --list-skills        List available and installed skills"
            echo "  --targets=LIST       Comma-separated: cursor,opencode,claude,antigravity"
            echo "  Graphify: enabled interactively at end of install when TTY (answer yes at prompt)"
            echo "  --with-graphify      Non-interactive: full Graphify co-install (CI/scripts; same as --graphify-init)"
            echo "  --graphify-init      Alias for --with-graphify (full tri-platform co-install)"
            echo "  --graphify-hooks     Also run graphify hook install (post-commit graph refresh)"
            echo "  --graphify-uninstall Remove Graphify platform artifacts (Cursor mdc, OpenCode plugin, Claude hook)"
            echo "  --no-graphify-prompt Skip interactive Graphify opt-in prompt (non-TTY skips automatically)"
            echo "  MkDocs: enabled interactively at end of install when TTY (answer yes at prompt)"
            echo "  --with-mkdocs        Non-interactive: full MkDocs setup (CI/scripts)"
            echo "  --mkdocs-uninstall   Remove MkDocs templates and config from project"
            echo "  --no-mkdocs-prompt   Skip interactive MkDocs opt-in prompt (non-TTY skips automatically)"
            echo "  --force              Replace mismatched symlinks / overwrite copy conflicts"
            echo "  --dry-run            Preview without making changes"
            echo ""
            echo "Examples:"
            echo "  bash .spine/install.sh"
            echo "  bash .spine/install.sh --copy"
            echo "  bash .spine/install.sh --copy --update"
            echo "  bash .spine/install.sh --core"
            echo "  bash .spine/install.sh --skills=python-patterns,fastapi-pro"
            echo "  bash .spine/install.sh --update"
            echo "  bash .spine/install.sh --list-skills"
            echo "  bash .spine/install.sh --add-skill=astro"
            echo "  bash .spine/install.sh --uninstall"
            echo "  bash .spine/install.sh --with-graphify   # non-interactive Graphify enable"
            echo "  bash .spine/install.sh --with-mkdocs     # non-interactive MkDocs enable"
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Run with --help for usage." >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve Spine Repository Root
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPINE_DIR="$(cd "$SCRIPT_DIR" && pwd)"

if [[ -n "$SPINE_DIR_CUSTOM" ]]; then
    SPINE_DIR="$(cd "$SPINE_DIR_CUSTOM" 2>/dev/null && pwd || echo "")"
    if [[ -z "$SPINE_DIR" ]]; then
        echo "ERROR: --spine-dir not found: $SPINE_DIR_CUSTOM" >&2
        exit 1
    fi
fi

if [[ ! -d "$SPINE_DIR/rules" || ! -d "$SPINE_DIR/skills" || ! -d "$SPINE_DIR/commands" ]]; then
    echo "ERROR: Cannot find rules/, skills/, or commands/ in $SPINE_DIR" >&2
    echo "       Make sure install.sh is inside the Spine repository root." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# OS Detection
# ---------------------------------------------------------------------------

detect_os() {
    local uname_out
    uname_out="$(uname -s)"
    case "$uname_out" in
        Linux*)
            if grep -qi "microsoft" /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        Darwin*)
            echo "macos"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

OS="$(detect_os)"

# ---------------------------------------------------------------------------
# Core Skills (base profile)
# ---------------------------------------------------------------------------

CORE_SKILLS=(
    "writing-plans"
    "executing-plans"
    "test-driven-development"
    "systematic-debugging"
    "verification-before-completion"
)

# ---------------------------------------------------------------------------
# Dynamic Discovery Functions
# ---------------------------------------------------------------------------

get_rule_files() {
    local rules_dir="$SPINE_DIR/rules"
    if [[ ! -d "$rules_dir" ]]; then
        return
    fi
    local rule_file
    for rule_file in "$rules_dir"/*.md; do
        [[ -f "$rule_file" ]] && basename "$rule_file"
    done | sort
}

get_command_files() {
    local commands_dir="$SPINE_DIR/commands"
    if [[ ! -d "$commands_dir" ]]; then
        return
    fi
    local command_file
    for command_file in "$commands_dir"/*.md; do
        [[ -f "$command_file" ]] && basename "$command_file"
    done | sort
}

# Core rules loaded by both OpenCode (via opencode.json) and Cursor (via symlinks).
# Non-core rules are loaded on-demand as skills.
get_core_rules() {
    echo "01-core-protocol.md
02-memory-bank.md
03-code-quality.md"
}

get_agent_files() {
    local agents_dir="$SPINE_DIR/agents"
    if [[ ! -d "$agents_dir" ]]; then
        return
    fi
    local agent_file
    for agent_file in "$agents_dir"/*.md; do
        [[ -f "$agent_file" ]] && basename "$agent_file"
    done | sort
}

# ---------------------------------------------------------------------------
# Gitignore entries for consumer projects
#
# Symlink mode (default): ignore machine-specific .spine and .agents/ hub;
#   IDE trees (.cursor/, .claude/, .opencode/) may be committed as relative symlinks.
# Copy/hybrid mode (--copy): ignore only .spine (symlink); version .agents/ + IDE
#   trees as real files.
# ---------------------------------------------------------------------------

PROJECT_GITIGNORE_ENTRIES=(
    ".spine"
)

PROJECT_GITIGNORE_REMOVE_ENTRIES=(
    ".cursor/"
    ".claude/"
    ".opencode/"
    ".agents/"
    ".spine-vendor"
)

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

LINKED=0
SKIPPED=0
CONFLICTS=0
WARNINGS=0
CLEANED=0
HEALTH_ISSUES=0

# ---------------------------------------------------------------------------
# Helper Functions (Shared)
# ---------------------------------------------------------------------------

log_linked()   { printf "  \033[32m+\033[0m %s\n" "$1"; }
log_skipped()  { printf "  \033[34m=\033[0m %s\n" "$1"; }
log_conflict() { printf "  \033[31m✗\033[0m %s\n" "$1"; }
log_warn()     { printf "  \033[33m!\033[0m %s\n" "$1"; }
log_info()    { printf "  \033[36mℹ\033[0m %s\n" "$1"; }

mkdir_p() {
    local dir="$1"
    if $DRY_RUN; then
        echo "  [DRY-RUN] Would create directory: $dir"
    else
        mkdir -p "$dir"
    fi
}

# create_relative_symlink rel_target link_path label
# For project mode. Creates symlinks with relative paths.
# Returns: 0=created, 1=skipped, 2=warning, 3=conflict
create_relative_symlink() {
    local rel_target="$1"
    local link_path="$2"
    local label="$3"

    local parent_dir
    parent_dir="$(dirname "$link_path")"
    mkdir_p "$parent_dir"

    if [[ -L "$link_path" ]]; then
        local current
        current="$(readlink "$link_path")"

        if [[ "$current" == "$rel_target" ]]; then
            log_skipped "$label (already linked)"
            return 1
        fi

        if $FORCE; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would replace: $link_path"
                echo "             $current -> $rel_target"
            else
                rm "$link_path"
                ln -s "$rel_target" "$link_path"
                log_warn "$label (replaced: $current -> $rel_target)"
            fi
            return 0
        else
            log_warn "$label (points to $current, expected $rel_target)"
            echo "             Use --force to replace." >&2
            return 2
        fi

    elif [[ -e "$link_path" ]]; then
        log_conflict "$label ($link_path exists and is not a symlink)"
        echo "             Remove it and re-run install.sh." >&2
        return 3
    else
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would link: $link_path -> $rel_target"
        else
            ln -s "$rel_target" "$link_path"
            log_linked "$label"
        fi
        return 0
    fi
}

tally() {
    local rc=$1
    case $rc in
        0) LINKED=$((LINKED + 1)) ;;
        1) SKIPPED=$((SKIPPED + 1)) ;;
        2) WARNINGS=$((WARNINGS + 1)) ;;
        3) CONFLICTS=$((CONFLICTS + 1)) ;;
    esac
}

rsync_available() {
    command -v rsync >/dev/null 2>&1
}

# copy_tree_into src_dir dest_dir — rsync/cp directory contents (dest becomes real dir)
copy_tree_into() {
    local src="$1"
    local dest="$2"

    if [[ ! -d "$src" ]]; then
        log_warn "Source missing, skip: $src"
        WARNINGS=$((WARNINGS + 1))
        return 2
    fi

    if [[ -L "$dest" ]]; then
        if $FORCE || $COPY_MODE; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would replace symlink with copy: $dest"
            else
                rm "$dest"
            fi
        else
            log_conflict "$(basename "$dest") ($dest is a symlink; use --force or --copy)"
            return 3
        fi
    fi

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy tree: $src -> $dest"
        return 0
    fi

    mkdir -p "$dest"
    if rsync_available; then
        rsync -a --delete "$src"/ "$dest"/
    else
        # Best-effort without rsync --delete semantics for extras
        cp -a "$src"/. "$dest"/
    fi
    return 0
}

# copy_file_into src dest — physical file copy (replaces symlink at dest)
copy_file_into() {
    local src="$1"
    local dest="$2"
    local label="${3:-$(basename "$dest")}"

    if [[ ! -f "$src" ]]; then
        log_warn "File missing, skip: $src"
        WARNINGS=$((WARNINGS + 1))
        return 2
    fi

    if [[ -L "$dest" ]]; then
        if $FORCE || $COPY_MODE; then
            if ! $DRY_RUN; then rm "$dest"; fi
        else
            log_conflict "$label ($dest is a symlink; use --force or --copy)"
            return 3
        fi
    elif [[ -e "$dest" ]] && ! $FORCE && ! $UPDATE_MODE && ! $COPY_MODE; then
        log_skipped "$label (already exists)"
        return 1
    fi

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would copy file: $dest"
        return 0
    fi

    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
    log_linked "$label (copied)"
    return 0
}

# ---------------------------------------------------------------------------
# Ensure Executable Permissions
# ---------------------------------------------------------------------------

chmod_scripts() {
    local count=0

    if [[ -f "$SPINE_DIR/install.sh" ]]; then
        if ! $DRY_RUN; then chmod +x "$SPINE_DIR/install.sh"; fi
        count=$((count + 1))
    fi

    local script
    for script in "$SPINE_DIR"/scripts/*.sh; do
        if [[ -f "$script" ]]; then
            if ! $DRY_RUN; then chmod +x "$script"; fi
            count=$((count + 1))
        fi
    done

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would chmod +x on $count script(s)"
    else
        printf "  \033[32m+\033[0m chmod +x on %d script(s)\n" "$count"
    fi
}

# ===========================================================================
# PROJECT INSTALL: Per-project symlinks with granular skill selection
# ===========================================================================

# --- Find project root (git worktree) ---

find_project_root() {
    local root
    root="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [[ -z "$root" ]]; then
        echo "ERROR: Not inside a git repository." >&2
        echo "       Run from your consumer project root (git repo)." >&2
        return 1
    fi
    echo "$root"
}

# --- Require .spine path (symlink via link-spine.sh; --copy requires symlink) ---

require_spine_path() {
    local project_root="$1"
    local spine_path="$project_root/.spine"

    if [[ -L "$spine_path" ]]; then
        if [[ ! -d "$spine_path" ]]; then
            echo "ERROR: .spine symlink target is not a directory in $project_root" >&2
            echo "Run: bash $SPINE_DIR/scripts/link-spine.sh  (symlink mode)" >&2
            exit 1
        fi
    elif [[ -d "$spine_path" ]]; then
        if $COPY_MODE; then
            echo "ERROR: --copy requires .spine to be a symlink (not a real directory)." >&2
            echo "       Remove vendored .spine and run: bash $SPINE_DIR/scripts/link-spine.sh" >&2
            echo "       For a fully vendored tree use: bash $SPINE_DIR/scripts/install-vendor.sh" >&2
            exit 1
        fi
        :  # Real directory (rsync/vendor mode) — OK for symlink install path
    else
        echo "ERROR: .spine not found in $project_root" >&2
        echo "Run: bash $SPINE_DIR/scripts/link-spine.sh  (symlink mode)" >&2
        echo " or: bash $SPINE_DIR/scripts/spine-init.sh   (rsync mode)" >&2
        exit 1
    fi

    if [[ ! -d "$spine_path/rules" || ! -d "$spine_path/skills" || ! -d "$spine_path/commands" ]]; then
        echo "ERROR: .spine is missing rules/, skills/, or commands/" >&2
        exit 1
    fi
}

# --- Get available skills from Spine repo ---

get_available_skills() {
    local skills_dir="$SPINE_DIR/skills"
    if [[ ! -d "$skills_dir" ]]; then
        return
    fi
    local skill_dir
    for skill_dir in "$skills_dir"/*/; do
        if [[ -f "$skill_dir/SKILL.md" ]]; then
            basename "$skill_dir"
        fi
    done | sort
}

# --- Get currently installed skills in project ---

get_installed_skills() {
    local project_root="$1"
    local agents_skills="$project_root/.agents/skills"
    if [[ ! -d "$agents_skills" ]]; then
        return
    fi
    local entry
    for entry in "$agents_skills"/*; do
        if [[ -L "$entry" ]] || [[ -d "$entry" ]]; then
            basename "$entry"
        fi
    done | sort
}

# --- Resolve skill list from argument ---

resolve_skills() {
    local skills_arg="$1"
    if [[ -z "$skills_arg" || "$skills_arg" == "all" ]]; then
        get_available_skills
    elif [[ "$skills_arg" == "core" ]]; then
        printf '%s\n' "${CORE_SKILLS[@]}"
    else
        echo "$skills_arg" | tr ',' '\n'
    fi
}

# --- Install skills in .agents/skills/ (symlinks or copies) ---

install_project_skills() {
    local project_root="$1"
    local skill_list="$2"
    local agents_skills="$project_root/.agents/skills"

    mkdir_p "$agents_skills"

    if $COPY_MODE; then
        echo ""
        echo "Skills (physical copies in .agents/skills/):"

        if $UPDATE_MODE && ! $DRY_RUN && [[ -d "$agents_skills" ]]; then
            local existing name
            for existing in "$agents_skills"/*/; do
                [[ -d "$existing" ]] || continue
                name="$(basename "$existing")"
                if ! printf '%s\n' "$skill_list" | grep -qxF "$name"; then
                    rm -rf "$existing"
                    log_linked "removed skill (not in selection): $name"
                    CLEANED=$((CLEANED + 1))
                fi
            done
        fi
    else
        echo ""
        echo "Skills (per-skill symlinks in .agents/skills/):"
    fi

    local skill
    while IFS= read -r skill; do
        [[ -z "$skill" ]] && continue

        local source_dir="$SPINE_DIR/skills/$skill"
        if [[ ! -d "$source_dir" ]]; then
            log_warn "Skill '$skill' not found in Spine repo, skipping"
            WARNINGS=$((WARNINGS + 1))
            continue
        fi

        local dest_path="$agents_skills/$skill"
        if $COPY_MODE; then
            if copy_tree_into "$source_dir" "$dest_path"; then
                log_linked "skill: $skill (copied)"
                LINKED=$((LINKED + 1))
            else
                WARNINGS=$((WARNINGS + 1))
            fi
        else
            local rel_target="../../.spine/skills/$skill"
            create_relative_symlink "$rel_target" "$dest_path" "skill: $skill"
            tally $?
        fi
    done <<< "$skill_list"
}

# --- Install Cursor rules, commands, and skills ---

install_project_cursor() {
    local project_root="$1"
    local cursor_rules="$project_root/.cursor/rules"
    local cursor_commands="$project_root/.cursor/commands"
    local cursor_skills="$project_root/.cursor/skills"

    echo ""
    echo "=== Cursor (project-level) ==="

    mkdir_p "$cursor_rules"
    mkdir_p "$cursor_commands"

    echo ""
    if $COPY_MODE; then
        echo "Rules (physical copies):"
    else
        echo "Rules (per-file symlinks):"
    fi
    local rule_file
    for rule_file in $(get_core_rules); do
        local source_abs="$SPINE_DIR/rules/$rule_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Rule '$rule_file' not found, skipping"
            continue
        fi
        local dest_path="$cursor_rules/$rule_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "rule: $rule_file"
            tally $?
        else
            local rel_target="../../.spine/rules/$rule_file"
            create_relative_symlink "$rel_target" "$dest_path" "rule: $rule_file"
            tally $?
        fi
    done

    echo ""
    if $COPY_MODE; then
        echo "Commands (physical copies):"
    else
        echo "Commands (per-file symlinks):"
    fi
    local command_file
    for command_file in $(get_command_files); do
        local source_abs="$SPINE_DIR/commands/$command_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Command '$command_file' not found, skipping"
            continue
        fi
        local dest_path="$cursor_commands/$command_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "command: $command_file"
            tally $?
        else
            local rel_target="../../.spine/commands/$command_file"
            create_relative_symlink "$rel_target" "$dest_path" "command: $command_file"
            tally $?
        fi
    done

    echo ""
    if $COPY_MODE; then
        echo "Skills hub (.cursor/skills/ copy of .agents/skills/):"
        copy_tree_into "$project_root/.agents/skills" "$cursor_skills"
        tally $?
        log_linked ".cursor/skills/ (copied)"
    else
        echo "Skills (symlink to .agents/skills/):"
        create_relative_symlink "../.agents/skills" "$cursor_skills" "skills"
        tally $?
    fi
}

# --- Install Claude Code skills ---

install_project_claude() {
    local project_root="$1"
    local claude_skills="$project_root/.claude/skills"

    echo ""
    echo "=== Claude Code (project-level) ==="

    echo ""
    if $COPY_MODE; then
        echo "Skills hub (.claude/skills/ copy of .agents/skills/):"
        copy_tree_into "$project_root/.agents/skills" "$claude_skills"
        tally $?
        log_linked ".claude/skills/ (copied)"
    else
        echo "Skills (symlink to .agents/skills/):"
        create_relative_symlink "../.agents/skills" "$claude_skills" "skills"
        tally $?
    fi
}

# --- Warn if legacy global OpenCode agent symlinks exist ---

warn_if_global_opencode_agents() {
    local global_agents="${HOME}/.config/opencode/agents"
    if [[ ! -d "$global_agents" ]]; then
        return 0
    fi

    local link name target warned=0
    for link in "$global_agents"/*.md; do
        [[ -e "$link" ]] || continue
        [[ -L "$link" ]] || continue
        name="$(basename "$link")"
        target="$(readlink "$link")"
        if [[ "$target" == *"/spine/agents/"* ]] || [[ "$target" == *".spine/agents/"* ]]; then
            log_warn "Global OpenCode agent symlink: ~/.config/opencode/agents/$name"
            log_warn "Spine agents are project-only. Remove: rm ~/.config/opencode/agents/$name"
            log_warn "Use per-project .opencode/agents/ (installed by this script) instead."
            warned=$((warned + 1))
        fi
    done

    if [[ $warned -gt 0 ]]; then
        WARNINGS=$((WARNINGS + warned))
    fi
}

# --- Install OpenCode commands and agents (project-level only) ---

install_project_opencode() {
    local project_root="$1"
    local oc_commands="$project_root/.opencode/commands"
    local oc_agents="$project_root/.opencode/agents"

    echo ""
    echo "=== OpenCode (project-level) ==="

    warn_if_global_opencode_agents

    mkdir_p "$oc_commands"
    mkdir_p "$oc_agents"

    echo ""
    if $COPY_MODE; then
        echo "Commands (physical copies):"
    else
        echo "Commands (per-file symlinks):"
    fi
    local command_file
    for command_file in $(get_command_files); do
        local source_abs="$SPINE_DIR/commands/$command_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Command '$command_file' not found, skipping"
            continue
        fi
        local dest_path="$oc_commands/$command_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "command: $command_file"
            tally $?
        else
            local rel_target="../../.spine/commands/$command_file"
            create_relative_symlink "$rel_target" "$dest_path" "command: $command_file"
            tally $?
        fi
    done

    echo ""
    if $COPY_MODE; then
        echo "Agents (physical copies):"
    else
        echo "Agents (per-file symlinks):"
    fi
    local agent_file
    for agent_file in $(get_agent_files); do
        local source_abs="$SPINE_DIR/agents/$agent_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Agent '$agent_file' not found, skipping"
            continue
        fi
        local dest_path="$oc_agents/$agent_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "agent: $agent_file"
            tally $?
        else
            local rel_target="../../.spine/agents/$agent_file"
            create_relative_symlink "$rel_target" "$dest_path" "agent: $agent_file"
            tally $?
        fi
    done
}

# --- Install Antigravity rules + workflows under .agents/ ---

# Mirror project-local Cursor rules (e.g. graphify.mdc, ansible.mdc) into .agents/rules/
sync_project_rules_to_antigravity() {
    local project_root="$1"
    local cursor_rules="$project_root/.cursor/rules"
    local agents_rules="$project_root/.agents/rules"
    local core_rules
    core_rules="$(get_core_rules)"

    if [[ ! -d "$cursor_rules" ]]; then
        return 0
    fi

    mkdir_p "$agents_rules"

    echo ""
    echo "Project-local rules (mirror .cursor/rules extras -> .agents/rules/):"
    local src name mirrored=0
    for src in "$cursor_rules"/*; do
        [[ -f "$src" ]] || continue
        name="$(basename "$src")"
        # Skip Spine core rules (already installed from .spine/rules)
        if printf '%s\n' "$core_rules" | grep -qxF "$name"; then
            continue
        fi
        if $COPY_MODE || [[ ! -L "$agents_rules/$name" ]]; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would mirror: $name"
            else
                cp -a "$src" "$agents_rules/$name"
                log_linked "agy-rule (project): $name"
            fi
            mirrored=$((mirrored + 1))
            LINKED=$((LINKED + 1))
        else
            # Symlink mode: link to the cursor file so both stay in sync
            local rel_target="../../.cursor/rules/$name"
            create_relative_symlink "$rel_target" "$agents_rules/$name" "agy-rule (project): $name"
            tally $?
            mirrored=$((mirrored + 1))
        fi
    done
    if [[ $mirrored -eq 0 ]]; then
        log_skipped "no extra project rules to mirror"
    fi
}

install_project_antigravity() {
    local project_root="$1"
    local agents_rules="$project_root/.agents/rules"
    local agents_workflows="$project_root/.agents/workflows"

    echo ""
    echo "=== Antigravity (project-level) ==="

    mkdir_p "$agents_rules"
    mkdir_p "$agents_workflows"

    echo ""
    if $COPY_MODE; then
        echo "Rules (physical copies in .agents/rules/):"
    else
        echo "Rules (per-file symlinks in .agents/rules/):"
    fi
    local rule_file
    for rule_file in $(get_core_rules); do
        local source_abs="$SPINE_DIR/rules/$rule_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Rule '$rule_file' not found, skipping"
            continue
        fi
        local dest_path="$agents_rules/$rule_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "agy-rule: $rule_file"
            tally $?
        else
            local rel_target="../../.spine/rules/$rule_file"
            create_relative_symlink "$rel_target" "$dest_path" "agy-rule: $rule_file"
            tally $?
        fi
    done

    # graphify.mdc, ansible.mdc, and other project-local Cursor rules
    sync_project_rules_to_antigravity "$project_root"

    echo ""
    if $COPY_MODE; then
        echo "Workflows (physical copies in .agents/workflows/ from commands/):"
    else
        echo "Workflows (per-file symlinks in .agents/workflows/ -> commands/):"
    fi
    local command_file
    for command_file in $(get_command_files); do
        local source_abs="$SPINE_DIR/commands/$command_file"
        if [[ ! -f "$source_abs" ]]; then
            log_warn "Command '$command_file' not found, skipping"
            continue
        fi
        local dest_path="$agents_workflows/$command_file"
        if $COPY_MODE; then
            copy_file_into "$source_abs" "$dest_path" "agy-workflow: $command_file"
            tally $?
        else
            local rel_target="../../.spine/commands/$command_file"
            create_relative_symlink "$rel_target" "$dest_path" "agy-workflow: $command_file"
            tally $?
        fi
    done
}

# --- Add gitignore entries for consumer project ---

add_gitignore_entries() {
    local project_root="$1"
    local gitignore="$project_root/.gitignore"

    echo ""
    echo "Gitignore:"

    # Mode-specific entries
    local -a entries_to_add=(".spine")
    local -a entries_to_remove=(".cursor/" ".claude/" ".opencode/" ".spine-vendor")
    if $COPY_MODE; then
        # Hybrid: version .agents/ as real files; only .spine (symlink) is local
        entries_to_remove+=(".agents/" ".agents")
    else
        # Symlink hub: .agents/ is machine-local per-skill links
        entries_to_add+=(".agents/")
    fi

    if [[ ! -f "$gitignore" ]]; then
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would create .gitignore with Spine entries"
        else
            printf "# Spine: .spine is local (symlink); applied IDE trees may be committed\n" > "$gitignore"
            local entry
            for entry in "${entries_to_add[@]}"; do
                printf "%s\n" "$entry" >> "$gitignore"
            done
            log_linked ".gitignore (created with Spine entries)"
        fi
        return 0
    fi

    local remove_entry removed=0
    local tmp=""
    local needs_strip=false
    for remove_entry in "${entries_to_remove[@]}"; do
        if grep -qxF "$remove_entry" "$gitignore" 2>/dev/null; then
            needs_strip=true
            break
        fi
    done
    if $needs_strip; then
        if $DRY_RUN; then
            for remove_entry in "${entries_to_remove[@]}"; do
                if grep -qxF "$remove_entry" "$gitignore" 2>/dev/null; then
                    echo "  [DRY-RUN] Would remove ignore entry: $remove_entry"
                    removed=$((removed + 1))
                fi
            done
        else
            tmp="$(mktemp)"
            while IFS= read -r line || [[ -n "$line" ]]; do
                local drop=false
                for remove_entry in "${entries_to_remove[@]}"; do
                    if [[ "$line" == "$remove_entry" ]]; then
                        drop=true
                        removed=$((removed + 1))
                        log_linked ".gitignore: -$remove_entry (versionable in this install mode)"
                        break
                    fi
                done
                $drop || printf '%s\n' "$line" >> "$tmp"
            done < "$gitignore"
            mv "$tmp" "$gitignore"
        fi
    fi

    local entry added=0
    for entry in "${entries_to_add[@]}"; do
        if ! grep -qxF "$entry" "$gitignore" 2>/dev/null; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would add '$entry' to .gitignore"
            else
                echo "$entry" >> "$gitignore"
                log_linked ".gitignore: +$entry"
            fi
            added=$((added + 1))
        else
            log_skipped ".gitignore: $entry (already present)"
        fi
    done

    if [[ $added -gt 0 || $removed -gt 0 ]] && ! $DRY_RUN; then
        log_info "$added gitignore entries added, $removed obsolete ignores removed"
    fi
}

# --- List available and installed skills ---

list_skills() {
    local project_root
    project_root="$(find_project_root)" || exit 1

    echo ""
    echo "==========================================="
    echo "  Spine Skills"
    echo "==========================================="
    echo ""
    echo "Spine repo: $SPINE_DIR"
    echo "Project:    $project_root"
    echo ""

    echo "Core skills (minimal profile with --core):"
    local core
    for core in "${CORE_SKILLS[@]}"; do
        local marker=" "
        if [[ -L "$project_root/.agents/skills/$core" ]] || [[ -d "$project_root/.agents/skills/$core" ]]; then
            marker="✓"
        fi
        echo "  [$marker] $core"
    done

    echo ""
    echo "Available skills in Spine repo:"
    local available
    available="$(get_available_skills)"
    if [[ -z "$available" ]]; then
        echo "  (none found)"
    else
        echo "$available" | while read -r skill; do
            local marker=" "
            if [[ -L "$project_root/.agents/skills/$skill" ]] || [[ -d "$project_root/.agents/skills/$skill" ]]; then
                marker="✓"
            fi
            echo "  [$marker] $skill"
        done
    fi

    echo ""
    echo "==========================================="
}

# --- Add a single skill ---

add_skill() {
    local project_root="$1"
    local skill_name="$2"
    local source_dir="$SPINE_DIR/skills/$skill_name"

    if [[ ! -d "$source_dir" ]]; then
        echo "ERROR: Skill '$skill_name' not found in $SPINE_DIR/skills/" >&2
        echo "Available skills:" >&2
        get_available_skills >&2
        exit 1
    fi

    local agents_skills="$project_root/.agents/skills"
    local dest_path="$agents_skills/$skill_name"

    mkdir_p "$agents_skills"

    local rc=0
    if $COPY_MODE || [[ -d "$dest_path" && ! -L "$dest_path" ]]; then
        copy_tree_into "$source_dir" "$dest_path"
        rc=$?
        log_linked "skill: $skill_name (copied)"
        # Mirror into IDE hubs when present as real trees
        if [[ -d "$project_root/.cursor/skills" && ! -L "$project_root/.cursor/skills" ]]; then
            copy_tree_into "$source_dir" "$project_root/.cursor/skills/$skill_name"
        fi
        if [[ -d "$project_root/.claude/skills" && ! -L "$project_root/.claude/skills" ]]; then
            copy_tree_into "$source_dir" "$project_root/.claude/skills/$skill_name"
        fi
    else
        local rel_target="../../.spine/skills/$skill_name"
        create_relative_symlink "$rel_target" "$dest_path" "skill: $skill_name"
        rc=$?
    fi

    echo ""
    echo "Skill '$skill_name' installed in .agents/skills/"
    echo "Restart your agent to pick up the new skill."
    return $rc
}

# --- Remove a single skill ---

remove_skill() {
    local project_root="$1"
    local skill_name="$2"
    local dest_path="$project_root/.agents/skills/$skill_name"

    if [[ ! -e "$dest_path" && ! -L "$dest_path" ]]; then
        echo "WARNING: '$skill_name' not found in .agents/skills/" >&2
        return 1
    fi

    if $DRY_RUN; then
        echo "  [DRY-RUN] Would remove: $dest_path"
    else
        rm -rf "$dest_path"
        log_linked "skill: $skill_name (removed)"
        # Also remove mirrored copies in IDE hubs when they are real trees
        if [[ -d "$project_root/.cursor/skills/$skill_name" && ! -L "$project_root/.cursor/skills" ]]; then
            rm -rf "$project_root/.cursor/skills/$skill_name"
        fi
        if [[ -d "$project_root/.claude/skills/$skill_name" && ! -L "$project_root/.claude/skills" ]]; then
            rm -rf "$project_root/.claude/skills/$skill_name"
        fi
    fi
    return 0
}

# --- Cleanup dangling symlinks in a directory ---
# Scans a directory for symlinks that point to nonexistent targets.
# Arguments: directory_path category_name
# Returns: number of dangling symlinks cleaned.

cleanup_dangling_in_dir() {
    local dir_path="$1"
    local category="$2"
    local count=0

    if [[ ! -d "$dir_path" ]]; then
        return 0
    fi

    local link target
    for link in "$dir_path"/*; do
        [[ -L "$link" ]] || continue
        target="$(readlink "$link")"
        if [[ "$target" = /* ]]; then
            if [[ ! -e "$target" ]]; then
                if $DRY_RUN; then
                    echo "  [DRY-RUN] Would remove dangling: $category/$(basename "$link")"
                else
                    rm "$link"
                    log_linked "removed dangling: $category/$(basename "$link")"
                fi
                count=$((count + 1))
            fi
        else
            local parent_dir
            parent_dir="$(dirname "$link")"
            if [[ ! -e "$parent_dir/$target" ]]; then
                if $DRY_RUN; then
                    echo "  [DRY-RUN] Would remove dangling: $category/$(basename "$link")"
                else
                    rm "$link"
                    log_linked "removed dangling: $category/$(basename "$link")"
                fi
                count=$((count + 1))
            fi
        fi
    done

    echo "$count"
}

# --- Cleanup rule symlinks that are not in the core allowlist ---
# Removes symlinks in a rules directory for rules that are no longer core.
# Arguments: directory_path
# Returns: number of obsolete rule symlinks removed.

cleanup_obsolete_rules() {
    local dir_path="$1"
    local count=0

    if [[ ! -d "$dir_path" ]]; then
        return 0
    fi

    local core_rules
    core_rules="$(get_core_rules)"

    local link rule_name
    for link in "$dir_path"/*; do
        [[ -L "$link" ]] || continue
        rule_name="$(basename "$link")"
        if ! echo "$core_rules" | grep -qxF "$rule_name"; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove obsolete rule: $rule_name"
            else
                rm "$link"
                log_linked "removed obsolete rule: $rule_name"
            fi
            count=$((count + 1))
        fi
    done

    echo "$count"
}

# --- Cleanup all dangling symlinks in project ---

cleanup_dangling_symlinks() {
    local project_root="$1"
    local total=0
    local sub

    echo ""
    echo "Cleanup (dangling symlinks):"

    sub="$(cleanup_dangling_in_dir "$project_root/.agents/skills" "skills")"
    total=$((total + sub))

    sub="$(cleanup_dangling_in_dir "$project_root/.cursor/rules" "cursor/rules")"
    total=$((total + sub))

    sub="$(cleanup_obsolete_rules "$project_root/.cursor/rules")"
    total=$((total + sub))

    sub="$(cleanup_dangling_in_dir "$project_root/.cursor/commands" "cursor/commands")"
    total=$((total + sub))

    sub="$(cleanup_dangling_in_dir "$project_root/.opencode/commands" "opencode/commands")"
    total=$((total + sub))

    sub="$(cleanup_dangling_in_dir "$project_root/.opencode/agents" "opencode/agents")"
    total=$((total + sub))

    CLEANED=$total

    if [[ $total -eq 0 ]]; then
        log_skipped "No dangling symlinks found"
    else
        log_info "$total dangling symlink(s) removed"
    fi
}

# --- Validate health of project symlinks ---

validate_health() {
    local project_root="$1"
    local issues=0

    echo ""
    echo "Health check:"

    if [[ -L "$project_root/.spine" ]]; then
        local spine_target
        spine_target="$(readlink "$project_root/.spine")"
        if [[ ! -d "$project_root/.spine" ]]; then
            log_warn ".spine symlink points to nonexistent: $spine_target"
            issues=$((issues + 1))
        elif [[ ! -d "$project_root/.spine/rules" || ! -d "$project_root/.spine/skills" ]]; then
            log_warn ".spine target is missing rules/ or skills/"
            issues=$((issues + 1))
        else
            log_skipped ".spine symlink OK"
        fi
    elif [[ -d "$project_root/.spine" ]]; then
        if [[ ! -d "$project_root/.spine/rules" || ! -d "$project_root/.spine/skills" ]]; then
            log_warn ".spine (rsync mode) is missing rules/ or skills/"
            issues=$((issues + 1))
        else
            log_skipped ".spine (rsync mode) OK"
        fi
    else
        log_warn ".spine is missing"
        issues=$((issues + 1))
    fi

    local check_dirs=(
        "$project_root/.agents/skills"
        "$project_root/.cursor/rules"
        "$project_root/.cursor/commands"
        "$project_root/.opencode/commands"
        "$project_root/.opencode/agents"
    )
    if [[ -d "$project_root/.agents/rules" ]] || $COPY_MODE; then
        check_dirs+=("$project_root/.agents/rules" "$project_root/.agents/workflows")
    fi
    local dir label
    for dir in "${check_dirs[@]}"; do
        label="$(basename "$(dirname "$dir")")/$(basename "$dir")"
        if [[ ! -d "$dir" ]]; then
            if $COPY_MODE || [[ "$label" == agents/rules || "$label" == agents/workflows ]]; then
                log_warn "$label directory is missing"
                issues=$((issues + 1))
            fi
            continue
        fi
        if $COPY_MODE; then
            local count
            count="$(find "$dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')"
            if [[ "$count" -eq 0 ]]; then
                log_warn "$label is empty"
                issues=$((issues + 1))
            else
                log_skipped "$label: $count item(s) OK (copy mode)"
            fi
            continue
        fi
        local link target broken=0 total_links=0
        for link in "$dir"/*; do
            [[ -L "$link" ]] || continue
            total_links=$((total_links + 1))
            target="$(readlink "$link")"
            if [[ "$target" = /* ]]; then
                [[ -e "$target" ]] || { broken=$((broken + 1)); }
            else
                local parent
                parent="$(dirname "$link")"
                [[ -e "$parent/$target" ]] || { broken=$((broken + 1)); }
            fi
        done
        if [[ $broken -gt 0 ]]; then
            log_warn "$label: $broken broken symlink(s) out of $total_links"
            issues=$((issues + 1))
        else
            log_skipped "$label: $total_links symlink(s) OK"
        fi
    done

    local dir_symlinks=(
        "$project_root/.cursor/skills"
        "$project_root/.claude/skills"
    )
    local s s_target
    for s in "${dir_symlinks[@]}"; do
        label="$(basename "$(dirname "$s")")/$(basename "$s")"
        if $COPY_MODE; then
            if [[ -d "$s" && ! -L "$s" ]]; then
                log_skipped "$label OK (copy mode directory)"
            elif [[ -L "$s" && -d "$s" ]]; then
                log_skipped "$label OK (symlink)"
            else
                log_warn "$label missing (expected copy directory in --copy mode)"
                issues=$((issues + 1))
            fi
            continue
        fi
        if [[ ! -L "$s" ]]; then
            log_warn "$label is not a symlink"
            issues=$((issues + 1))
        elif [[ ! -d "$s" ]]; then
            s_target="$(readlink "$s")"
            log_warn "$label points to nonexistent: $s_target"
            issues=$((issues + 1))
        else
            log_skipped "$label OK"
        fi
    done

    HEALTH_ISSUES=$issues

    if [[ $issues -eq 0 ]]; then
        if $COPY_MODE; then
            printf "\n  \033[32m✓\033[0m All copy-mode trees are healthy\n"
        else
            printf "\n  \033[32m✓\033[0m All symlinks are healthy\n"
        fi
    else
        printf "\n  \033[33m⚠\033[0m %d issue(s) found\n" "$issues"
    fi
}

# --- Seed docs/ templates from Spine templates/docs/ (idempotent) ---

get_docs_seed_paths() {
    # active_tasks/: only _task-template.md — no sample numbered tasks
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

seed_docs_templates() {
    local project_root="$1"
    local templates_docs="$SPINE_DIR/templates/docs"
    local rel dest src

    echo ""
    echo "Docs templates:"

    if [[ ! -d "$templates_docs" ]]; then
        log_warn "templates/docs/ not found in $SPINE_DIR"
        return 1
    fi

    local seeded=0 skipped=0 missing=0

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
            log_linked "docs/$rel (seeded from templates/)"
            seeded=$((seeded + 1))
        fi
    done < <(get_docs_seed_paths)

    local dir gitkeep_path
    for dir in \
        "$project_root/docs/documentation" \
        "$project_root/docs/memory/active_tasks" \
        "$project_root/docs/memory/completed_tasks"; do
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would ensure directory: ${dir#"$project_root/"}"
        else
            mkdir -p "$dir"
        fi
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
            log_linked "${gitkeep_path#"$project_root/"} (created)"
        fi
    done

    echo ""
    echo "  Docs seed: $seeded copied, $skipped skipped (existing), $missing template gaps"
}

# --- Merge or create opencode.json from Spine template ---

merge_or_copy_opencode() {
    local project_root="$1"
    local template_opencode="$SPINE_DIR/templates/opencode.json"
    local project_opencode="$project_root/opencode.json"
    local merge_script="$SPINE_DIR/scripts/merge-opencode.py"

    echo ""
    echo "opencode.json:"

    if [[ ! -f "$template_opencode" ]]; then
        log_warn "templates/opencode.json not found in $SPINE_DIR"
        return 1
    fi

    if [[ ! -f "$merge_script" ]]; then
        log_warn "merge helper not found: $merge_script"
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
        log_linked "opencode.json ($output)"
    else
        log_warn "opencode.json merge failed: $output"
        return 1
    fi
}

# --- Optional Graphify setup for consumer projects ---

should_prompt_graphify() {
    $NO_GRAPHIFY_PROMPT && return 1
    $UNINSTALL_MODE && return 1
    $LIST_SKILLS && return 1
    [[ -n "$ADD_SKILL" || -n "$REMOVE_SKILL" ]] && return 1
    $DRY_RUN && return 1
    $WITH_GRAPHIFY && return 1
    [[ ! -t 0 ]] && return 1
    return 0
}

graphify_integration_complete() {
    local project_root="$1"
    local validate="$SPINE_DIR/scripts/validate-graphify-integration.sh"

    if [[ ! -f "$validate" ]]; then
        return 1
    fi

    (cd "$project_root" && bash "$validate" --targets="$TARGETS" >/dev/null 2>&1)
}

install_graphify_cli_if_needed() {
    if command -v graphify >/dev/null 2>&1; then
        return 0
    fi

    echo ""
    echo "Graphify CLI not found. Attempting install via uv..."
    if command -v uv >/dev/null 2>&1; then
        if uv tool install graphifyy; then
            echo "Graphify CLI installed."
            return 0
        fi
        echo "WARNING: uv tool install graphifyy failed." >&2
    else
        echo "WARNING: uv not found. Install Graphify manually:" >&2
        echo "  uv tool install graphifyy" >&2
        echo "  # alternatives: pipx install graphifyy | pip install graphifyy" >&2
    fi
    return 1
}

prompt_graphify_opt_in() {
    local project_root="$1"
    local prompt_title="Optional: Graphify"
    local prompt_question="Enable Graphify for this project? [Y/n]: "
    local graph_exists=false

    if ! should_prompt_graphify; then
        return 0
    fi

    if graphify_integration_complete "$project_root"; then
        echo ""
        echo "Graphify: integration complete (graph + Cursor/OpenCode/Claude). Skipping opt-in prompt."
        return 0
    fi

    if [[ -f "$project_root/graphify-out/graph.json" ]]; then
        graph_exists=true
        prompt_title="Complete Graphify integration?"
        prompt_question="Complete Graphify integration for this project? [Y/n]: "
    fi

    echo ""
    echo "==========================================="
    echo "  $prompt_title"
    echo "==========================================="
    echo ""
    if $graph_exists; then
        echo "Graphify graph exists but tri-platform integration is incomplete"
        echo "(Cursor mdc, OpenCode plugin, or Claude hook missing)."
        echo ""
    fi
    echo "Graphify is an optional code-structure layer (Spine owns docs/memory; Graphify maps source)."
    echo "Enabling runs graphify update . and installs:"
    echo "  - Cursor: .cursor/rules/graphify.mdc"
    echo "  - OpenCode: plugin + opencode.json registration"
    echo "  - Claude Code: CLAUDE.md section + PreToolUse hook"
    echo ""
    echo "Recommended for:"
    echo "  - medium/large codebases with many modules or services"
    echo "  - projects where broad file scanning increases token cost"
    echo ""
    echo "Usually skip for:"
    echo "  - small repos, docs-only trees, or greenfield prototypes"
    echo "  - when you prefer direct file reads only"
    echo ""
    echo "The memory bank (docs/memory/) remains the operational source of truth."
    echo ""

    local response=""
    while true; do
        read -r -p "$prompt_question" response
        response="$(printf '%s' "$response" | tr '[:upper:]' '[:lower:]')"
        case "$response" in
            y|yes|"")
                WITH_GRAPHIFY=true
                GRAPHIFY_INIT=true
                install_graphify_cli_if_needed || true
                echo ""
                echo "Graphify: enabled (graph build + tri-platform co-install for $TARGETS)"
                break
                ;;
            n|no)
                echo ""
                echo "Graphify: skipped. Re-run and press Enter to enable, or use:"
                echo "  bash .spine/install.sh --with-graphify"
                break
                ;;
            *)
                echo "Please answer y or n."
                ;;
        esac
    done
}

setup_project_graphify() {
    local project_root="$1"

    echo ""
    echo "Graphify (optional):"

    local helper="$SPINE_DIR/scripts/install-graphify.sh"
    if [[ ! -f "$helper" ]]; then
        log_warn "Graphify helper script not found: $helper"
        return 1
    fi

    local cmd=(bash "$helper" "--project-root=$project_root" "--targets=$TARGETS")
    if $GRAPHIFY_INIT; then
        cmd+=("--init-graph")
    fi
    if $GRAPHIFY_HOOKS; then
        cmd+=("--graphify-hooks")
    fi
    if $GRAPHIFY_UNINSTALL; then
        cmd+=("--uninstall")
    fi
    if $DRY_RUN; then
        cmd+=("--dry-run")
    fi

    "${cmd[@]}"
}

# --- MkDocs optional integration ---

should_prompt_mkdocs() {
    $NO_MKDOCS_PROMPT && return 1
    $UNINSTALL_MODE && return 1
    $LIST_SKILLS && return 1
    [[ -n "$ADD_SKILL" || -n "$REMOVE_SKILL" ]] && return 1
    $DRY_RUN && return 1
    $WITH_MKDOCS && return 1
    [[ ! -t 0 ]] && return 1
    return 0
}

mkdocs_integration_complete() {
    local project_root="$1"
    local validate="$SPINE_DIR/scripts/validate-mkdocs-integration.sh"

    if [[ ! -f "$validate" ]]; then
        return 1
    fi

    (cd "$project_root" && bash "$validate" >/dev/null 2>&1)
}

prompt_mkdocs_opt_in() {
    local project_root="$1"
    local prompt_title="Optional: MkDocs"
    local prompt_question="Enable MkDocs for this project? [Y/n]: "

    if ! should_prompt_mkdocs; then
        return 0
    fi

    if mkdocs_integration_complete "$project_root"; then
        echo ""
        echo "MkDocs: integration complete (config + build). Skipping opt-in prompt."
        return 0
    fi

    echo ""
    echo "==========================================="
    echo "  $prompt_title"
    echo "==========================================="
    echo ""
    echo "MkDocs generates a static documentation site from Markdown in docs/mkdocs/."
    echo "Enabling seeds docs/mkdocs/mkdocs.yml, docs/mkdocs/index.md, and runs an initial build."
    echo ""
    echo "Recommended for:"
    echo "  - projects with public APIs or libraries consumed by other teams"
    echo "  - projects where onboarding documentation is valuable"
    echo "  - teams practicing documentation-driven development"
    echo ""
    echo "Usually skip for:"
    echo "  - internal microservices with no external consumers"
    echo "  - small prototypes or scripts"
    echo "  - when the memory bank (docs/memory/) is sufficient"
    echo ""
    echo "The memory bank (docs/memory/) remains the operational source of truth."
    echo "MkDocs is the public-facing layer for humans reading the project."
    echo ""

    local response=""
    while true; do
        read -r -p "$prompt_question" response
        response="$(printf '%s' "$response" | tr '[:upper:]' '[:lower:]')"
        case "$response" in
            y|yes|"")
                WITH_MKDOCS=true
                MKDOCS_INIT=true
                echo ""
                echo "MkDocs: enabled (template seed + initial build)"
                break
                ;;
            n|no)
                echo ""
                echo "MkDocs: skipped. Re-run and press Enter to enable, or use:"
                echo "  bash .spine/install.sh --with-mkdocs"
                break
                ;;
            *)
                echo "Please answer y or n."
                ;;
        esac
    done
}

setup_project_mkdocs() {
    local project_root="$1"

    echo ""
    echo "MkDocs (optional):"

    local helper="$SPINE_DIR/scripts/install-mkdocs.sh"
    if [[ ! -f "$helper" ]]; then
        log_warn "MkDocs helper script not found: $helper"
        return 1
    fi

    local cmd=(bash "$helper" "--project-root=$project_root")
    if $MKDOCS_INIT; then
        cmd+=("--init-mkdocs")
    fi
    if $MKDOCS_UNINSTALL; then
        cmd+=("--uninstall")
    fi
    if $DRY_RUN; then
        cmd+=("--dry-run")
    fi

    "${cmd[@]}"
}

# --- Uninstall all Spine artefacts from project ---

uninstall_project() {
    local project_root="$1"

    echo "Spine Project Uninstaller"
    echo "Repository: $SPINE_DIR"
    echo "Project:    $project_root"
    echo ""

    local removed=0

    remove_symlink_or_dir() {
        local path="$1"
        local label="$2"
        if [[ -L "$path" ]]; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove symlink: $label"
            else
                rm "$path"
                log_linked "removed: $label"
            fi
            removed=$((removed + 1))
        elif [[ -d "$path" ]]; then
            local is_empty
            is_empty="$(find "$path" -maxdepth 1 -not -name '.' -not -name '..' | head -1)"
            if [[ -z "$is_empty" ]]; then
                if $DRY_RUN; then
                    echo "  [DRY-RUN] Would remove empty directory: $label"
                else
                    rmdir "$path"
                    log_linked "removed: $label (empty dir)"
                fi
                removed=$((removed + 1))
            else
                log_warn "$label (directory not empty, skipping)"
            fi
        fi
    }

    echo "Removing per-file symlinks and copied artefacts:"

    local dirs_to_clean=(
        "$project_root/.agents/skills"
        "$project_root/.agents/rules"
        "$project_root/.agents/workflows"
        "$project_root/.cursor/rules"
        "$project_root/.cursor/commands"
        "$project_root/.opencode/commands"
        "$project_root/.opencode/agents"
    )

    local d f
    for d in "${dirs_to_clean[@]}"; do
        if [[ -d "$d" ]]; then
            for f in "$d"/*; do
                [[ -e "$f" || -L "$f" ]] || continue
                if [[ -L "$f" ]]; then
                    if $DRY_RUN; then
                        echo "  [DRY-RUN] Would remove: $(basename "$d")/$(basename "$f")"
                    else
                        rm "$f"
                        log_linked "removed: $(basename "$d")/$(basename "$f")"
                    fi
                    removed=$((removed + 1))
                elif [[ -f "$f" ]] || [[ -d "$f" ]]; then
                    # Physical copies from --copy / vendor materialize
                    if $DRY_RUN; then
                        echo "  [DRY-RUN] Would remove copy: $(basename "$d")/$(basename "$f")"
                    else
                        rm -rf "$f"
                        log_linked "removed copy: $(basename "$d")/$(basename "$f")"
                    fi
                    removed=$((removed + 1))
                fi
            done
        fi
    done

    echo ""
    echo "Removing directory hubs:"

    # Skills hubs may be symlink or real copy tree
    for d in \
        "$project_root/.cursor/skills" \
        "$project_root/.claude/skills" \
        "$project_root/.agents/skills" \
        "$project_root/.agents/rules" \
        "$project_root/.agents/workflows"; do
        if [[ -L "$d" ]]; then
            remove_symlink_or_dir "$d" "${d#"$project_root/"}"
        elif [[ -d "$d" ]]; then
            if $DRY_RUN; then
                echo "  [DRY-RUN] Would remove directory: ${d#"$project_root/"}"
            else
                rm -rf "$d"
                log_linked "removed: ${d#"$project_root/"}"
            fi
            removed=$((removed + 1))
        fi
    done

    echo ""
    echo "Removing empty Spine parent directories:"

    for d in \
        "$project_root/.cursor/rules" \
        "$project_root/.cursor/commands" \
        "$project_root/.opencode/commands" \
        "$project_root/.opencode/agents" \
        "$project_root/.agents"; do
        if [[ -d "$d" ]]; then
            remove_symlink_or_dir "$d" "${d#"$project_root/"}"
        fi
    done

    remove_symlink_or_dir "$project_root/.cursor" ".cursor"
    remove_symlink_or_dir "$project_root/.claude" ".claude"
    remove_symlink_or_dir "$project_root/.opencode" ".opencode"
    remove_symlink_or_dir "$project_root/.agents" ".agents"

    echo ""
    echo "Handling .spine:"
    if [[ -L "$project_root/.spine" ]]; then
        log_skipped ".spine (symlink kept — re-run link-spine.sh only if needed)"
    elif [[ -d "$project_root/.spine" ]]; then
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would remove directory: .spine (rsync/vendor mode)"
            removed=$((removed + 1))
        else
            rm -rf "$project_root/.spine"
            log_linked "removed: .spine (rsync/vendor mode)"
            removed=$((removed + 1))
        fi
    else
        log_skipped ".spine (not present)"
    fi

    if [[ -f "$project_root/.spine-vendor" ]]; then
        if $DRY_RUN; then
            echo "  [DRY-RUN] Would remove: .spine-vendor"
        else
            rm -f "$project_root/.spine-vendor"
            log_linked "removed: .spine-vendor"
        fi
        removed=$((removed + 1))
    fi

    echo ""
    echo "==========================================="
    echo "  Spine Project Uninstall Summary"
    echo "==========================================="
    echo ""
    if $DRY_RUN; then
        echo "  (dry-run preview, no changes made)"
    else
        echo "  Removed: $removed artefact(s)"
    fi
    echo ""
    echo "  Note: opencode.json was NOT removed."
    echo "  Remove it manually if no longer needed."
    echo ""
    echo "==========================================="
}

# --- Project install summary ---

print_project_summary() {
    local project_root="$1"
    local skills_installed
    skills_installed="$(get_installed_skills "$project_root" | wc -l)"
    skills_installed="$(echo "$skills_installed" | tr -d ' ')"

    echo ""
    echo "==========================================="
    echo "  Spine Project Install Summary"
    echo "==========================================="
    echo ""
    echo "Detected OS: $OS"
    echo "Spine repo : $SPINE_DIR"
    echo "Project    : $project_root"
    echo "Targets    : $TARGETS"
    echo "Skills     : $skills_installed installed"
    echo ""
    echo "  Linked   : $LINKED"
    echo "  Skipped  : $SKIPPED (already correct)"
    echo "  Cleaned  : $CLEANED (dangling symlinks removed)"
    echo "  Conflicts: $CONFLICTS"
    echo "  Warnings : $WARNINGS"
    echo ""

    if [[ $CONFLICTS -gt 0 ]]; then
        printf "\033[33m⚠ %d conflict(s) detected.\033[0m\n" "$CONFLICTS"
        echo "  Use --force to replace conflicting targets."
        echo ""
    fi

    if [[ $WARNINGS -gt 0 ]]; then
        printf "\033[33m⚠ %d warning(s) detected.\033[0m\n" "$WARNINGS"
        echo "  Use --force to replace mismatched symlinks."
        echo ""
    fi

    echo "Project structure:"
    if [[ -L "$project_root/.spine" ]]; then
        echo "  .spine              -> (Spine repository symlink, gitignored)"
    else
        echo "  .spine/                (rsync/vendor mode — real directory)"
    fi
    if $COPY_MODE; then
        echo "  .agents/skills/        (physical skill copies — versionable)"
        echo "  .agents/rules/         (physical rule copies — Antigravity)"
        echo "  .agents/workflows/     (physical command copies — Antigravity slash)"
        echo "  .claude/skills/        (physical copy of skills hub)"
        echo "  .cursor/rules/         (physical rule copies)"
        echo "  .cursor/commands/      (physical command copies)"
        echo "  .cursor/skills/        (physical copy of skills hub)"
        echo "  .opencode/commands/    (physical command copies)"
        echo "  .opencode/agents/      (physical agent copies)"
    else
        echo "  .agents/skills/        (per-skill symlinks)"
        echo "  .agents/rules/         (per-file rule symlinks — Antigravity)"
        echo "  .agents/workflows/     (per-file command symlinks — Antigravity)"
        echo "  .claude/skills      -> .agents/skills/"
        echo "  .cursor/rules/         (per-file rule symlinks)"
        echo "  .cursor/commands/      (per-file command symlinks)"
        echo "  .cursor/skills      -> .agents/skills/"
        echo "  .opencode/commands/    (per-file command symlinks)"
        echo "  .opencode/agents/      (per-file agent symlinks)"
    fi
    echo ""
    echo "  docs/       memory bank templates (seeded, fill via /spine-bootstrap)"
    echo "  Rules:      opencode.json (GitHub URLs) + .agents/rules (Antigravity)"
    echo "  Skills:     docs/governance/skills-policy.md"
    echo ""
    echo "Next step (IDE): /spine-bootstrap"
    echo ""
    echo "==========================================="
}

# ===========================================================================
# Main
# ===========================================================================

PROJECT_ROOT="$(find_project_root)" || exit 1

# Handle --list-skills
if $LIST_SKILLS; then
    list_skills
    exit 0
fi

# Handle --add-skill
if [[ -n "$ADD_SKILL" ]]; then
    require_spine_path "$PROJECT_ROOT"
    add_skill "$PROJECT_ROOT" "$ADD_SKILL"
    exit $?
fi

# Handle --remove-skill
if [[ -n "$REMOVE_SKILL" ]]; then
    require_spine_path "$PROJECT_ROOT"
    remove_skill "$PROJECT_ROOT" "$REMOVE_SKILL"
    exit $?
fi

# Handle --uninstall
if $UNINSTALL_MODE; then
    uninstall_project "$PROJECT_ROOT"
    exit 0
fi

# Handle --graphify-uninstall (Graphify platform artifacts only)
if $GRAPHIFY_UNINSTALL; then
    require_spine_path "$PROJECT_ROOT"
    setup_project_graphify "$PROJECT_ROOT"
    exit 0
fi

# Handle --mkdocs-uninstall (MkDocs templates and config)
if $MKDOCS_UNINSTALL; then
    require_spine_path "$PROJECT_ROOT"
    setup_project_mkdocs "$PROJECT_ROOT"
    exit 0
fi

echo "Spine Project Installer"
echo "Repository: $SPINE_DIR"
echo "Project:    $PROJECT_ROOT"
echo "Targets:    $TARGETS"
echo "OS:         $OS"
if $FORCE; then echo "Mode: force (will replace existing symlinks/copies)"; fi
if $UPDATE_MODE; then echo "Mode: update (install + cleanup dangling)"; fi
if $COPY_MODE; then echo "Mode: copy (physical files; .spine stays symlink)"; fi
if $DRY_RUN; then echo "Mode: dry-run (preview only)"; fi
if $WITH_GRAPHIFY; then
    echo "Graphify:   enabled (tri-platform: cursor, opencode, claude)"
    if $GRAPHIFY_INIT; then
        echo "Graphify:   initial graph build + platform co-install"
    fi
    if $GRAPHIFY_HOOKS; then
        echo "Graphify:   git hooks enabled"
    fi
fi
if $WITH_MKDOCS; then
    echo "MkDocs:     enabled"
    if $MKDOCS_INIT; then
        echo "MkDocs:     template seed + initial build"
    fi
fi

chmod_scripts

require_spine_path "$PROJECT_ROOT"

# Resolve skill list (default: all)
SKILL_LIST="$(resolve_skills "${SKILLS_ARG:-all}")"

echo ""
echo "Skills to install:"
echo "$SKILL_LIST" | while read -r skill; do
    [[ -n "$skill" ]] && echo "  - $skill"
done

# Parse targets
INSTALL_CURSOR=false
INSTALL_OPENCODE=false
INSTALL_CLAUDE=false
INSTALL_ANTIGRAVITY=false
IFS=',' read -ra TARGET_ARRAY <<< "$TARGETS"
for target in "${TARGET_ARRAY[@]}"; do
    case "$target" in
        cursor)      INSTALL_CURSOR=true ;;
        opencode)    INSTALL_OPENCODE=true ;;
        claude)      INSTALL_CLAUDE=true ;;
        antigravity) INSTALL_ANTIGRAVITY=true ;;
        *)           echo "WARNING: Unknown target '$target', skipping" >&2 ;;
    esac
done

# Install skills (shared .agents/ hub)
install_project_skills "$PROJECT_ROOT" "$SKILL_LIST"

# Install per-tool wiring
if $INSTALL_CURSOR; then
    install_project_cursor "$PROJECT_ROOT"
fi

if $INSTALL_OPENCODE; then
    install_project_opencode "$PROJECT_ROOT"
fi

if $INSTALL_CLAUDE; then
    install_project_claude "$PROJECT_ROOT"
fi

if $INSTALL_ANTIGRAVITY; then
    install_project_antigravity "$PROJECT_ROOT"
fi

# Seed docs/ templates and merge opencode.json
seed_docs_templates "$PROJECT_ROOT"
merge_or_copy_opencode "$PROJECT_ROOT"

# Add gitignore entries
add_gitignore_entries "$PROJECT_ROOT"

# Optional Graphify setup (interactive opt-in on fresh install)
prompt_graphify_opt_in "$PROJECT_ROOT"
if $WITH_GRAPHIFY; then
    setup_project_graphify "$PROJECT_ROOT"
fi

# Optional MkDocs setup (interactive opt-in on fresh install)
prompt_mkdocs_opt_in "$PROJECT_ROOT"
if $WITH_MKDOCS; then
    setup_project_mkdocs "$PROJECT_ROOT"
fi

# Cleanup dangling symlinks (only in update mode)
if $UPDATE_MODE; then
    cleanup_dangling_symlinks "$PROJECT_ROOT"
fi

# Health check (always, silent in install mode, verbose in update mode)
validate_health "$PROJECT_ROOT"

print_project_summary "$PROJECT_ROOT"

if $DRY_RUN; then
    echo ""
    echo "This was a dry run. No changes were made."
    echo "Run without --dry-run to apply."
fi