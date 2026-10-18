"""skills.sh discovery, blended ranking, --curate fast path, partner audits,
rival detection. No test touches the network: _http_get is always mocked."""
from __future__ import annotations

import json
import math
import sys

import pytest

SH_RESPONSE = {
    "query": "react performance",
    "skills": [
        {"id": "vercel-labs/agent-skills/vercel-react-best-practices",
         "source": "vercel-labs/agent-skills",
         "skillId": "vercel-react-best-practices",
         "name": "vercel-react-best-practices", "installs": 812274},
        {"id": "someone/repo/react-performance", "source": "someone/repo",
         "skillId": "react-performance", "name": "React Performance",
         "installs": 5955},
        # duplicate full id -> dropped
        {"id": "someone/repo/react-performance", "source": "someone/repo",
         "skillId": "react-performance", "name": "dupe", "installs": 1},
        # malformed source -> dropped
        {"id": "x", "source": "noslash", "skillId": "x", "installs": 3},
    ],
}


@pytest.fixture
def online(isolated_registry, monkeypatch):
    """Telemetry on, but every HTTP call goes through a recorder."""
    reg = isolated_registry
    monkeypatch.setattr(reg, "NO_TELEMETRY", False)
    calls: list[tuple[str, dict]] = []
    responses: dict[str, object] = {}

    def fake_get(url, headers=None, timeout=8):
        calls.append((url, headers or {}))
        for prefix, body in responses.items():
            if url.startswith(prefix):
                return json.dumps(body)
        return None

    monkeypatch.setattr(reg, "_http_get", fake_get)
    reg._test_calls = calls
    reg._test_responses = responses
    return reg


def _project(tmp_path, readme: str):
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "README.md").write_text(readme, encoding="utf-8")
    return proj


# ── skills.sh mapping ────────────────────────────────────────────────────────

def test_skills_sh_mapping(online):
    online._test_responses["https://skills.sh/api/search"] = SH_RESPONSE
    entries = online._fetch_skills_sh("react performance")
    assert len(entries) == 2
    e = entries[0]
    assert e["install"] == ("npx skills add vercel-labs/agent-skills "
                           "--skill vercel-react-best-practices")
    assert e["trust"] == "official"          # via _classify_trust("vercel-labs")
    assert "skills-sh" in e["tags"]
    assert e["installs"] == 812274
    assert e["sh_id"] == "vercel-labs/agent-skills/vercel-react-best-practices"
    assert e["url"] == ("https://skills.sh/vercel-labs/agent-skills/"
                        "vercel-react-best-practices")
    assert entries[1]["trust"] == "unknown"
    url, headers = online._test_calls[0]
    assert "q=react+performance" in url and "limit=20" in url
    assert "Authorization" not in headers


def test_skills_sh_api_key_sent_as_bearer(online, monkeypatch):
    monkeypatch.setattr(online, "SKILLS_SH_API_KEY", "sk_live_test")
    online._fetch_skills_sh("react", owner="vercel-labs")
    url, headers = online._test_calls[0]
    assert headers["Authorization"] == "Bearer sk_live_test"
    assert "owner=vercel-labs" in url


def test_skills_sh_network_off_returns_empty(isolated_registry, monkeypatch):
    called = []
    monkeypatch.setattr(isolated_registry, "_http_get",
                        lambda *a, **k: called.append(a) or "{}")
    assert isolated_registry.NO_TELEMETRY is True
    assert isolated_registry._fetch_skills_sh("react") == []
    assert isolated_registry._fetch_partner_audits("a/b", "c") is None
    assert called == []


def test_skills_sh_bad_payload_returns_empty(online, monkeypatch):
    monkeypatch.setattr(online, "_http_get", lambda *a, **k: "<html>nope")
    assert online._fetch_skills_sh("react") == []


def test_curated_wins_on_collision(online):
    entry = online._skills_sh_to_entry(SH_RESPONSE["skills"][0])
    merged = online._merge_find_results(online.KNOWN_SKILLS, [entry])
    hits = [m for m in merged if "vercel-react-best-practices" in m.get("install", "")]
    assert len(hits) == 1
    cur = hits[0]
    assert cur["id"] == "vercel-react-best-practices"
    assert cur.get("pros")                    # curated pros/cons kept
    assert cur["installs"] == 812274          # enriched with skills.sh count


# ── blended score math ───────────────────────────────────────────────────────

def test_blended_score_weights(isolated_registry):
    r = isolated_registry
    assert r._blended_score(1, 1, 1, 1) == pytest.approx(1.0)
    assert r._blended_score(1, 0, 0, 0) == pytest.approx(0.35)
    assert r._blended_score(0, 1, 0, 0) == pytest.approx(0.30)
    assert r._blended_score(0, 0, 1, 0) == pytest.approx(0.20)
    assert r._blended_score(0, 0, 0, 1) == pytest.approx(0.15)


def test_ranking_components(isolated_registry):
    r = isolated_registry
    entry = {"id": "react-perf", "name": "React Perf", "trust": "high",
             "tags": ["react", "nextjs", "performance"], "description": "",
             "installs": 185_000}
    [row] = r._rank_entries([entry], "react performance", ["react", "nextjs", "python"])
    assert row["relevance"] == pytest.approx(0.9)   # react: name 1.0, performance: tag 0.8
    assert row["fit"] == pytest.approx(2 / 3 * 0.9, abs=1e-3)   # fit x relevance with a query
    assert row["matched"] == ["nextjs", "react"]
    assert row["trust"] == 0.8
    assert row["popularity"] == pytest.approx(min(1, math.log10(185_001) / 6), abs=1e-3)
    expected = 0.35 * 0.9 + 0.30 * row["fit"] + 0.20 * 0.8 + 0.15 * row["popularity"]
    assert row["score"] == pytest.approx(expected, abs=1e-3)
    why = r._why_line(row)
    assert why.startswith("why: ")
    assert "fit .6 (nextjs, react)" in why
    assert "trust high" in why and "185K installs" in why


def test_relevance_no_query_and_stars_fallback(isolated_registry):
    r = isolated_registry
    e = {"id": "x", "name": "x", "tags": [], "stars": 999}
    assert r._relevance(e, None) == 1.0
    assert r._relevance(e, "") == 1.0
    pop, n, label = r._popularity(e)
    assert n == 999 and label == "stars" and pop == pytest.approx(math.log10(1000) / 6)
    assert r._popularity({"id": "y"}) == (0.0, None, "")
    assert r.TRUST_SCORES == {"official": 1.0, "high": 0.8, "medium": 0.6,
                              "community": 0.4, "unknown": 0.2}


def test_skip_penalty(isolated_registry):
    r = isolated_registry
    e = {"id": "foo", "name": "foo", "trust": "official", "tags": ["react"]}
    [base] = r._rank_entries([e], "foo", ["react"])
    [pen] = r._rank_entries([e], "foo", ["react"], rejected={"foo"})
    assert pen["score"] == pytest.approx(base["score"] * 0.3, abs=1e-3)
    assert "previously rejected" in pen["flags"]
    assert "previously rejected" in r._why_line(pen)


def test_decision_index_from_registry(isolated_registry):
    r = isolated_registry
    reg = {"skills": [
        {"id": "a", "evaluation_history": [{"project": "p", "verdict": "skip"}]},
        {"id": "b", "evaluation_history": [{"project": "p", "verdict": "adopt"}]},
        {"id": "c", "evaluation_history": [{"project": "other", "verdict": "skip"}]},
        {"id": "d", "active_in_projects": ["p"], "evaluation_history": []},
    ]}
    rejected, installed = r._decision_index(reg, "p", ["e"])
    assert rejected == {"a"}
    assert installed == {"b", "d", "e"}


# ── --curate ─────────────────────────────────────────────────────────────────

def test_curate_excludes_installed_and_prints_why(online, tmp_path, capsys):
    online._test_responses["https://skills.sh/api/search"] = SH_RESPONSE
    proj = _project(tmp_path, "A react + next.js app.")
    online.cmd_add("react-performance", "React Performance",
                   "someone/repo", "npx skills add someone/repo --skill react-performance")
    online.cmd_eval("react-performance", "proj", "adopt", "using it")
    capsys.readouterr()
    rows = online.cmd_curate("react performance", proj, limit=5)
    ids = [row["entry"]["id"] for row in rows]
    assert "react-performance" not in ids
    assert "vercel-react-best-practices" in ids
    out = capsys.readouterr().out
    assert "why: " in out
    assert "skills.sh + catalog" in out
    assert "Scan before installing: registry.py --check <path>" in out
    assert " -g" not in out and " -y" not in out


def test_curate_shows_skills_sh_link(online, tmp_path, capsys):
    online._test_responses["https://skills.sh/api/search"] = SH_RESPONSE
    proj = _project(tmp_path, "A react app.")
    online.cmd_curate("react performance", proj, limit=10)
    out = capsys.readouterr().out
    assert "https://skills.sh/someone/repo/react-performance" in out
    assert "install: npx skills add someone/repo --skill react-performance" in out


def test_curate_offline_falls_back_to_catalog(isolated_registry, tmp_path, capsys):
    proj = _project(tmp_path, "A react app.")
    rows = isolated_registry.cmd_curate("react", proj, limit=3)
    assert rows and len(rows) <= 3
    assert "catalog only" in capsys.readouterr().out


def test_curate_flag_takes_new_path(isolated_registry, monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(isolated_registry, "cmd_curate",
                        lambda q, proj, limit, refresh: seen.update(q=q, limit=limit))
    monkeypatch.setattr(isolated_registry, "cmd_discover",
                        lambda *a, **k: seen.update(discover=True))
    monkeypatch.setattr(sys, "argv", ["registry.py", "--curate", "react performance",
                                      "--limit", "3", "--path", str(tmp_path)])
    isolated_registry.main()
    assert seen == {"q": "react performance", "limit": 3}


def test_find_is_still_discover_alias(isolated_registry, monkeypatch, tmp_path):
    seen = {}
    monkeypatch.setattr(isolated_registry, "cmd_curate",
                        lambda *a, **k: seen.update(curate=True))
    monkeypatch.setattr(isolated_registry, "cmd_discover",
                        lambda term, refresh, proj=None: seen.update(term=term))
    monkeypatch.setattr(sys, "argv", ["registry.py", "--find", "react",
                                      "--path", str(tmp_path)])
    isolated_registry.main()
    assert seen == {"term": "react"}


# ── partner audits ───────────────────────────────────────────────────────────

AUDIT = {"vercel-react-best-practices": {
    "ath": {"risk": "safe", "analyzedAt": "x"},
    "socket": {"risk": "safe", "alerts": 0, "score": 90, "analyzedAt": "x"},
    "snyk": {"risk": "low", "analyzedAt": "x"}}}


def test_partner_audits(online):
    online._test_responses["https://www.skills.sh/tele/audit"] = AUDIT
    lines = online._audit_lines("vercel-labs/agent-skills", "vercel-react-best-practices")
    assert "Gen: safe" in lines and "Socket: safe, 0 alerts" in lines
    assert "Snyk: low" in lines
    assert lines[-1] == "Details: https://skills.sh/vercel-labs/agent-skills/vercel-react-best-practices"
    url, _ = online._test_calls[0]
    assert "source=vercel-labs%2Fagent-skills" in url
    assert "skills=vercel-react-best-practices" in url


def test_export_eval_includes_audits(online, capsys):
    online._test_responses["https://www.skills.sh/tele/audit"] = AUDIT
    online.cmd_add("vercel-react-best-practices", "React BP", "vercel-labs/agent-skills",
                   "npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices")
    online.cmd_eval("vercel-react-best-practices", "p", "adopt", "good")
    assert "Third-party audits (advisory)" in capsys.readouterr().out
    online.cmd_export_eval("vercel-react-best-practices")
    out = capsys.readouterr().out
    assert "## Third-party audits (advisory)" in out
    assert "- Snyk: low" in out


# ── rival detection ──────────────────────────────────────────────────────────

def test_rival_flag(isolated_registry):
    r = isolated_registry
    assert r._rival_overlaps([{"id": "other"}], []) == []
    msgs = r._rival_overlaps([{"id": "find-skills"}], [])
    assert msgs and msgs[0].startswith("find-skills overlaps: Skills Curator covers search")
    assert r._rival_overlaps([], ["find-skills"]) == msgs


def test_audit_command_flags_find_skills(isolated_registry, capsys):
    isolated_registry.cmd_add("find-skills", "Find Skills", "vercel-labs/skills",
                              "npx skills add vercel-labs/skills --skill find-skills")
    isolated_registry.cmd_audit()
    out = capsys.readouterr().out
    assert "find-skills overlaps: Skills Curator covers search plus fit, safety and " \
           "persistence; keep one to avoid both triggering" in out


def test_query_scales_fit_so_weak_match_cannot_win_on_fit(isolated_registry):
    r = isolated_registry
    exact = {"id": "react-performance", "name": "react-performance", "trust": "unknown",
             "tags": [], "description": "", "installs": 2000}
    weak = {"id": "remotion", "name": "Remotion Best Practices", "trust": "high",
            "tags": ["react", "video", "animation"], "description": "", "installs": 0}
    ranked = r._rank_entries([weak, exact], "react performance", ["video", "animation", "remotion"])
    assert ranked[0]["entry"]["id"] == "react-performance"


def test_rival_flagged_in_ranking(isolated_registry):
    r = isolated_registry
    e = {"id": "find-skills", "name": "Find Skills", "trust": "official", "tags": []}
    [row] = r._rank_entries([e], "find skills", [])
    assert "overlaps Skills Curator" in row["flags"]
