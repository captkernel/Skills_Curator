"""--export-eval emits shareable markdown — the differentiating feature."""
from __future__ import annotations


def test_export_eval_emits_markdown(isolated_registry, capsys):
    isolated_registry.cmd_add(
        "browser", "Agent Browser",
        "https://github.com/vercel-labs/agent-browser",
        "npx skills add vercel-labs/agent-browser",
    )
    isolated_registry.cmd_eval(
        "browser", "my-scraper", "partial", "Useful for auth flows",
        pros=["Handles JS-heavy pages", "Session import auth"],
        cons=["Requires Chrome"],
        conflicts=["Overlaps with Playwright"],
    )
    capsys.readouterr()
    isolated_registry.cmd_export_eval("browser")
    out = capsys.readouterr().out
    assert "# Skill Evaluation: Agent Browser" in out
    assert "**PARTIAL**" in out
    assert "## ✅ Pros" in out
    assert "Handles JS-heavy pages" in out
    assert "## ⚠️ Cons" in out
    assert "## 🔴 Conflicts" in out
    # Footer exists
    assert "Skills Curator" in out


def test_export_eval_unknown_skill(isolated_registry, capsys):
    isolated_registry.cmd_export_eval("does-not-exist")
    assert "not found" in capsys.readouterr().out.lower()


def test_export_eval_no_evaluation_yet(isolated_registry, capsys):
    isolated_registry.cmd_add("x", "X", "https://github.com/a/b", "echo")
    isolated_registry.cmd_export_eval("x")
    out = capsys.readouterr().out
    assert "No evaluations" in out
