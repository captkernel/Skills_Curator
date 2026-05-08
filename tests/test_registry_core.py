"""Core registry behaviour: add, eval (with pros/cons/conflicts), history, validate."""
from __future__ import annotations


def test_load_empty_registry_when_no_file(isolated_registry):
    reg = isolated_registry.load_registry()
    assert reg["version"] == isolated_registry.SCHEMA_VERSION
    assert reg["skills"] == []


def test_add_skill(isolated_registry):
    isolated_registry.cmd_add(
        "test-skill", "Test Skill",
        "https://github.com/test/test",
        "echo install",
    )
    reg = isolated_registry.load_registry()
    assert len(reg["skills"]) == 1
    s = reg["skills"][0]
    assert s["id"] == "test-skill"
    assert s["type"] == "capability"
    # v3 fields populated
    assert s["security_scan"] is None
    assert s["installed_version"] is None
    assert s["pairs_with"] == []


def test_add_duplicate_is_noop(isolated_registry, capsys):
    for _ in range(2):
        isolated_registry.cmd_add(
            "dup", "Dup", "https://github.com/x/y", "echo",
        )
    reg = isolated_registry.load_registry()
    assert len(reg["skills"]) == 1
    out = capsys.readouterr().out
    assert "already registered" in out


def test_eval_captures_pros_cons_conflicts(isolated_registry):
    """Bug #6 from the audit: --eval used to silently drop pros/cons/conflicts."""
    isolated_registry.cmd_add(
        "browser", "Browser",
        "https://github.com/vercel-labs/agent-browser",
        "npx skills add vercel-labs/agent-browser",
    )
    isolated_registry.cmd_eval(
        "browser", "my-scraper", "partial",
        "Useful for auth flows",
        pros=["Handles JS-heavy pages", "Session import auth"],
        cons=["Requires Chrome"],
        conflicts=["Overlaps with Playwright"],
    )
    reg = isolated_registry.load_registry()
    ev = reg["skills"][0]["evaluation_history"][0]
    assert ev["pros"] == ["Handles JS-heavy pages", "Session import auth"]
    assert ev["cons"] == ["Requires Chrome"]
    assert ev["conflicts"] == ["Overlaps with Playwright"]
    assert ev["verdict"] == "partial"


def test_eval_invalid_verdict_rejected(isolated_registry, capsys):
    isolated_registry.cmd_add(
        "x", "X", "https://github.com/a/b", "echo",
    )
    isolated_registry.cmd_eval("x", "proj", "maybe", "summary")
    reg = isolated_registry.load_registry()
    assert reg["skills"][0]["evaluation_history"] == []
    assert "verdict" in capsys.readouterr().out.lower()


def test_split_csv_handles_whitespace_and_empties(isolated_registry):
    f = isolated_registry._split_csv
    assert f(None) == []
    assert f("") == []
    assert f("a,b,c") == ["a", "b", "c"]
    assert f(" a , b , ,c ") == ["a", "b", "c"]


def test_remove_skill(isolated_registry, capsys):
    isolated_registry.cmd_add("rm-me", "Rm", "https://github.com/a/b", "echo")
    isolated_registry.cmd_remove("rm-me")
    reg = isolated_registry.load_registry()
    assert reg["skills"] == []
    isolated_registry.cmd_remove("rm-me")  # second time is a no-op
    assert "Not found" in capsys.readouterr().out
