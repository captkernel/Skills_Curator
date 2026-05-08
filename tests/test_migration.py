"""Schema migration and persistence."""
from __future__ import annotations

import json


def _write_v1_registry(path, registry_dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry_dict), encoding="utf-8")


def test_v1_migrates_to_v3_on_load(isolated_registry):
    """v1 → v2 → v3 in one load. Bug from the audit: migration used to run
    on every load without persisting. Verify it persists this time."""
    legacy = {
        "version": "1.0",
        "last_updated": "2024-01-01",
        "skills": [{
            "id": "old",
            "name": "Old Skill",
            "source": "https://github.com/x/y",
            "install_command": "echo",
            "evaluation_history": [{
                "date": "2024-01-01",
                "project": "p",
                "verdict": "adopt",
                "summary": "fine",
            }],
        }],
    }
    _write_v1_registry(isolated_registry.REGISTRY_FILE, legacy)

    reg = isolated_registry.load_registry()
    assert reg["version"] == isolated_registry.SCHEMA_VERSION
    s = reg["skills"][0]
    # v1 → v2 fields
    assert "type" in s and s["type"] == "capability"
    assert "compatibility" in s
    assert s["security_reviewed"] is False
    # v2 → v3 fields
    assert s["installed_version"] is None
    assert s["pairs_with"] == []
    assert s["security_scan"] is None
    # Eval has the new fields
    ev = s["evaluation_history"][0]
    assert ev["skill_type"] == "capability"
    assert "adoption_plan" in ev
    assert "security_notes" in ev


def test_migration_persists_after_first_load(isolated_registry):
    """Once migrated, a subsequent load should NOT re-print the migration banner."""
    legacy = {"version": "1.0", "skills": []}
    _write_v1_registry(isolated_registry.REGISTRY_FILE, legacy)

    isolated_registry.load_registry()
    on_disk = json.loads(isolated_registry.REGISTRY_FILE.read_text())
    assert on_disk["version"] == isolated_registry.SCHEMA_VERSION

    # Second load: file already at current schema, no migration needed
    reg2 = isolated_registry.load_registry()
    assert reg2["version"] == isolated_registry.SCHEMA_VERSION
