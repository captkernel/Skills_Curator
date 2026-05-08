"""Validator: pass/fail behaviour and exit codes."""
from __future__ import annotations

import json

import pytest


def test_validate_empty_registry_passes(isolated_registry):
    with pytest.raises(SystemExit) as exc:
        isolated_registry.cmd_validate(strict=False)
    assert exc.value.code == 0


def test_validate_catches_duplicate_id(isolated_registry):
    bad = {
        "version": isolated_registry.SCHEMA_VERSION,
        "last_updated": "2026-01-01",
        "skills": [
            {"id": "x", "name": "X", "type": "capability", "install_command": "echo"},
            {"id": "x", "name": "X2", "type": "capability", "install_command": "echo"},
        ],
    }
    isolated_registry.REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    isolated_registry.REGISTRY_FILE.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        isolated_registry.cmd_validate(strict=False)
    assert exc.value.code == 3


def test_validate_strict_warns_on_no_tags(isolated_registry, capsys):
    isolated_registry.cmd_add(
        "no-tags", "No Tags", "https://github.com/x/y", "echo",
    )
    with pytest.raises(SystemExit) as exc:
        isolated_registry.cmd_validate(strict=True)
    # warnings only — exit code should still be 0
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "No tags" in out
