"""Test fixtures. Each test gets an isolated registry under a tmp_path,
so we never touch the user's real ~/.claude/skills/skills-curator/."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "skills-curator" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def isolated_registry(tmp_path, monkeypatch):
    """Reload registry module with SKILL_DIR pointed at a tmp_path so tests
    never write into ~/.claude/."""
    fake_skill_dir = tmp_path / "skills-curator"
    fake_skill_dir.mkdir(parents=True, exist_ok=True)

    # Force telemetry off so tests don't make real HTTP calls.
    monkeypatch.setenv("SKILLS_NO_TELEMETRY", "1")

    # Import (or reload) the module after env is set, then patch the paths.
    if "registry" in sys.modules:
        registry = importlib.reload(sys.modules["registry"])
    else:
        registry = importlib.import_module("registry")

    monkeypatch.setattr(registry, "SKILL_DIR", fake_skill_dir)
    monkeypatch.setattr(registry, "REGISTRY_FILE", fake_skill_dir / "registry.json")
    monkeypatch.setattr(registry, "CATALOG_FILE", fake_skill_dir / "catalog.json")
    monkeypatch.setattr(registry, "RECOMMENDATIONS_FILE", fake_skill_dir / "recommendations.json")
    monkeypatch.setattr(registry, "NO_TELEMETRY", True)
    return registry
