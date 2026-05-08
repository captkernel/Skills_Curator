"""Coverage for v4.3.0: PLATFORMS catalog, cmd_platforms, and the
multi-target / detection-aware migrate flow."""
from __future__ import annotations


def test_platforms_catalog_has_55_entries(isolated_registry):
    """skills.sh ships 55 agent adapters as of v1.5.5; we mirror that."""
    assert len(isolated_registry.PLATFORMS) == 55


def test_claude_code_is_first_class(isolated_registry):
    """Claude Code must remain the primary target — it's the maintainer's
    actual user base and the source for cross-agent migrations."""
    cc = isolated_registry.PLATFORMS["claude-code"]
    assert cc["display"] == "Claude Code"
    assert "claude-code" in isolated_registry.DEFAULT_PLATFORMS


def test_agent_paths_back_compat(isolated_registry):
    """Older callers (and the existing migrate test) read AGENT_PATHS as a
    flat {id: Path}. Keep that shape working."""
    assert "claude-code" in isolated_registry.AGENT_PATHS
    assert isolated_registry.AGENT_PATHS["claude-code"] == \
        isolated_registry.PLATFORMS["claude-code"]["dir"]


def test_detect_platforms_returns_only_existing(isolated_registry, tmp_path, monkeypatch):
    """_detect_platforms checks each platform's detect path. Point them all
    at non-existent dirs and confirm the result is empty."""
    fake = tmp_path / "no-such"
    monkeypatch.setattr(isolated_registry, "PLATFORMS",
                        {pid: {**meta, "detect": fake / pid}
                         for pid, meta in isolated_registry.PLATFORMS.items()})
    assert isolated_registry._detect_platforms() == []


def test_migrate_unknown_target_rejected(isolated_registry, tmp_path, monkeypatch, capsys):
    """An unknown platform id must produce an error, not a silent miss or
    a copytree to a guessed path."""
    src = tmp_path / "src"
    (src / "skill-a").mkdir(parents=True)
    (src / "skill-a" / "SKILL.md").write_text("---\nname: a\n---\n# A\n")
    cc = dict(isolated_registry.PLATFORMS["claude-code"])
    cc["dir"] = src
    monkeypatch.setitem(isolated_registry.PLATFORMS, "claude-code", cc)

    isolated_registry.cmd_migrate("not-a-real-agent")
    out = capsys.readouterr().out
    assert "Unknown platform" in out
    assert "not-a-real-agent" in out


def test_migrate_multi_target_csv(isolated_registry, tmp_path, monkeypatch, capsys):
    """--migrate cursor,codex copies skills into both destinations."""
    src = tmp_path / "claude-skills"
    (src / "skill-x").mkdir(parents=True)
    (src / "skill-x" / "SKILL.md").write_text("---\nname: x\n---\n# X\n")

    new_platforms = dict(isolated_registry.PLATFORMS)
    new_platforms["claude-code"] = {**new_platforms["claude-code"], "dir": src}
    new_platforms["cursor"] = {**new_platforms["cursor"], "dir": tmp_path / "cursor-skills"}
    new_platforms["codex"]  = {**new_platforms["codex"],  "dir": tmp_path / "codex-skills"}
    monkeypatch.setattr(isolated_registry, "PLATFORMS", new_platforms)

    isolated_registry.cmd_migrate("cursor,codex")
    out = capsys.readouterr().out
    assert "Cursor" in out and "Codex" in out
    assert (tmp_path / "cursor-skills" / "skill-x" / "SKILL.md").exists()
    assert (tmp_path / "codex-skills"  / "skill-x" / "SKILL.md").exists()


def test_known_skills_have_pros_and_cons(isolated_registry):
    """Pros/cons enrichment is a v4.3.0 deliverable — every curated entry
    must have both fields populated so cmd_recommend has something to show."""
    for skill in isolated_registry.KNOWN_SKILLS:
        assert "pros" in skill, f"{skill['id']} missing pros"
        assert "cons" in skill, f"{skill['id']} missing cons"
        assert skill["pros"], f"{skill['id']} pros is empty"
        assert skill["cons"], f"{skill['id']} cons is empty"


def test_catalog_fetch_skipped_when_telemetry_off(isolated_registry):
    """conftest forces SKILLS_NO_TELEMETRY=1, so the GitHub fetcher must
    return [] and the catalog must equal KNOWN_SKILLS only."""
    discovered = isolated_registry._fetch_github_topics()
    assert discovered == []
    catalog = isolated_registry._load_catalog(refresh=True)
    curated_ids = {s["id"] for s in isolated_registry.KNOWN_SKILLS}
    catalog_ids = {s["id"] for s in catalog}
    assert curated_ids == catalog_ids


def test_merge_catalog_curated_wins_on_id_collision(isolated_registry):
    """Curated entries hand-author pros/cons; community-discovered entries
    don't. On collision the curated record must win so we don't lose them."""
    discovered = [{
        "id": "frontend-design",
        "name": "Frontend Design (community fork)",
        "trust": "unknown",
        "pros": [],
        "cons": [],
    }]
    merged = isolated_registry._merge_catalog(
        isolated_registry.KNOWN_SKILLS, discovered)
    fd = next(s for s in merged if s["id"] == "frontend-design")
    assert fd["trust"] == "official"
    assert fd["pros"]  # curated pros preserved
