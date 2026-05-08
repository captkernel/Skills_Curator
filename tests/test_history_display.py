"""cmd_history should display conflicts and adoption_plan, not just summary."""
from __future__ import annotations


def test_history_shows_pros_cons_conflicts(isolated_registry, capsys):
    isolated_registry.cmd_add(
        "ab", "AB", "https://github.com/a/b", "echo",
    )
    isolated_registry.cmd_eval(
        "ab", "proj", "partial", "mixed bag",
        pros=["fast"], cons=["heavy"], conflicts=["pw-overlap"],
    )
    capsys.readouterr()  # drain
    isolated_registry.cmd_history("ab")
    out = capsys.readouterr().out
    assert "pros" in out.lower()
    assert "fast" in out
    assert "cons" in out.lower()
    assert "heavy" in out
    assert "conflicts" in out.lower()
    assert "pw-overlap" in out


def test_history_unknown_skill(isolated_registry, capsys):
    isolated_registry.cmd_history("does-not-exist")
    assert "Not found" in capsys.readouterr().out
