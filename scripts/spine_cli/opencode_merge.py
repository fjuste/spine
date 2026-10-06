"""In-process wrappers around the existing opencode merge scripts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from spine_cli.log import Log


def _load(filename: str, module_name: str) -> ModuleType:
    path = Path(__file__).resolve().parents[1] / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def merge_project_opencode(spine: Path, project: Path, log: Log) -> None:
    """Merge Spine instructions into the consumer ``opencode.json``.

    Args:
        spine: Spine repository root.
        project: Consumer project root.
        log: Progress logger.
    """
    print("\nopencode.json:")
    template = spine / "templates" / "opencode.json"
    if not template.is_file():
        log.warn(f"templates/opencode.json not found in {spine}")
        return
    dest = project / "opencode.json"
    if log.dry_run:
        if dest.is_file():
            log.dry("Would merge Spine instructions into: opencode.json")
        else:
            log.dry("Would create: opencode.json from template")
        return
    module = _load("merge-opencode.py", "spine_merge_opencode")
    message = module.merge_opencode(template, dest)
    log.plus(f"opencode.json ({message})")


def replace_project_opencode(spine: Path, project: Path, log: Log) -> None:
    """Overwrite consumer ``opencode.json`` with the template.

    Args:
        spine: Spine repository root.
        project: Consumer project root.
        log: Progress logger.
    """
    template = spine / "templates" / "opencode.json"
    dest = project / "opencode.json"
    if log.dry_run:
        log.dry(f"Would replace: {dest}")
        return
    dest.write_bytes(template.read_bytes())
    print(f"  Replaced with template: {dest}")


def merge_graphify_plugin(project: Path, log: Log) -> None:
    """Merge Graphify plugin keys into the project ``opencode.json``.

    Args:
        project: Consumer project root.
        log: Progress logger.
    """
    dest = project / "opencode.json"
    if not dest.is_file():
        return
    if log.dry_run:
        log.dry("Would merge graphify plugin into opencode.json")
        return
    module = _load("merge-graphify-opencode.py", "spine_merge_graphify_opencode")
    local = project / ".opencode" / "opencode.json"
    local_path = local if local.is_file() else None
    print(f"    {module.merge_graphify_into_opencode(dest, local_path)}")


def strip_graphify_plugin(project: Path, log: Log) -> None:
    """Remove Graphify plugin keys from the project ``opencode.json``.

    Args:
        project: Consumer project root.
        log: Progress logger.
    """
    dest = project / "opencode.json"
    if not dest.is_file():
        return
    if log.dry_run:
        log.dry("Would strip graphify plugin from opencode.json")
        return
    module = _load("merge-graphify-opencode.py", "spine_merge_graphify_opencode")
    print(f"    {module.strip_graphify_from_opencode(dest)}")
