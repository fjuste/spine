"""Symlink and physical-copy wiring for IDE trees."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from spine_cli.constants import CORE_RULES, CORE_SKILLS, KNOWN_TARGETS
from spine_cli.log import Log, die
from spine_cli.skills import available_skills, installed_skills, markdown_names
from spine_cli.workflow_skills import (
    WORKFLOW_TARGETS,
    command_description,
    render_skill_markdown,
    workflow_names,
)


def parse_targets(raw: str) -> set[str]:
    """Parse a comma-separated target list.

    Args:
        raw: Flag value such as ``cursor,opencode``.

    Returns:
        Known target names. Unknown names are warned and skipped.
    """
    selected: set[str] = set()
    for part in raw.split(","):
        name = part.strip()
        if not name:
            continue
        if name not in KNOWN_TARGETS:
            print(f"WARNING: Unknown target '{name}', skipping")
            continue
        selected.add(name)
    return selected


def _mkdir(path: Path, log: Log) -> None:
    if log.dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def create_relative_symlink(
    rel_target: str,
    link_path: Path,
    label: str,
    log: Log,
    *,
    force: bool,
) -> None:
    """Create ``link_path`` as a relative symlink to ``rel_target``.

    Args:
        rel_target: Link text stored in the symlink.
        link_path: Path to create.
        label: Human label for logs.
        log: Progress logger.
        force: Replace a symlink that points elsewhere.

    Raises:
        SpineExit: When the OS refuses to create a symlink.
    """
    _mkdir(link_path.parent, log)
    if link_path.is_symlink():
        current = os.readlink(link_path)
        if current == rel_target:
            log.skip(f"{label} (already linked)")
            return
        if not force:
            log.warn(f"{label} (points to {current}, expected {rel_target})")
            print("             Use --force to replace.", flush=True)
            return
        if log.dry_run:
            log.dry(f"Would replace: {link_path}")
            return
        link_path.unlink()
        try:
            link_path.symlink_to(rel_target)
        except OSError as exc:
            die(
                f"Cannot create symlink {link_path} ({exc}). "
                "Use: python3 scripts/spine.py vendor"
            )
        log.warn(f"{label} (replaced: {current} -> {rel_target})")
        return

    if link_path.exists():
        log.conflict(f"{label} ({link_path} exists and is not a symlink)")
        print("             Remove it and re-run install.", flush=True)
        return

    if log.dry_run:
        log.dry(f"Would link: {link_path} -> {rel_target}")
        return
    try:
        link_path.symlink_to(rel_target)
    except OSError as exc:
        die(
            f"Cannot create symlink {link_path} ({exc}). "
            "Use: python3 scripts/spine.py vendor"
        )
    log.plus(label)


def copy_file(src: Path, dest: Path, label: str, log: Log, *, force: bool, copy_mode: bool) -> None:
    """Copy one file, replacing a symlink when copy mode or ``--force`` is set.

    Args:
        src: Source file.
        dest: Destination file.
        label: Human label for logs.
        log: Progress logger.
        force: Replace an existing different file.
        copy_mode: Hybrid or vendor materialize.
    """
    if not src.is_file():
        log.warn(f"File missing, skip: {src}")
        return
    if dest.is_symlink():
        if not (force or copy_mode):
            log.conflict(f"{label} ({dest} is a symlink; use --force or --copy)")
            return
        if not log.dry_run:
            dest.unlink()
    elif dest.exists() and not (force or copy_mode):
        log.skip(f"{label} (already exists)")
        return
    if log.dry_run:
        log.dry(f"Would copy file: {dest}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    log.plus(f"{label} (copied)")


def copy_tree(src: Path, dest: Path, log: Log, *, force: bool, copy_mode: bool) -> None:
    """Copy a directory tree over ``dest``.

    Args:
        src: Source directory.
        dest: Destination directory.
        log: Progress logger.
        force: Replace a symlink at ``dest``.
        copy_mode: Hybrid or vendor materialize.
    """
    if not src.is_dir():
        log.warn(f"Source missing, skip: {src}")
        return
    if dest.is_symlink():
        if not (force or copy_mode):
            log.conflict(f"{dest.name} ({dest} is a symlink; use --force or --copy)")
            return
        if log.dry_run:
            log.dry(f"Would replace symlink with copy: {dest}")
        else:
            dest.unlink()
    if log.dry_run:
        log.dry(f"Would copy tree: {src} -> {dest}")
        return
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=True, dirs_exist_ok=True)


def _place_file(
    src: Path,
    dest: Path,
    rel_target: str,
    label: str,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    if copy_mode:
        copy_file(src, dest, label, log, force=force, copy_mode=True)
        return
    if not src.is_file():
        log.warn(f"{label} not found, skipping")
        return
    create_relative_symlink(rel_target, dest, label, log, force=force)


def install_skills(
    project: Path,
    content: Path,
    skill_names: list[str],
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
    update_mode: bool,
) -> None:
    """Install the skill hub under ``.agents/skills``.

    Args:
        project: Consumer project root.
        content: Spine tree that holds ``skills/``.
        skill_names: Skills to install.
        log: Progress logger.
        copy_mode: Copy trees instead of linking.
        force: Replace mismatched links.
        update_mode: Remove skills that are no longer selected. ``commands/*.md``
            bundles stay.
    """
    hub = project / ".agents" / "skills"
    _mkdir(hub, log)
    print("\nSkills:")
    if update_mode and not log.dry_run and hub.is_dir():
        selected = set(skill_names)
        reserved = set(workflow_names(content))
        for existing in list(hub.iterdir()):
            if existing.name in reserved:
                continue
            if existing.name not in selected and (existing.is_dir() or existing.is_symlink()):
                if existing.is_dir() and not existing.is_symlink():
                    shutil.rmtree(existing)
                else:
                    existing.unlink()
                log.plus(f"removed skill (not in selection): {existing.name}")
                log.cleaned += 1

    for skill in skill_names:
        source = content / "skills" / skill
        dest = hub / skill
        if not source.is_dir():
            log.warn(f"Skill '{skill}' not found in Spine repo, skipping")
            continue
        if copy_mode:
            copy_tree(source, dest, log, force=force, copy_mode=True)
            log.plus(f"skill: {skill} (copied)")
        else:
            create_relative_symlink(
                f"../../.spine/skills/{skill}",
                dest,
                f"skill: {skill}",
                log,
                force=force,
            )


def _install_named_files(
    names: list[str],
    source_dir: Path,
    dest_dir: Path,
    rel_prefix: str,
    label: str,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    _mkdir(dest_dir, log)
    for name in names:
        _place_file(
            source_dir / name,
            dest_dir / name,
            f"{rel_prefix}/{name}",
            f"{label}: {name}",
            log,
            copy_mode=copy_mode,
            force=force,
        )


def install_cursor(
    project: Path,
    content: Path,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Wire Cursor rules, commands, and the skills hub.

    Args:
        project: Consumer project root.
        content: Spine content root.
        log: Progress logger.
        copy_mode: Physical copies.
        force: Replace mismatched links.
    """
    print("\n=== Cursor (project-level) ===")
    _install_named_files(
        list(CORE_RULES),
        content / "rules",
        project / ".cursor" / "rules",
        "../../.spine/rules",
        "rule",
        log,
        copy_mode=copy_mode,
        force=force,
    )
    _install_named_files(
        markdown_names(content / "commands"),
        content / "commands",
        project / ".cursor" / "commands",
        "../../.spine/commands",
        "command",
        log,
        copy_mode=copy_mode,
        force=force,
    )
    skills_dest = project / ".cursor" / "skills"
    skills_src = project / ".agents" / "skills"
    if copy_mode:
        copy_tree(skills_src, skills_dest, log, force=force, copy_mode=True)
        log.plus(".cursor/skills/ (copied)")
    else:
        create_relative_symlink("../.agents/skills", skills_dest, "skills", log, force=force)


def install_claude(project: Path, log: Log, *, copy_mode: bool, force: bool) -> None:
    """Wire the Claude skills hub.

    Args:
        project: Consumer project root.
        log: Progress logger.
        copy_mode: Physical copies.
        force: Replace mismatched links.
    """
    print("\n=== Claude Code (project-level) ===")
    dest = project / ".claude" / "skills"
    if copy_mode:
        copy_tree(project / ".agents" / "skills", dest, log, force=force, copy_mode=True)
        log.plus(".claude/skills/ (copied)")
    else:
        create_relative_symlink("../.agents/skills", dest, "skills", log, force=force)


def warn_global_opencode_agents(log: Log) -> None:
    """Warn when ``~/.config/opencode/agents`` still points at Spine.

    Args:
        log: Progress logger.
    """
    global_agents = Path.home() / ".config" / "opencode" / "agents"
    if not global_agents.is_dir():
        return
    for link in global_agents.glob("*.md"):
        if not link.is_symlink():
            continue
        target = os.readlink(link)
        if "/spine/agents/" in target or ".spine/agents/" in target:
            log.warn(f"Global OpenCode agent symlink: ~/.config/opencode/agents/{link.name}")
            log.warn("Spine agents are project-only. Remove the global symlink.")


def install_opencode(
    project: Path,
    content: Path,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Wire OpenCode commands and agents.

    Args:
        project: Consumer project root.
        content: Spine content root.
        log: Progress logger.
        copy_mode: Physical copies.
        force: Replace mismatched links.
    """
    print("\n=== OpenCode (project-level) ===")
    warn_global_opencode_agents(log)
    _install_named_files(
        markdown_names(content / "commands"),
        content / "commands",
        project / ".opencode" / "commands",
        "../../.spine/commands",
        "command",
        log,
        copy_mode=copy_mode,
        force=force,
    )
    _install_named_files(
        markdown_names(content / "agents"),
        content / "agents",
        project / ".opencode" / "agents",
        "../../.spine/agents",
        "agent",
        log,
        copy_mode=copy_mode,
        force=force,
    )


def _mirror_extra_rules(project: Path, log: Log, *, copy_mode: bool, force: bool) -> None:
    cursor_rules = project / ".cursor" / "rules"
    agents_rules = project / ".agents" / "rules"
    if not cursor_rules.is_dir():
        return
    core = set(CORE_RULES)
    mirrored = 0
    for src in sorted(cursor_rules.iterdir()):
        if not src.is_file() or src.name in core:
            continue
        dest = agents_rules / src.name
        if copy_mode or not dest.is_symlink():
            if log.dry_run:
                log.dry(f"Would mirror: {src.name}")
            else:
                _mkdir(agents_rules, log)
                shutil.copy2(src, dest)
                log.plus(f"agy-rule (project): {src.name}")
        else:
            create_relative_symlink(
                f"../../.cursor/rules/{src.name}",
                dest,
                f"agy-rule (project): {src.name}",
                log,
                force=force,
            )
        mirrored += 1
    if mirrored == 0:
        log.skip("no extra project rules to mirror")


def install_antigravity(
    project: Path,
    content: Path,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Wire Antigravity rules and drop legacy workflow files.

    Slash commands are skills under ``.agents/skills/<name>/SKILL.md``.
    ``publish_workflow_skills`` writes those bundles. This step removes any
    ``.agents/workflows/<name>.md`` left by older installs.

    Args:
        project: Consumer project root.
        content: Spine content root.
        log: Progress logger.
        copy_mode: Physical copies.
        force: Replace mismatched links.
    """
    print("\n=== Antigravity (project-level) ===")
    _install_named_files(
        list(CORE_RULES),
        content / "rules",
        project / ".agents" / "rules",
        "../../.spine/rules",
        "agy-rule",
        log,
        copy_mode=copy_mode,
        force=force,
    )
    _mirror_extra_rules(project, log, copy_mode=copy_mode, force=force)
    remove_legacy_workflows(project, set(workflow_names(content)), log)


def publish_workflow_skills(
    project: Path,
    content: Path,
    targets: set[str],
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Install ``commands/*.md`` as skills for Claude Code and Antigravity.

    Args:
        project: Consumer project root.
        content: Spine tree that holds ``commands/``.
        targets: Selected IDE targets.
        log: Progress logger.
        copy_mode: Copy ``procedure.md`` instead of linking it.
        force: Replace a procedure symlink that points elsewhere.
    """
    if not (targets & WORKFLOW_TARGETS):
        return
    names = workflow_names(content)
    if not names:
        return
    print("\nWorkflow skills (Claude Code and Antigravity):")
    hub = project / ".agents" / "skills"
    _mkdir(hub, log)
    for name in names:
        source = content / "commands" / f"{name}.md"
        if not source.is_file():
            log.warn(f"Workflow command missing, skip: {source}")
            continue
        dest_dir = hub / name
        if dest_dir.is_symlink():
            log.conflict(f"workflow skill: {name} ({dest_dir} is a symlink)")
            continue
        _mkdir(dest_dir, log)
        _write_workflow_skill(
            dest_dir / "SKILL.md",
            name,
            command_description(source),
            log,
        )
        procedure = dest_dir / "procedure.md"
        if copy_mode:
            copy_file(
                source,
                procedure,
                f"workflow procedure: {name}",
                log,
                force=True,
                copy_mode=True,
            )
        else:
            create_relative_symlink(
                f"../../../.spine/commands/{name}.md",
                procedure,
                f"workflow procedure: {name}",
                log,
                force=force,
            )
    remove_legacy_workflows(project, set(names), log)


def _write_workflow_skill(path: Path, name: str, description: str, log: Log) -> None:
    body = render_skill_markdown(name, description)
    if path.is_file() and path.read_text(encoding="utf-8") == body:
        log.skip(f"workflow skill: {name} (already current)")
        return
    if log.dry_run:
        log.dry(f"Would write workflow skill: {name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    log.plus(f"workflow skill: {name}")


def remove_legacy_workflows(project: Path, names: set[str], log: Log) -> None:
    """Remove Spine command files previously installed as Antigravity workflows.

    Args:
        project: Consumer project root.
        names: Command stems to delete from ``.agents/workflows``.
        log: Progress logger.
    """
    directory = project / ".agents" / "workflows"
    if not directory.is_dir():
        return
    for name in sorted(names):
        path = directory / f"{name}.md"
        if not path.exists() and not path.is_symlink():
            continue
        if log.dry_run:
            log.dry(f"Would remove legacy workflow: {path.name}")
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()
        log.plus(f"removed legacy workflow: {path.name}")


def install_selected_targets(
    project: Path,
    content: Path,
    targets: set[str],
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Wire each selected IDE target.

    Args:
        project: Consumer project root.
        content: Spine content root.
        targets: Target names from ``parse_targets``.
        log: Progress logger.
        copy_mode: Physical copies.
        force: Replace mismatched links.
    """
    if "cursor" in targets:
        install_cursor(project, content, log, copy_mode=copy_mode, force=force)
    if "opencode" in targets:
        install_opencode(project, content, log, copy_mode=copy_mode, force=force)
    if "claude" in targets:
        install_claude(project, log, copy_mode=copy_mode, force=force)
    if "antigravity" in targets:
        install_antigravity(project, content, log, copy_mode=copy_mode, force=force)


def add_one_skill(
    project: Path,
    content: Path,
    skill_name: str,
    log: Log,
    *,
    copy_mode: bool,
    force: bool,
) -> None:
    """Install a single skill into the hub and real IDE copies.

    Args:
        project: Consumer project root.
        content: Spine content root.
        skill_name: Skill directory name.
        log: Progress logger.
        copy_mode: Copy instead of link.
        force: Replace mismatched links.

    Raises:
        SpineExit: When the skill does not exist.
    """
    source = content / "skills" / skill_name
    if not source.is_dir():
        names = "\n".join(available_skills(content)) or "(none)"
        die(f"Skill '{skill_name}' not found in {content}/skills/\nAvailable skills:\n{names}")
    hub = project / ".agents" / "skills"
    dest = hub / skill_name
    _mkdir(hub, log)
    use_copy = copy_mode or (dest.is_dir() and not dest.is_symlink())
    if use_copy:
        copy_tree(source, dest, log, force=True, copy_mode=True)
        log.plus(f"skill: {skill_name} (copied)")
        for ide in (".cursor", ".claude"):
            ide_hub = project / ide / "skills"
            if ide_hub.is_dir() and not ide_hub.is_symlink():
                copy_tree(source, ide_hub / skill_name, log, force=True, copy_mode=True)
    else:
        create_relative_symlink(
            f"../../.spine/skills/{skill_name}",
            dest,
            f"skill: {skill_name}",
            log,
            force=force,
        )
    print(f"\nSkill '{skill_name}' installed in .agents/skills/")
    print("Restart your agent to pick up the new skill.")


def remove_one_skill(project: Path, skill_name: str, log: Log) -> None:
    """Remove one skill from the hub and real IDE copies.

    Args:
        project: Consumer project root.
        skill_name: Skill directory name.
        log: Progress logger.
    """
    dest = project / ".agents" / "skills" / skill_name
    if not dest.exists() and not dest.is_symlink():
        log.warn(f"'{skill_name}' not found in .agents/skills/")
        return
    if log.dry_run:
        log.dry(f"Would remove: {dest}")
        return
    if dest.is_dir() and not dest.is_symlink():
        shutil.rmtree(dest)
    else:
        dest.unlink()
    log.plus(f"skill: {skill_name} (removed)")
    for ide in (".cursor", ".claude"):
        hub = project / ide / "skills"
        mirrored = hub / skill_name
        if hub.is_dir() and not hub.is_symlink() and (mirrored.exists() or mirrored.is_symlink()):
            if mirrored.is_dir() and not mirrored.is_symlink():
                shutil.rmtree(mirrored)
            else:
                mirrored.unlink()


def list_skills(project: Path, spine: Path) -> None:
    """Print core, available, and installed skills.

    Args:
        project: Consumer project root.
        spine: Spine repository root.
    """
    installed = set(installed_skills(project))
    print("\n===========================================")
    print("  Spine Skills")
    print("===========================================\n")
    print(f"Spine repo: {spine}")
    print(f"Project:    {project}\n")
    print("Core skills (minimal profile with --core):")
    for name in CORE_SKILLS:
        marker = "x" if name in installed else " "
        print(f"  [{marker}] {name}")
    print("\nAvailable skills in Spine repo:")
    names = available_skills(spine)
    if not names:
        print("  (none found)")
    else:
        for name in names:
            marker = "x" if name in installed else " "
            print(f"  [{marker}] {name}")
    print("\n===========================================")


def _link_dangling(link: Path) -> bool:
    target = os.readlink(link)
    if target.startswith("/"):
        return not Path(target).exists()
    return not (link.parent / target).exists()


def cleanup_dangling(project: Path, log: Log) -> None:
    """Remove dangling symlinks and obsolete core-rule links.

    Args:
        project: Consumer project root.
        log: Progress logger.
    """
    print("\nCleanup (dangling symlinks):")
    directories = (
        project / ".agents" / "skills",
        project / ".cursor" / "rules",
        project / ".cursor" / "commands",
        project / ".opencode" / "commands",
        project / ".opencode" / "agents",
    )
    removed = 0
    core = set(CORE_RULES)
    for directory in directories:
        if not directory.is_dir():
            continue
        for link in list(directory.iterdir()):
            if not link.is_symlink():
                continue
            obsolete_rule = directory.name == "rules" and link.name not in core
            if not obsolete_rule and not _link_dangling(link):
                continue
            if log.dry_run:
                log.dry(f"Would remove dangling: {directory.name}/{link.name}")
            else:
                link.unlink()
                log.plus(f"removed dangling: {directory.name}/{link.name}")
            removed += 1
    log.cleaned += removed
    if removed == 0:
        log.skip("No dangling symlinks found")
    else:
        log.info(f"{removed} dangling symlink(s) removed")
