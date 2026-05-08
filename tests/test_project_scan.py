"""Project scanner: language + framework + goal detection."""
from __future__ import annotations


def test_scan_detects_python_project(isolated_registry, tmp_path):
    (tmp_path / "main.py").write_text("print('hi')")
    (tmp_path / "lib.py").write_text("x = 1")
    (tmp_path / "requirements.txt").write_text("django\nfastapi\n")
    sig = isolated_registry._scan_project(tmp_path)
    assert "python" in sig["languages"]
    assert "django" in sig["tags"]
    assert "fastapi" in sig["tags"]
    assert "backend" in sig["tags"]


def test_scan_detects_react_via_package_json(isolated_registry, tmp_path):
    (tmp_path / "package.json").write_text('{"dependencies":{"react":"18","next":"14"}}')
    (tmp_path / "App.tsx").write_text("export default () => <div/>")
    sig = isolated_registry._scan_project(tmp_path)
    assert "react" in sig["tags"]
    assert "nextjs" in sig["tags"] or "next" in str(sig["tags"])


def test_scan_extracts_goals_from_readme(isolated_registry, tmp_path):
    (tmp_path / "README.md").write_text(
        "# My Project\n\nA web scraping pipeline that extracts data from JS-heavy pages."
    )
    sig = isolated_registry._scan_project(tmp_path)
    assert "scraping" in sig["tags"]


def test_scan_returns_empty_for_blank_dir(isolated_registry, tmp_path):
    sig = isolated_registry._scan_project(tmp_path)
    assert sig["languages"] == []
    assert sig["tags"] == []
