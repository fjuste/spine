"""OpenCode consumer template contract tests."""

import json
from pathlib import Path


def _load_template() -> dict:
    return json.loads(Path("templates/opencode.json").read_text(encoding="utf-8"))


def test_opencode_template_has_model_and_default_agent() -> None:
    cfg = _load_template()
    assert cfg["$schema"] == "https://opencode.ai/config.json"
    assert cfg["default_agent"] == "ask"
    assert cfg["permission"]
    assert cfg["permission"]["bash"] == "allow"
    assert cfg["permission"]["websearch"] == "allow"
    assert cfg["permission"]["webfetch"] == "allow"


def test_opencode_template_registers_ask_agent() -> None:
    cfg = _load_template()
    ask = cfg["agent"]["ask"]
    assert ask["mode"] == "primary"
    assert "model" not in ask
    assert ask["temperature"] == 0.3
    assert ask["description"]
    assert ask["prompt"] == "{file:.spine/agents/ask.md}"
    assert ask["permission"]["edit"] == "deny"
    assert ask["permission"]["bash"] == "allow"


def test_opencode_template_has_spine_instructions_and_compaction() -> None:
    cfg = _load_template()
    assert len(cfg["instructions"]) == 3
    assert "02-memory-bank.md" in cfg["instructions"][1]
    assert cfg["compaction"]["auto"] is True
    assert cfg["compaction"]["prune"] is False
    assert cfg["compaction"]["tail_turns"] == 4
