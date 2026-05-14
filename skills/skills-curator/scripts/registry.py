#!/usr/bin/env python3
"""
Skills Curator — registry.py (see VERSION constant for current version)
The only Claude skill tool with built-in judgment: evaluate before installing,
persist your decisions forever, get project-aware recommendations.

Install:
  npx skills add captkernel/Skills_Curator
  # or: git clone https://github.com/captkernel/Skills_Curator && bash install.sh

Usage:
  python registry.py                            # Status + help
  python registry.py --list [--type capability|preference]
  python registry.py --search <term>
  python registry.py --detect                   # Scan project for installed skills
  python registry.py --status                   # Project vs global view
  python registry.py --auto [--refresh]         # PROACTIVE: scans only on drift, surfaces top picks
  python registry.py --symptoms "slow tests"    # Map a complaint to skill categories
  python registry.py --recommend [--refresh]    # Project-aware recommendations (full output)
  python registry.py --discover [term]          # Search live catalog
  python registry.py --find [term]              # Alias for --discover
  python registry.py --scan                     # Project tech signals only
  python registry.py --check <path>             # Security scan a skill folder
  python registry.py --audit                    # Duplicate + conflict detection
  python registry.py --health                   # Skill health scores
  python registry.py --stale                    # Check for outdated installed skills
  python registry.py --migrate <agent>          # Copy skills to another agent
  python registry.py --author                   # Scaffold a new SKILL.md
  python registry.py --customize SOURCE         # Fork an external skill as a project-customized version
  python registry.py --validate [--strict]
  python registry.py --add ID NAME SOURCE INSTALL [--skill-type capability|preference]
  python registry.py --eval ID PROJECT VERDICT SUMMARY
                          [--pros "a,b,c"] [--cons "d,e"] [--conflicts "f"]
  python registry.py --history <skill-id>
  python registry.py --remove <skill-id>
  python registry.py --sync | --push            # Gist cross-device sync
  python registry.py --export

Environment variables:
  SKILLS_CURATOR_GIST_ID        Private GitHub Gist ID (cross-device sync)
  SKILLS_CURATOR_GITHUB_TOKEN   GitHub PAT with gist + repo scope
  SKILLS_SH_API_KEY             skills.sh API key (sk_live_...) for accurate install counts
  SKILLS_NO_TELEMETRY           Set to "1" to disable all outbound network calls

Requires Python 3.10+.
"""
from __future__ import annotations

import sys

# ─── Python version gate ──────────────────────────────────────────────────────
if sys.version_info < (3, 10):
    sys.stderr.write(
        "ERROR: Skills Curator requires Python 3.10 or newer. "
        f"You have {sys.version_info.major}.{sys.version_info.minor}.\n"
        "   Upgrade: https://www.python.org/downloads/\n"
    )
    sys.exit(1)

# ─── Force UTF-8 on stdout/stderr ──────────────────────────────────────────────
# Windows defaults to cp1252; without this, every emoji print() crashes.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import hashlib
import json
import os
import re
import argparse
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION = "4.5.0"
SCHEMA_VERSION = "3.0"

SKILL_DIR            = Path.home() / ".claude" / "skills" / "skills-curator"
SCRIPTS_DIR          = SKILL_DIR / "scripts"
REGISTRY_FILE        = SKILL_DIR / "registry.json"
CATALOG_FILE         = SKILL_DIR / "catalog.json"
RECOMMENDATIONS_FILE = SKILL_DIR / "recommendations.json"
AUTO_STATE_FILE      = SKILL_DIR / "auto_state.json"

GIST_ID            = os.environ.get("SKILLS_CURATOR_GIST_ID", "")
GITHUB_TOKEN       = os.environ.get("SKILLS_CURATOR_GITHUB_TOKEN", "")
SKILLS_SH_API_KEY  = os.environ.get("SKILLS_SH_API_KEY", "")
NO_TELEMETRY       = os.environ.get("SKILLS_NO_TELEMETRY", "") == "1"
GIST_FILENAME      = "registry.json"
CATALOG_TTL_HOURS  = 24

VALID_VERDICTS = ("adopt", "partial", "skip")
VALID_TYPES    = ("capability", "preference")

EMPTY_REGISTRY: dict = {"version": SCHEMA_VERSION, "last_updated": str(date.today()), "skills": []}

# ─── Agent skill directory paths ──────────────────────────────────────────────
# Catalog of every agent platform skills.sh ships an adapter for. Paths kept in
# sync with vercel-labs/skills (dist/cli.mjs). Each entry: display name, the
# global skills directory we'd install to, and a detection path whose existence
# means the agent is present on this machine. `aider` has no native skill
# system and is deliberately excluded. The cross-tool `agents` convention is
# kept as a synthetic destination for tools that read ~/.agents/skills.
HOME = Path.home()
_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", "")) if os.environ.get("XDG_CONFIG_HOME") else HOME / ".config"

PLATFORMS: dict[str, dict] = {
    # id: {display, dir (where SKILL.md goes), detect (path that signals presence)}
    "claude-code":     {"display": "Claude Code",      "dir": HOME / ".claude/skills",                    "detect": HOME / ".claude"},
    "github-copilot":  {"display": "GitHub Copilot",   "dir": HOME / ".copilot/skills",                   "detect": HOME / ".copilot"},
    "codex":           {"display": "Codex",            "dir": HOME / ".codex/skills",                     "detect": HOME / ".codex"},
    "cursor":          {"display": "Cursor",           "dir": HOME / ".cursor/skills",                    "detect": HOME / ".cursor"},
    "gemini-cli":      {"display": "Gemini CLI",       "dir": HOME / ".gemini/skills",                    "detect": HOME / ".gemini"},
    "cline":           {"display": "Cline",            "dir": HOME / ".cline/skills",                     "detect": HOME / ".cline"},
    "windsurf":        {"display": "Windsurf",         "dir": HOME / ".codeium/windsurf/skills",          "detect": HOME / ".codeium/windsurf"},
    "opencode":        {"display": "OpenCode",         "dir": _CONFIG_HOME / "opencode/skills",           "detect": _CONFIG_HOME / "opencode"},
    "amp":             {"display": "Amp",              "dir": _CONFIG_HOME / "agents/skills",             "detect": _CONFIG_HOME / "amp"},
    "antigravity":     {"display": "Antigravity",      "dir": HOME / ".gemini/antigravity/skills",        "detect": HOME / ".gemini/antigravity"},
    "aider-desk":      {"display": "AiderDesk",        "dir": HOME / ".aider-desk/skills",                "detect": HOME / ".aider-desk"},
    "augment":         {"display": "Augment",          "dir": HOME / ".augment/skills",                   "detect": HOME / ".augment"},
    "bob":             {"display": "IBM Bob",          "dir": HOME / ".bob/skills",                       "detect": HOME / ".bob"},
    "openclaw":        {"display": "OpenClaw",         "dir": HOME / ".openclaw/skills",                  "detect": HOME / ".openclaw"},
    "codearts-agent":  {"display": "CodeArts Agent",   "dir": HOME / ".codeartsdoer/skills",              "detect": HOME / ".codeartsdoer"},
    "codebuddy":       {"display": "CodeBuddy",        "dir": HOME / ".codebuddy/skills",                 "detect": HOME / ".codebuddy"},
    "codemaker":       {"display": "Codemaker",        "dir": HOME / ".codemaker/skills",                 "detect": HOME / ".codemaker"},
    "codestudio":      {"display": "Code Studio",      "dir": HOME / ".codestudio/skills",                "detect": HOME / ".codestudio"},
    "command-code":    {"display": "Command Code",     "dir": HOME / ".commandcode/skills",               "detect": HOME / ".commandcode"},
    "continue":        {"display": "Continue",         "dir": HOME / ".continue/skills",                  "detect": HOME / ".continue"},
    "cortex":          {"display": "Cortex Code",      "dir": HOME / ".snowflake/cortex/skills",          "detect": HOME / ".snowflake/cortex"},
    "crush":           {"display": "Crush",            "dir": HOME / ".config/crush/skills",              "detect": HOME / ".config/crush"},
    "deepagents":      {"display": "Deep Agents",      "dir": HOME / ".deepagents/agent/skills",          "detect": HOME / ".deepagents"},
    "devin":           {"display": "Devin",            "dir": _CONFIG_HOME / "devin/skills",              "detect": _CONFIG_HOME / "devin"},
    "dexto":           {"display": "Dexto",            "dir": HOME / ".agents/skills",                    "detect": HOME / ".dexto"},
    "droid":           {"display": "Droid",            "dir": HOME / ".factory/skills",                   "detect": HOME / ".factory"},
    "firebender":      {"display": "Firebender",       "dir": HOME / ".firebender/skills",                "detect": HOME / ".firebender"},
    "forgecode":       {"display": "ForgeCode",        "dir": HOME / ".forge/skills",                     "detect": HOME / ".forge"},
    "goose":           {"display": "Goose",            "dir": _CONFIG_HOME / "goose/skills",              "detect": _CONFIG_HOME / "goose"},
    "hermes-agent":    {"display": "Hermes Agent",     "dir": HOME / ".hermes/skills",                    "detect": HOME / ".hermes"},
    "junie":           {"display": "Junie",            "dir": HOME / ".junie/skills",                     "detect": HOME / ".junie"},
    "iflow-cli":       {"display": "iFlow CLI",        "dir": HOME / ".iflow/skills",                     "detect": HOME / ".iflow"},
    "kilo":            {"display": "Kilo Code",        "dir": HOME / ".kilocode/skills",                  "detect": HOME / ".kilocode"},
    "kimi-cli":        {"display": "Kimi Code CLI",    "dir": HOME / ".config/agents/skills",             "detect": HOME / ".kimi"},
    "kiro-cli":        {"display": "Kiro CLI",         "dir": HOME / ".kiro/skills",                      "detect": HOME / ".kiro"},
    "kode":            {"display": "Kode",             "dir": HOME / ".kode/skills",                      "detect": HOME / ".kode"},
    "mcpjam":          {"display": "MCPJam",           "dir": HOME / ".mcpjam/skills",                    "detect": HOME / ".mcpjam"},
    "mistral-vibe":    {"display": "Mistral Vibe",     "dir": HOME / ".vibe/skills",                      "detect": HOME / ".vibe"},
    "mux":             {"display": "Mux",              "dir": HOME / ".mux/skills",                       "detect": HOME / ".mux"},
    "openhands":       {"display": "OpenHands",        "dir": HOME / ".openhands/skills",                 "detect": HOME / ".openhands"},
    "pi":              {"display": "Pi",               "dir": HOME / ".pi/agent/skills",                  "detect": HOME / ".pi/agent"},
    "qoder":           {"display": "Qoder",            "dir": HOME / ".qoder/skills",                     "detect": HOME / ".qoder"},
    "qwen-code":       {"display": "Qwen Code",        "dir": HOME / ".qwen/skills",                      "detect": HOME / ".qwen"},
    "replit":          {"display": "Replit",           "dir": _CONFIG_HOME / "agents/skills",             "detect": HOME / ".replit"},
    "rovodev":         {"display": "Rovo Dev",         "dir": HOME / ".rovodev/skills",                   "detect": HOME / ".rovodev"},
    "roo":             {"display": "Roo Code",         "dir": HOME / ".roo/skills",                       "detect": HOME / ".roo"},
    "tabnine-cli":     {"display": "Tabnine CLI",      "dir": HOME / ".tabnine/agent/skills",             "detect": HOME / ".tabnine"},
    "trae":            {"display": "Trae",             "dir": HOME / ".trae/skills",                      "detect": HOME / ".trae"},
    "trae-cn":         {"display": "Trae CN",          "dir": HOME / ".trae-cn/skills",                   "detect": HOME / ".trae-cn"},
    "warp":            {"display": "Warp",             "dir": HOME / ".agents/skills",                    "detect": HOME / ".warp"},
    "zencoder":        {"display": "Zencoder",         "dir": HOME / ".zencoder/skills",                  "detect": HOME / ".zencoder"},
    "neovate":         {"display": "Neovate",          "dir": HOME / ".neovate/skills",                   "detect": HOME / ".neovate"},
    "pochi":           {"display": "Pochi",            "dir": HOME / ".pochi/skills",                     "detect": HOME / ".pochi"},
    "adal":            {"display": "AdaL",             "dir": HOME / ".adal/skills",                      "detect": HOME / ".adal"},
    "agents":          {"display": "Cross-tool ~/.agents/", "dir": HOME / ".agents/skills",               "detect": HOME / ".agents"},
}

# Backwards-compat: tests and older callers reference AGENT_PATHS as {id: Path}.
AGENT_PATHS = {pid: meta["dir"] for pid, meta in PLATFORMS.items()}

# Default install targets when the user hasn't specified — primary ecosystem.
DEFAULT_PLATFORMS = ["claude-code"]


def _detect_platforms() -> list[str]:
    """Return ids of platforms that appear installed on this machine."""
    return [pid for pid, meta in PLATFORMS.items() if meta["detect"].exists()]

# ─── Security scan patterns ───────────────────────────────────────────────────
# Lines below contain the literal trigger strings inside regex patterns; the
# `scanner:ignore` marker tells cmd_check() to skip these lines so the scanner
# does not flag its own pattern definitions as risks.
SECURITY_RISK_PATTERNS = [  # scanner:ignore-block-start
    (r'curl\s+.*\|\s*(bash|sh)',        "🔴 CRITICAL", "Remote code execution via curl pipe"),
    (r'wget\s+.*\|\s*(bash|sh)',        "🔴 CRITICAL", "Remote code execution via wget pipe"),
    (r'rm\s+-rf?\s+[/~]',               "🔴 CRITICAL", "Destructive recursive delete on root/home"),
    (r'\beval\s*\(',                    "🔴 CRITICAL", "Dynamic code execution call (CWE-95)"),
    (r'\bexec\s*\(',                    "🟠 HIGH",     "Code execution function call (CWE-95)"),
    (r'OPENAI_API_KEY\s*=\s*["\']sk-',  "🔴 CRITICAL", "Hardcoded OpenAI API key"),
    (r'ANTHROPIC_API_KEY\s*=\s*["\']sk-',"🔴 CRITICAL","Hardcoded Anthropic API key"),
    (r'ghp_[A-Za-z0-9]{36}',            "🔴 CRITICAL", "Hardcoded GitHub PAT"),
    (r'password\s*=\s*["\'][^"\']{6,}["\']',"🟠 HIGH", "Hardcoded password literal"),
    (r'https?://[^\s"\']+/exfil',       "🔴 CRITICAL", "Suspected data exfiltration endpoint"),
    (r'subprocess\.call\s*\(|os\.system\s*\(',"🟡 MEDIUM","Shell execution — review carefully"),
    (r'requests\.post.*secret',         "🟡 MEDIUM",   "HTTP POST with sensitive token — verify endpoint"),
    (r'__import__\s*\(',                "🟠 HIGH",     "Dynamic import — obfuscation risk"),
    (r'base64\.b64decode',              "🟡 MEDIUM",   "Base64 decode — check for obfuscated payload"),
    (r'keychain|credentials\s*store',   "🟡 MEDIUM",   "OS credential store access"),
]  # scanner:ignore-block-end

# ─── Health scoring weights ───────────────────────────────────────────────────
HEALTH_WEIGHTS = {
    "has_evaluation":    30,
    "security_reviewed": 20,
    "has_description":   10,
    "has_tags":          10,
    "has_source":        10,
    "has_install":       10,
    "has_compatibility":  5,
    "recent_eval":        5,  # eval within last 90 days
}


# ─── Registry I/O ─────────────────────────────────────────────────────────────

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return dict(EMPTY_REGISTRY)
    with open(REGISTRY_FILE, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("version", "1.0") < SCHEMA_VERSION:
        data = _migrate(data)
        save_registry(data)  # persist migration once, not on every load
    return data


def save_registry(registry: dict) -> None:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    registry["last_updated"] = str(date.today())
    registry["version"] = SCHEMA_VERSION
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def _migrate(old: dict) -> dict:
    ver = old.get("version", "1.0")
    for s in old.get("skills", []):
        # v1 → v2
        s.setdefault("type", "capability")
        s.setdefault("compatibility", [])
        s.setdefault("security_reviewed", False)
        for e in s.get("evaluation_history", []):
            e.setdefault("skill_type", s.get("type", "capability"))
            e.setdefault("adoption_plan", {"adopt": [], "skip": [], "pairs_with": []})
            e.setdefault("security_notes", [])
        # v2 → v3
        s.setdefault("installed_version", None)
        s.setdefault("pairs_with", [])
        s.setdefault("security_scan", None)
    old["version"] = SCHEMA_VERSION
    print(f"⬆️  Registry migrated v{ver} → {SCHEMA_VERSION}")
    return old


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def _http_get(url: str, headers: dict | None = None, timeout: int = 8) -> str | None:
    """Best-effort GET. Respects SKILLS_NO_TELEMETRY. Returns text or None."""
    if NO_TELEMETRY:
        return None
    h = {"User-Agent": f"skills-curator/{VERSION}"}
    if headers:
        h.update(headers)
    try:
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return None


# ─── Gist Sync ────────────────────────────────────────────────────────────────

def _gist_req(method: str, data: dict | None = None) -> dict | None:
    if not (GIST_ID and GITHUB_TOKEN):
        print("❌ Set SKILLS_CURATOR_GIST_ID + SKILLS_CURATOR_GITHUB_TOKEN to enable sync.")
        return None
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": f"skills-curator/{VERSION}",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        codes = {401: "Check your token has gist scope.", 404: "Check your GIST_ID."}
        print(f"⚠️  Gist {method} failed: HTTP {e.code}. {codes.get(e.code, '')}")
    except Exception as e:
        print(f"⚠️  Gist error: {e}")
    return None


def gist_pull() -> dict | None:
    r = _gist_req("GET")
    if r and GIST_FILENAME in r.get("files", {}):
        try:
            reg = json.loads(r["files"][GIST_FILENAME]["content"])
            SKILL_DIR.mkdir(parents=True, exist_ok=True)
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(reg, f, indent=2)
            print(f"✅ Pulled from Gist — {len(reg.get('skills', []))} skill(s)")
            return reg
        except Exception:
            print("⚠️  Gist content is not valid JSON.")
    return None


def gist_push(registry: dict) -> None:
    data = {"files": {GIST_FILENAME: {"content": json.dumps(registry, indent=2)}}}
    if _gist_req("PATCH", data):
        print(f"☁️  Pushed to Gist: https://gist.github.com/{GIST_ID}")
    else:
        print("⚠️  Gist push failed — saved locally only.")


# ─── Core Registry Operations ─────────────────────────────────────────────────

def cmd_init() -> None:
    registry = load_registry()
    n = len(registry.get("skills", []))
    if not REGISTRY_FILE.exists():
        save_registry(registry)
        print(f"📋 Registry created at {REGISTRY_FILE}")
    else:
        print(f"📋 Skills Curator v{VERSION}  ·  {n} skill(s) registered")
        print(f"   Updated  : {registry.get('last_updated', '?')}")
        print(f"   Gist sync: {'✅ enabled' if GIST_ID else '⬜ disabled'}")
        print(f"   Telemetry: {'⬜ disabled (SKILLS_NO_TELEMETRY=1)' if NO_TELEMETRY else '✅ enabled'}")
    print()
    print(f"  Registry  : --list  --search  --detect  --status  --validate")
    print(f"  Intel     : --auto  --symptoms \"<phrase>\"")
    print(f"  Discovery : --recommend  --discover [term]  --scan")
    print(f"  Safety    : --check <path>  --audit  --health  --stale")
    print(f"  Platforms : --platforms [--verbose]  --migrate [target[,...]]")
    print(f"  Authoring : --author  --customize <source>")
    print(f"  Sync      : --sync  --push")
    print(f"  Run --help for all options")


def cmd_list(skill_type: str | None = None) -> None:
    registry = load_registry()
    skills = [s for s in registry.get("skills", []) if not skill_type or s.get("type") == skill_type]
    if not skills:
        suffix = f" of type {skill_type}" if skill_type else ""
        print(f"📭 No skills registered{suffix}.")
        return

    groups: dict[str, list] = {"adopt": [], "partial": [], "skip": [], "unevaluated": []}
    for s in skills:
        ev = s.get("evaluation_history", [])
        verdict = ev[-1]["verdict"] if ev else "unevaluated"
        groups.setdefault(verdict, groups["unevaluated"]).append(s)

    icons = {"adopt": "✅", "partial": "🟡", "skip": "❌", "unevaluated": "⬜"}
    type_icons = {"capability": "⚡", "preference": "🎨"}

    print(f"\n{'═' * 60}")
    print(f"  REGISTRY v{SCHEMA_VERSION}  ·  {len(skills)} skill(s)")
    print(f"{'═' * 60}")

    for verdict, group in groups.items():
        if not group:
            continue
        print(f"\n  {icons[verdict]} {verdict.upper()}")
        for s in group:
            ev = s.get("evaluation_history", [])
            t = type_icons.get(s.get("type", "capability"), "⚡")
            sr = "🔒" if s.get("security_reviewed") else "⚠️ "
            print(f"\n  {t} {s['name']}  [{s['id']}]  {sr}")
            print(f"     Source  : {s.get('source', '?')}")
            print(f"     Install : {s.get('install_command', '?')}")
            if s.get("active_in_projects"):
                print(f"     Projects: {', '.join(s['active_in_projects'])}")
            if ev:
                last = ev[-1]
                print(f"     Eval    : [{last['verdict'].upper()}] {last['project']} "
                      f"({last['date']}) — {last['summary']}")
    print()


def cmd_search(term: str) -> None:
    registry = load_registry()
    tl = term.lower()
    results = [
        s for s in registry.get("skills", [])
        if tl in " ".join(
            [s.get(k, "") for k in ("id", "name", "description")]
            + s.get("tags", [])
        ).lower()
    ]
    print(f"\n🔍 '{term}' — {len(results)} result(s)\n")
    for s in results:
        ev = s.get("evaluation_history", [])
        icon = {"adopt": "✅", "partial": "🟡", "skip": "❌"}.get(
            ev[-1]["verdict"] if ev else "", "⬜"
        )
        print(f"  {icon} {s['name']}  [{s['id']}]  — {s.get('description', '')[:70]}")
        print(f"     {s.get('install_command', '?')}")


def cmd_detect(project_dir: Path | None = None) -> None:
    project_dir = project_dir or Path.cwd()
    project_name = project_dir.name
    registry = load_registry()
    existing = {s["id"]: s for s in registry["skills"]}
    found: list[str] = []

    skills_dir = project_dir / ".claude" / "skills"
    if skills_dir.exists():
        for d in skills_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                found.append(d.name)

    for doc in ["CLAUDE.md", ".claude/CLAUDE.md", "README.md"]:
        p = project_dir / doc
        if p.exists():
            content = p.read_text(errors="ignore").lower()
            for sid, skill in existing.items():
                if sid in content or skill["name"].lower() in content:
                    if sid not in found:
                        found.append(sid)

    print(f"\n🔍 {project_name}: {', '.join(found) if found else 'no skills found'}\n")
    for sid in found:
        if sid not in existing:
            registry["skills"].append({
                "id": sid, "name": sid.replace("-", " ").title(), "type": "capability",
                "source": "auto-detected", "install_command": "unknown",
                "description": "", "tags": [], "compatibility": [],
                "security_reviewed": False, "security_scan": None,
                "installed_version": None, "pairs_with": [],
                "date_added": str(date.today()), "active_in_projects": [project_name],
                "evaluation_history": [],
            })
            print(f"   ➕ Registered: {sid}")
        else:
            skill = existing[sid]
            if project_name not in skill.get("active_in_projects", []):
                skill["active_in_projects"].append(project_name)
                print(f"   🔗 Linked: {sid}")
    save_registry(registry)


def cmd_status(project_dir: Path | None = None) -> None:
    project_dir = project_dir or Path.cwd()
    name = project_dir.name
    registry = load_registry()
    active   = [s for s in registry["skills"] if name in s.get("active_in_projects", [])]
    inactive = [s for s in registry["skills"] if name not in s.get("active_in_projects", [])]
    print(f"\n📁 {name}")
    print(f"  Active ({len(active)}): {', '.join(s['id'] for s in active) or 'none'}")
    print(f"  Available ({len(inactive)}): {', '.join(s['id'] for s in inactive) or 'none'}")


def cmd_add(skill_id: str, name: str, source: str, install: str,
            skill_type: str = "capability") -> None:
    if skill_type not in VALID_TYPES:
        print(f"❌ --skill-type must be: {' | '.join(VALID_TYPES)}")
        return
    registry = load_registry()
    if any(s["id"] == skill_id for s in registry["skills"]):
        print(f"⚠️  '{skill_id}' already registered.")
        return
    registry["skills"].append({
        "id": skill_id, "name": name, "type": skill_type,
        "source": source, "install_command": install, "description": "",
        "tags": [], "compatibility": [], "security_reviewed": False,
        "security_scan": None, "installed_version": None, "pairs_with": [],
        "date_added": str(date.today()), "active_in_projects": [],
        "evaluation_history": [],
    })
    save_registry(registry)
    print(f"✅ Registered [{skill_type}]: {name}  [{skill_id}]")
    print(f"   💡 Run --check <path> to security-scan before using")


def cmd_remove(skill_id: str) -> None:
    registry = load_registry()
    before = len(registry["skills"])
    registry["skills"] = [s for s in registry["skills"] if s["id"] != skill_id]
    if len(registry["skills"]) < before:
        save_registry(registry)
        print(f"🗑️  Removed: {skill_id}")
    else:
        print(f"❌ Not found: {skill_id}")


def _split_csv(s: str | None) -> list[str]:
    """Parse comma-separated CLI value into a clean list."""
    if not s:
        return []
    return [item.strip() for item in s.split(",") if item.strip()]


def cmd_eval(skill_id: str, project: str, verdict: str, summary: str,
             pros: list[str] | None = None,
             cons: list[str] | None = None,
             conflicts: list[str] | None = None) -> None:
    verdict = verdict.lower()
    if verdict not in VALID_VERDICTS:
        print(f"❌ verdict: {' | '.join(VALID_VERDICTS)}")
        return
    registry = load_registry()
    for s in registry["skills"]:
        if s["id"] == skill_id:
            s.setdefault("evaluation_history", []).append({
                "date": str(date.today()), "project": project,
                "verdict": verdict, "skill_type": s.get("type", "capability"),
                "summary": summary,
                "pros": pros or [], "cons": cons or [],
                "conflicts": conflicts or [],
                "adoption_plan": {"adopt": [], "skip": [], "pairs_with": []},
                "security_notes": [],
            })
            save_registry(registry)
            print(f"✅ Evaluation saved: {skill_id} in {project} → {verdict.upper()}")
            if pros:      print(f"   pros     : {len(pros)}")
            if cons:      print(f"   cons     : {len(cons)}")
            if conflicts: print(f"   conflicts: {len(conflicts)}")
            return
    print(f"❌ Skill '{skill_id}' not found.")


def cmd_history(skill_id: str) -> None:
    registry = load_registry()
    for s in registry["skills"]:
        if s["id"] == skill_id:
            ev = s.get("evaluation_history", [])
            print(f"\n📋 {s['name']} — {len(ev)} evaluation(s)")
            for i, e in enumerate(ev, 1):
                icon = {"adopt": "✅", "partial": "🟡", "skip": "❌"}.get(e["verdict"], "⬜")
                print(f"\n  {i}. {icon} {e['verdict'].upper()}  ·  {e['project']}  ·  {e['date']}")
                print(f"     {e['summary']}")
                if e.get("pros"):       print(f"     ✅ pros     : {'; '.join(e['pros'])}")
                if e.get("cons"):       print(f"     ⚠️  cons     : {'; '.join(e['cons'])}")
                if e.get("conflicts"):  print(f"     🔴 conflicts: {'; '.join(e['conflicts'])}")
                ap = e.get("adoption_plan", {})
                if ap and any(ap.values()):
                    if ap.get("adopt"):       print(f"     📦 adopt    : {', '.join(ap['adopt'])}")
                    if ap.get("skip"):        print(f"     ⏭️  skip     : {', '.join(ap['skip'])}")
                    if ap.get("pairs_with"):  print(f"     🔗 pairs    : {', '.join(ap['pairs_with'])}")
                if e.get("security_notes"):
                    print(f"     🔒 security : {'; '.join(e['security_notes'])}")
            return
    print(f"❌ Not found: {skill_id}")


def cmd_export_eval(skill_id: str) -> None:
    """Emit the latest evaluation as a shareable markdown artifact.

    The point: turn your private decision into something you can paste in a
    PR comment, an ADR, or a team doc. Other tools install skills; this one
    produces evidence that the install was deliberate.
    """
    registry = load_registry()
    skill = next((s for s in registry["skills"] if s["id"] == skill_id), None)
    if skill is None:
        print(f"❌ Skill '{skill_id}' not found.")
        return
    evals = skill.get("evaluation_history", [])
    if not evals:
        print(f"❌ No evaluations recorded for '{skill_id}'. "
              f"Run --eval first.")
        return

    e = evals[-1]
    type_label = {"capability": "Capability Uplift",
                  "preference": "Encoded Preference"}.get(
        e.get("skill_type", skill.get("type", "capability")), "—")
    verdict_icon = {"adopt": "✅", "partial": "🟡", "skip": "❌"}.get(e["verdict"], "⬜")

    lines: list[str] = []
    lines.append(f"# Skill Evaluation: {skill['name']}")
    lines.append("")
    lines.append(f"- **Skill:** [`{skill['id']}`]({skill.get('source', '')})")
    lines.append(f"- **Project:** {e['project']}")
    lines.append(f"- **Date:** {e['date']}")
    lines.append(f"- **Type:** {type_label}")
    lines.append(f"- **Verdict:** {verdict_icon} **{e['verdict'].upper()}**")
    if skill.get("install_command"):
        lines.append(f"- **Install:** `{skill['install_command']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(e.get("summary", ""))
    lines.append("")

    if e.get("pros"):
        lines.append("## ✅ Pros")
        for p in e["pros"]:
            lines.append(f"- {p}")
        lines.append("")
    if e.get("cons"):
        lines.append("## ⚠️ Cons")
        for c in e["cons"]:
            lines.append(f"- {c}")
        lines.append("")
    if e.get("conflicts"):
        lines.append("## 🔴 Conflicts")
        for c in e["conflicts"]:
            lines.append(f"- {c}")
        lines.append("")
    ap = e.get("adoption_plan") or {}
    if any(ap.values()) if isinstance(ap, dict) else False:
        lines.append("## 📦 Adoption Plan")
        if ap.get("adopt"):
            lines.append(f"- **Adopt:** {', '.join(ap['adopt'])}")
        if ap.get("skip"):
            lines.append(f"- **Skip:** {', '.join(ap['skip'])}")
        if ap.get("pairs_with"):
            lines.append(f"- **Pairs with:** {', '.join(ap['pairs_with'])}")
        lines.append("")

    scan = skill.get("security_scan")
    if scan:
        result = scan.get("result", "?")
        date_str = scan.get("date", "?")
        lines.append("## 🔒 Security")
        if scan.get("findings"):
            lines.append(f"- Scanned {date_str} — **{result}**")
            for f in scan["findings"]:
                lines.append(f"  - {f.get('severity', '?')} {f.get('description', '')} "
                             f"(`{f.get('file', '?')}`)")
        else:
            lines.append(f"- Scanned {date_str} — **{result}**, no findings")
        lines.append("")
    elif skill.get("security_reviewed"):
        lines.append("## 🔒 Security")
        lines.append("- Marked as security-reviewed in registry")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"> Evaluated using "
                 f"[Skills Curator](https://github.com/captkernel/Skills_Curator) "
                 f"v{VERSION}.")
    lines.append(f"> Reproduce: "
                 f"`npx skills add captkernel/Skills_Curator`")
    lines.append("")
    print("\n".join(lines))


def cmd_validate(strict: bool = False) -> None:
    registry = load_registry()
    skills = registry.get("skills", [])
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for s in skills:
        sid = s.get("id", "")
        if not sid:                 errors.append("Skill missing 'id'")
        elif sid in seen:           errors.append(f"Duplicate id: {sid}")
        seen.add(sid)
        if not s.get("name"):       errors.append(f"[{sid}] Missing name")
        if not s.get("install_command"): warnings.append(f"[{sid}] Missing install_command")
        if s.get("type") not in VALID_TYPES:
            warnings.append(f"[{sid}] Unknown type '{s.get('type')}'")
        if not s.get("security_reviewed"):
            warnings.append(f"[{sid}] Not security_reviewed")
        for e in s.get("evaluation_history", []):
            if e.get("verdict") not in VALID_VERDICTS:
                errors.append(f"[{sid}] Bad verdict: {e.get('verdict')}")
        if strict:
            if not s.get("tags"):
                warnings.append(f"[{sid}] No tags (--strict)")
            if not s.get("evaluation_history"):
                warnings.append(f"[{sid}] No evaluations (--strict)")

    print(f"\n{'═' * 50}")
    print(f"  Registry Validator  ·  {len(skills)} skill(s)")
    print(f"{'═' * 50}")
    print(f"  {'✅ No errors' if not errors else f'❌ {len(errors)} error(s):'}")
    for e in errors:
        print(f"     {e}")
    print(f"  {'✅ No warnings' if not warnings else f'⚠️  {len(warnings)} warning(s):'}")
    for w in warnings:
        print(f"     {w}")
    print(f"\n  Result: {'PASS' if not errors else 'FAIL'}\n")
    sys.exit(0 if not errors else 3)


# ─── Discovery & Recommendations ──────────────────────────────────────────────

# Built-in seed catalog. weekly_installs is None by default — populated live from
# skills.sh when network is available. Trust + tags are the durable matching signal.
KNOWN_SKILLS: list[dict] = [
    {"id": "find-skills", "name": "Find Skills", "source": "vercel-labs/skills",
     "type": "capability", "trust": "official",
     "install": "npx skills add vercel-labs/skills --skill find-skills",
     "tags": ["meta", "discovery", "skill-management"],
     "description": "Discovers and recommends skills from skills.sh based on task context.",
     "pros": ["Official Vercel maintenance", "Wraps skills.sh discovery in one verb"],
     "cons": ["Popularity-driven; doesn't filter by project fit", "Overlaps with Skills Curator's --recommend"]},
    {"id": "frontend-design", "name": "Frontend Design", "source": "anthropics/skills",
     "type": "preference", "trust": "official",
     "install": "npx skills add anthropics/skills --skill frontend-design",
     "tags": ["frontend", "design", "react", "css", "html", "ui", "vue"],
     "description": "Bold design philosophy before writing UI code. Prevents AI-slop aesthetics.",
     "pros": ["Anthropic-curated", "Prevents generic-looking UI defaults", "Stack-agnostic principles"],
     "cons": ["Strong opinions may conflict with team style guide", "Adds prompt overhead on non-UI tasks"]},
    {"id": "document-skills", "name": "Document Skills", "source": "anthropics/skills",
     "type": "capability", "trust": "official",
     "install": "npx skills add anthropics/skills --skill document-skills",
     "tags": ["documents", "pdf", "word", "excel", "powerpoint", "docx", "xlsx"],
     "description": "Create and edit PDFs, Word docs, Excel sheets, and presentations.",
     "pros": ["Covers all major office formats", "First-party Anthropic skill"],
     "cons": ["Useless if your project never produces office files", "Bundles 5 sub-skills you may not need"]},
    {"id": "skill-creator", "name": "Skill Creator", "source": "anthropics/skills",
     "type": "capability", "trust": "official",
     "install": "npx skills add anthropics/skills --skill skill-creator",
     "tags": ["meta", "skill-development", "authoring"],
     "description": "Interactive skill authoring. Creates properly structured SKILL.md files.",
     "pros": ["Produces canonically-formatted SKILL.md", "Reduces friction for first-time authors"],
     "cons": ["Overlaps with Skills Curator's --author", "Adds context cost when not authoring"]},
    {"id": "vercel-react-best-practices", "name": "React Best Practices",
     "source": "vercel-labs/agent-skills", "type": "preference", "trust": "high",
     "install": "npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices",
     "tags": ["react", "nextjs", "frontend", "performance", "typescript"],
     "description": "React/Next.js performance rules ordered by impact.",
     "pros": ["Vercel-authored", "Impact-ranked rules", "Next.js-aware"],
     "cons": ["Next.js-biased examples (less useful for plain React)", "Doesn't cover SSR alternatives"]},
    {"id": "web-design-guidelines", "name": "Web Design Guidelines",
     "source": "vercel-labs/agent-skills", "type": "preference", "trust": "high",
     "install": "npx skills add vercel-labs/agent-skills --skill web-design-guidelines",
     "tags": ["frontend", "design", "accessibility", "ux", "css", "web"],
     "description": "UI/UX rules: accessibility, typography, dark mode. Validates against Vercel standards.",
     "pros": ["Accessibility-first", "Specific, validatable rules"],
     "cons": ["Heavy overlap with frontend-design", "Vercel design language may not match your brand"]},
    {"id": "agent-browser", "name": "Agent Browser", "source": "vercel-labs/agent-browser",
     "type": "capability", "trust": "high",
     "install": "npx skills add vercel-labs/agent-browser --skill agent-browser",
     "tags": ["browser", "automation", "scraping", "cdp", "testing", "forms"],
     "description": "Browser automation via CDP. Element refs, 6 auth methods, screenshots, form filling.",
     "pros": ["Six auth methods including session import", "CDP gives access to JS-heavy pages"],
     "cons": ["Requires Chrome — adds CI dependency", "Heavyweight for static-page scraping"]},
    {"id": "supermemory", "name": "Supermemory", "source": "supermemoryai/supermemory",
     "type": "capability", "trust": "high",
     "install": "npx skills add supermemoryai/supermemory",
     "tags": ["memory", "personalization", "context", "recall", "ai"],
     "description": "Persistent memory across sessions. Tracks facts, resolves contradictions.",
     "pros": ["Cross-session persistence", "Conflict resolution built-in"],
     "cons": ["Sends context to a third-party service", "Privacy review required for sensitive projects"]},
    {"id": "remotion-best-practices", "name": "Remotion Best Practices",
     "source": "remotion-dev/skills", "type": "preference", "trust": "high",
     "install": "npx skills add remotion-dev/skills --skill remotion-best-practices",
     "tags": ["remotion", "video", "animation", "react", "programmatic-video"],
     "description": "Remotion knowledge: animations, timing, audio, captions, 3D. Auto-activates on Remotion code.",
     "pros": ["First-party Remotion knowledge", "Activates automatically on Remotion files"],
     "cons": ["Useless if you don't use Remotion", "Adds context cost on every session"]},
    {"id": "firecrawl-cli", "name": "Firecrawl CLI", "source": "firecrawl/cli",
     "type": "capability", "trust": "high",
     "install": "npx skills add firecrawl/cli",
     "tags": ["scraping", "web", "crawl", "data-extraction", "js-rendering"],
     "description": "Web scraping with JS rendering. Handles SPAs, auth-gated pages, structured extraction.",
     "pros": ["Handles JS-heavy SPAs out of the box", "Structured-extraction primitives"],
     "cons": ["Requires Firecrawl API key", "Paid tier for any meaningful usage"]},
    {"id": "openspace", "name": "OpenSpace", "source": "HKUDS/OpenSpace",
     "type": "capability", "trust": "medium",
     "install": "pip install git+https://github.com/HKUDS/OpenSpace.git",
     "tags": ["meta", "self-evolving", "mcp", "token-efficiency"],
     "description": "Self-evolving skills via MCP. Auto-fix, learn from execution.",
     "pros": ["Token-efficient", "Self-improving over usage"],
     "cons": ["Requires MCP setup", "Research-grade — interface may shift"]},
    {"id": "writing-plans", "name": "Writing Plans", "source": "obra/superpowers",
     "type": "preference", "trust": "medium",
     "install": "npx skills add obra/superpowers --skill writing-plans",
     "tags": ["workflow", "planning", "discipline", "process"],
     "description": "Plan-before-code discipline. Reduces agents skipping steps.",
     "pros": ["Reduces 'jumped to coding' failures", "Forces explicit alignment before edits"],
     "cons": ["Adds friction for trivial one-liner tasks", "Verbose for simple bug fixes"]},
    {"id": "verification-before-completion", "name": "Verification Before Completion",
     "source": "obra/superpowers", "type": "preference", "trust": "medium",
     "install": "npx skills add obra/superpowers --skill verification-before-completion",
     "tags": ["workflow", "verification", "quality", "testing"],
     "description": "Verify-before-done discipline. Stops agents marking tasks complete without checking.",
     "pros": ["Catches false-success claims", "Pairs naturally with TDD"],
     "cons": ["Requires verification commands to actually exist", "Slows iteration when verification is expensive"]},
    {"id": "composio-connect", "name": "Composio Connect",
     "source": "ComposioHQ/composio-skills", "type": "capability", "trust": "high",
     "install": "npx skills add ComposioHQ/composio-skills --skill connect",
     "tags": ["integrations", "api", "gmail", "slack", "github", "notion"],
     "description": "Connect Claude to SaaS apps with managed OAuth.",
     "pros": ["Managed OAuth removes credential plumbing", "100+ integrations"],
     "cons": ["Vendor lock-in to Composio", "Routes data through their proxy"]},
    {"id": "security-auditor", "name": "Security Auditor",
     "source": "alirezarezvani/claude-skills", "type": "capability", "trust": "medium",
     "install": "npx skills add alirezarezvani/claude-skills --skill security-auditor",
     "tags": ["security", "audit", "vulnerability", "owasp", "code-review"],
     "description": "Security audit skill. Scans for OWASP top 10, injection vectors, exposed secrets.",
     "pros": ["OWASP-mapped", "Catches obvious vulnerability patterns"],
     "cons": ["Pattern-based — misses logic-level issues", "Community-maintained, smaller maintainer pool"]},
    {"id": "git-commit-writer", "name": "Git Commit Writer",
     "source": "glebis/claude-skills", "type": "preference", "trust": "medium",
     "install": "npx skills add glebis/claude-skills --skill git-commit-writer",
     "tags": ["git", "commits", "workflow", "conventional-commits"],
     "description": "Enforces conventional commit message format.",
     "pros": ["Consistent commit history", "Plays well with semantic-release"],
     "cons": ["Convention may not match team's existing style", "Wasteful if you already have commitlint"]},
    {"id": "senior-backend", "name": "Senior Backend",
     "source": "davila7/claude-code-templates", "type": "preference", "trust": "medium",
     "install": "npx skills add davila7/claude-code-templates --skill senior-backend",
     "tags": ["backend", "api", "python", "nodejs", "go", "typescript", "database"],
     "description": "Senior backend patterns: API scaffolding, DB optimisation, load testing.",
     "pros": ["Multi-language coverage", "Includes load-testing patterns"],
     "cons": ["Generic — may not match your stack's idioms", "Adopting all 4 languages bloats prompt"]},
    {"id": "vercel-react-native-skills", "name": "React Native Skills",
     "source": "vercel-labs/agent-skills", "type": "preference", "trust": "high",
     "install": "npx skills add vercel-labs/agent-skills --skill vercel-react-native-skills",
     "tags": ["react-native", "mobile", "ios", "android", "expo"],
     "description": "React Native best practices: Expo patterns, performance, platform handling.",
     "pros": ["Expo-aware", "Platform-handling guidance for iOS/Android divergence"],
     "cons": ["Expo-biased; less useful for bare React Native", "No Fabric/Hermes guidance yet"]},
    {"id": "mcp-builder", "name": "MCP Builder",
     "source": "ComposioHQ/awesome-claude-skills", "type": "capability", "trust": "medium",
     "install": "npx skills add ComposioHQ/awesome-claude-skills --skill mcp-builder",
     "tags": ["mcp", "integration", "api", "tools", "typescript", "python"],
     "description": "Guides creation of high-quality MCP servers for integrating external APIs.",
     "pros": ["Tightens MCP server quality", "TypeScript + Python coverage"],
     "cons": ["Only useful when authoring an MCP server", "Heavy overlap with Anthropic MCP docs"]},
]

FRAMEWORK_SIGNALS = {
    "next": ["nextjs", "react", "frontend"], "react": ["react", "frontend"],
    "vue": ["vue", "frontend"], "svelte": ["svelte", "frontend"],
    "nuxt": ["nuxt", "vue", "frontend"], "remix": ["remix", "react", "frontend"],
    "express": ["express", "nodejs", "backend", "api"], "fastify": ["fastify", "backend", "api"],
    "nestjs": ["nestjs", "backend", "api"], "vite": ["vite", "frontend"],
    "tailwind": ["tailwind", "css", "frontend"], "prisma": ["prisma", "database", "orm"],
    "playwright": ["playwright", "testing", "browser"], "jest": ["jest", "testing"],
    "vitest": ["vitest", "testing"], "django": ["django", "python", "backend", "web"],
    "fastapi": ["fastapi", "python", "backend", "api"], "flask": ["flask", "python", "web"],
    "langchain": ["langchain", "ai", "llm"], "openai": ["openai", "ai", "llm"],
    "anthropic": ["anthropic", "claude", "ai", "llm"], "pandas": ["pandas", "data-science"],
    "torch": ["pytorch", "ml", "deep-learning"], "stripe": ["stripe", "payments"],
    "postgres": ["postgresql", "database"], "mongodb": ["mongodb", "database", "nosql"],
    "redis": ["redis", "cache"], "supabase": ["supabase", "database"],
    "aws": ["aws", "cloud"], "gcp": ["gcp", "cloud"], "azure": ["azure", "cloud"],
    "remotion": ["remotion", "video", "animation"], "expo": ["expo", "react-native", "mobile"],
}

GOAL_SIGNALS = {
    r"\bscrape\b|\bscraping\b|\bcrawl\b": ["scraping", "web-automation"],
    r"\btest\b|\btesting\b|\be2e\b": ["testing"],
    r"\bapi\b|\brest\b|\bgraphql\b": ["api"],
    r"\bdashboard\b|\badmin\b|\bcms\b": ["dashboard", "frontend"],
    r"\bpdf\b|\bdocument\b|\breport\b": ["documents", "pdf"],
    r"\bauth\b|\blogin\b|\bsession\b": ["auth"],
    r"\bdeploy\b|\bci\b|\bcd\b": ["devops"],
    r"\binstagram\b|\btwitter\b|\bsocial\b": ["social-media", "automation"],
    r"\bsecurity\b|\baudit\b|\bpentest\b": ["security"],
    r"\bdata\b|\banalytics\b": ["data", "analytics"],
    r"\bgit\b|\bcommit\b|\bpull request\b": ["git"],
    r"\bvideo\b|\banimation\b|\bremotio\b": ["video", "animation", "remotion"],
    r"\bmobile\b|\bios\b|\bandroid\b": ["mobile"],
    r"\bml\b|\bmachine learning\b|\bmodel\b": ["ml", "ai"],
    r"\bmemory\b|\bpersonaliz\b|\brecall\b": ["memory", "personalization"],
}


def _scan_project(project_dir: Path) -> dict:
    signals: dict = {"languages": [], "tags": set()}
    seen: set[str] = signals["tags"]

    def add(*tags: str) -> None:
        for t in tags:
            seen.add(t)

    lang_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
                ".tsx": "react", ".jsx": "react", ".go": "go", ".rs": "rust",
                ".java": "java", ".rb": "ruby"}
    lang_counts: dict[str, int] = {}
    for ext, lang in lang_map.items():
        try:
            c = sum(1 for _ in project_dir.rglob(f"*{ext}"))
        except Exception:
            c = 0
        if c:
            lang_counts[lang] = lang_counts.get(lang, 0) + c
    for lang in sorted(lang_counts, key=lambda x: -lang_counts[x]):
        signals["languages"].append(lang)
        add(lang)

    for fname in ["package.json", "requirements.txt", "pyproject.toml", "Pipfile"]:
        fp = project_dir / fname
        if fp.exists():
            content = fp.read_text(errors="ignore").lower()
            for pat, tags in FRAMEWORK_SIGNALS.items():
                if pat in content:
                    add(*tags)

    for doc in ["CLAUDE.md", ".claude/CLAUDE.md", "README.md", "README.mdx"]:
        fp = project_dir / doc
        if fp.exists():
            content = fp.read_text(errors="ignore")[:4000].lower()
            for pat, tags in FRAMEWORK_SIGNALS.items():
                if pat in content:
                    add(*tags)
            for pat, tags in GOAL_SIGNALS.items():
                if re.search(pat, content):
                    add(*tags)

    skills_found: list[str] = []
    for sd in [project_dir / ".claude" / "skills", Path.home() / ".claude" / "skills"]:
        if sd.exists():
            for d in sd.iterdir():
                if d.is_dir() and (d / "SKILL.md").exists():
                    skills_found.append(d.name)
    signals["existing_skills"] = skills_found
    signals["tags"] = list(seen)
    return signals


# GitHub topic queries used to surface community-maintained skills. We
# deliberately keep this list narrow — broader queries return too much noise
# (every PoC repo tagged "claude"). Trust tier is auto-classified by author.
_GITHUB_SKILL_TOPICS = ["claude-skill", "claude-code-skill", "agent-skill"]
_TRUSTED_AUTHORS = {
    "anthropics":   "official",
    "anthropic":    "official",
    "vercel-labs":  "official",
    "vercel":       "official",
    "microsoft":    "official",
    "google":       "official",
    "ComposioHQ":   "high",
    "supermemoryai": "high",
    "remotion-dev":  "high",
    "firecrawl":     "high",
    "obra":          "medium",
}


def _classify_trust(author: str) -> str:
    """Map a GitHub author/org to a trust tier."""
    return _TRUSTED_AUTHORS.get(author, _TRUSTED_AUTHORS.get(author.lower(), "unknown"))


def _fetch_github_topics(timeout: int = 6) -> list[dict]:
    """Pull repos tagged with skill topics from GitHub. Best effort, returns
    [] on any error, rate-limit, or when telemetry is disabled. Trust tier
    is classified by author membership in _TRUSTED_AUTHORS.
    """
    if NO_TELEMETRY:
        return []
    out: list[dict] = []
    seen: set[str] = set()
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "skills-curator"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    for topic in _GITHUB_SKILL_TOPICS:
        url = f"https://api.github.com/search/repositories?q=topic:{topic}&sort=stars&per_page=20"
        try:
            raw = _http_get(url, headers=headers, timeout=timeout)
            if not raw:
                continue
            data = json.loads(raw)
        except Exception:
            continue
        for repo in data.get("items", []):
            full = repo.get("full_name", "")
            if not full or full in seen:
                continue
            seen.add(full)
            owner = full.split("/", 1)[0]
            out.append({
                "id": repo.get("name", "").lower(),
                "name": repo.get("name", ""),
                "source": full,
                "type": "capability",
                "trust": _classify_trust(owner),
                "install": f"npx skills add {full}",
                "tags": (repo.get("topics") or []) + ["github-discovered"],
                "description": (repo.get("description") or "").strip()[:240],
                "stars": repo.get("stargazers_count", 0),
                "pros": [],
                "cons": [],
            })
    return out


def _merge_catalog(curated: list[dict], discovered: list[dict]) -> list[dict]:
    """Merge curated KNOWN_SKILLS with GitHub-discovered entries. Curated
    entries win on id collision — community discoveries can't override our
    pros/cons or trust classification.
    """
    by_id = {s["id"]: s for s in discovered}
    for s in curated:
        by_id[s["id"]] = s  # curated overrides discovered
    return list(by_id.values())


def _load_catalog(refresh: bool = False) -> list[dict]:
    """Return the merged skill catalog (curated + GitHub-discovered).

    Curated entries (KNOWN_SKILLS) include hand-written pros/cons. GitHub
    topic search adds breadth but those entries arrive with empty pros/cons
    and "unknown"-tier trust unless the author is in _TRUSTED_AUTHORS.
    Cached for CATALOG_TTL_HOURS. We never scrape skills.sh HTML — that was
    deliberately removed in v4.0 (brittle, dishonest for a judgment tool).
    """
    if not refresh and CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            age = datetime.now() - datetime.fromisoformat(data.get("fetched_at", "2000-01-01"))
            if age < timedelta(hours=CATALOG_TTL_HOURS):
                return data.get("skills", KNOWN_SKILLS)
        except Exception:
            pass

    discovered = _fetch_github_topics()
    merged = _merge_catalog(KNOWN_SKILLS, discovered)
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "fetched_at": datetime.now().isoformat(),
            "sources": ["KNOWN_SKILLS"] + (["github-topics"] if discovered else []),
            "skills": merged,
        }, f, indent=2)
    return merged


# ─── Intelligence layer ───────────────────────────────────────────────────────
# The proactive flow. Skills Curator's USP is judgment that activates without
# being asked. Two entry points:
#   --auto      : fingerprint the project, re-run recommendations only on drift
#   --symptoms  : map a user complaint ("slow tests", "ugly UI") to skill tags

# Files whose presence or mtime change implies the project has shifted enough
# to re-recommend. Adding/removing a dependency or framework should trip this;
# editing a single source file should not.
_FINGERPRINT_FILES = (
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "requirements.txt", "pyproject.toml", "Pipfile", "Pipfile.lock", "poetry.lock",
    "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
    "Gemfile", "Gemfile.lock", "composer.json",
    "tsconfig.json", "tailwind.config.js", "tailwind.config.ts",
    "next.config.js", "next.config.ts", "vite.config.ts", "vite.config.js",
    "Dockerfile", "docker-compose.yml",
    "CLAUDE.md", "AGENTS.md", "README.md",
)


def _project_fingerprint(project_dir: Path) -> str:
    """Stable hash of (key file paths + their mtimes). Changes when deps,
    config, or top-level docs change — not when ordinary source files change."""
    parts: list[str] = []
    for name in _FINGERPRINT_FILES:
        p = project_dir / name
        if p.exists():
            try:
                parts.append(f"{name}:{int(p.stat().st_mtime)}:{p.stat().st_size}")
            except OSError:
                pass
    # Workflow dir presence (don't hash mtimes — yaml edits shouldn't trigger)
    if (project_dir / ".github" / "workflows").is_dir():
        parts.append(".github/workflows:exists")
    return hashlib.sha1("|".join(parts).encode()).hexdigest()[:16] if parts else ""


def _load_auto_state() -> dict:
    if not AUTO_STATE_FILE.exists():
        return {}
    try:
        with open(AUTO_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_auto_state(state: dict) -> None:
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUTO_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def cmd_auto(project_dir: Path | None = None, refresh: bool = False) -> None:
    """Proactive entry point. Call this at session start in any project — it
    decides whether a re-scan is needed by comparing the project fingerprint
    against the last known state. Outputs the prioritized 'next actions' only
    when something actually changed."""
    project_dir = project_dir or Path.cwd()
    proj_key = str(project_dir.resolve())
    fp_now = _project_fingerprint(project_dir)

    if not fp_now:
        print("⚠️  No project signals to fingerprint (no package.json, requirements.txt, CLAUDE.md, etc.)")
        print("   Run --recommend explicitly if you want to scan anyway.")
        return

    state = _load_auto_state()
    prev = state.get(proj_key, {})
    fp_last = prev.get("fingerprint")

    if fp_now == fp_last and not refresh:
        last_top = prev.get("top", [])
        scanned_at = prev.get("scanned_at", "?")
        if last_top:
            print(f"📋 No project changes since {scanned_at}. Last top picks: {', '.join(last_top)}")
            print(f"   Re-scan with --auto --refresh, or run --recommend for full output.")
        else:
            print(f"📋 No project changes since {scanned_at}. No recommendations on file.")
        return

    # Drift detected (or first scan, or forced refresh) — run the full pipeline
    if fp_last and fp_last != fp_now:
        print(f"🔄 Project changed since last scan — re-evaluating recommendations...\n")
    elif refresh:
        print(f"🔄 Forced re-scan...\n")
    else:
        print(f"🔍 First scan of {project_dir.name} — learning the stack...\n")

    signals = _scan_project(project_dir)
    if not signals.get("tags"):
        print("⚠️  No tags extracted. Add a CLAUDE.md or README.md describing the project.")
        return

    print(f"   Detected: {', '.join(sorted(signals['tags'])[:8])}\n")

    catalog = _load_catalog(refresh)
    registry_ids = {s["id"] for s in load_registry().get("skills", [])}
    existing = set(signals.get("existing_skills", [])) | registry_ids
    project_tags = set(signals["tags"])

    scored: list[tuple[int, set, dict]] = []
    for skill in catalog:
        if skill["id"] in existing:
            continue
        overlap = project_tags & set(skill.get("tags", []))
        if not overlap:
            continue
        score = len(overlap) * 10
        score += {"official": 20, "high": 15, "medium": 5, "community": 2}.get(skill.get("trust", ""), 0)
        scored.append((score, overlap, skill))
    scored.sort(key=lambda x: -x[0])

    top3 = scored[:3]
    state[proj_key] = {
        "fingerprint": fp_now,
        "scanned_at": str(date.today()),
        "top": [sk["id"] for _, _, sk in top3],
    }
    _save_auto_state(state)

    if not top3:
        print(f"  ✅ Stack is well-covered. No new skill suggestions.\n")
        print(f"     Re-run --auto whenever dependencies change.")
        return

    trust_icons = {"official": "🏛️", "high": "✅", "medium": "🟡", "community": "⬜", "unknown": "❓"}
    print(f"💡 Top {len(top3)} skill(s) that fit this project:\n")
    for i, (_, overlap, sk) in enumerate(top3, 1):
        t = trust_icons.get(sk.get("trust", ""), "❓")
        why = ", ".join(sorted(overlap)[:3])
        print(f"  {i}. {t} {sk['name']}")
        print(f"     Why     : matches [{why}]")
        print(f"     What    : {sk.get('description', '')[:80]}")
        print(f"     Install : {sk['install']}")
        print()
    print(f"  Next: /skill-evaluate <id> for any of these, or --recommend for the full list.\n")


# Symptom → tag map. Tuned for things users actually say in chat. Keys are
# substrings (case-insensitive); first match wins.
_SYMPTOM_MAP: list[tuple[tuple[str, ...], list[str]]] = [
    (("slow test", "tests are slow", "test suite slow"), ["testing", "performance", "test-performance"]),
    (("flaky test", "tests fail random"),                 ["testing", "test-stability"]),
    (("no test", "untested", "missing tests"),            ["testing", "test-coverage", "unit-test"]),
    (("failing ci", "ci is broken", "ci failing", "broken pipeline"), ["ci-cd", "github-actions"]),
    (("ugly ui", "messy ui", "design is bad", "looks bad"), ["frontend-design", "design-system", "ui"]),
    (("manual deploy", "deploying by hand", "no automation"), ["ci-cd", "deploy", "release-automation"]),
    (("no docs", "missing docs", "doc is bad", "outdated docs"), ["docs", "docgen", "readme-builder"]),
    (("messy commits", "bad commit messages", "commit history"), ["commit-writer", "conventional-commits"]),
    (("slow build", "build is slow"),                     ["build-tools", "performance", "vite"]),
    (("auth broken", "session bug", "login issue"),       ["auth", "session-management"]),
    (("scraping broken", "can't scrape", "browser auth"), ["scraping", "browser-automation"]),
    (("memory leak", "out of memory", "oom"),             ["performance", "profiling"]),
    (("slow api", "endpoint is slow"),                    ["performance", "api", "profiling"]),
    (("hard to refactor", "spaghetti code"),              ["refactor", "code-quality"]),
    (("pr review takes", "review takes forever"),         ["pr-review", "code-review"]),
    (("changelog", "release notes"),                      ["changelog", "release-notes"]),
    (("accessibility", "a11y"),                           ["accessibility", "ui"]),
]


def cmd_symptoms(symptom: str) -> None:
    """Map a user-described problem to skill categories and search the catalog.
    Use this when the user says 'X is slow' / 'X is broken' / 'I wish I had Y'
    instead of naming a skill directly."""
    sym_lower = symptom.lower()
    matched_tags: list[str] = []
    matched_phrases: list[str] = []
    for keys, tags in _SYMPTOM_MAP:
        for k in keys:
            if k in sym_lower:
                matched_phrases.append(k)
                matched_tags.extend(tags)
                break
    matched_tags = sorted(set(matched_tags))

    if not matched_tags:
        print(f"⚠️  No symptom mapping for '{symptom}'.")
        print(f"   Try: --find {symptom}  (free-text catalog search)")
        return

    print(f"🩺 Symptom '{symptom}' → tags: {', '.join(matched_tags)}\n")

    catalog = _load_catalog()
    registry_ids = {s["id"] for s in load_registry().get("skills", [])}
    scored: list[tuple[int, set, dict]] = []
    for skill in catalog:
        if skill["id"] in registry_ids:
            continue
        overlap = set(matched_tags) & set(skill.get("tags", []))
        if not overlap:
            continue
        score = len(overlap) * 10
        score += {"official": 20, "high": 15, "medium": 5, "community": 2}.get(skill.get("trust", ""), 0)
        scored.append((score, overlap, skill))
    scored.sort(key=lambda x: -x[0])

    if not scored:
        print(f"  No catalog matches for those tags.")
        print(f"  Consider scaffolding a custom skill: --author")
        return

    trust_icons = {"official": "🏛️", "high": "✅", "medium": "🟡", "community": "⬜", "unknown": "❓"}
    print(f"  Candidates:\n")
    for _, overlap, sk in scored[:5]:
        t = trust_icons.get(sk.get("trust", ""), "❓")
        print(f"  {t} {sk['name']}")
        print(f"     Tags    : {', '.join(sorted(overlap))}")
        print(f"     What    : {sk.get('description', '')[:80]}")
        print(f"     Install : {sk['install']}")
        print()
    print(f"  Next: /skill-evaluate <id> before installing.")


# ─── Customization (skill-fork-for-this-project) ──────────────────────────────
# Take an external skill, read its SKILL.md, score sections by relevance to
# the project, and emit a customization plan + a fork at
# ~/.claude/skills/<name>-for-<project>/SKILL.md. The actual content rewriting
# (e.g. swapping Vue examples for React) is done by the agent — this engine
# produces the structured plan so the rewrite is grounded.

CUSTOMIZE_DIR = Path.home() / ".claude" / "skills"


def _split_skill_sections(skill_md_text: str) -> list[tuple[str, str]]:
    """Split a SKILL.md body into (heading, content) pairs. Frontmatter is
    extracted as a separate ('__frontmatter__', text) tuple if present."""
    sections: list[tuple[str, str]] = []
    body = skill_md_text

    # Strip and capture YAML frontmatter
    m = re.match(r"^---\n(.*?)\n---\n", body, flags=re.DOTALL)
    if m:
        sections.append(("__frontmatter__", m.group(1)))
        body = body[m.end():]

    # Split on H1/H2 headings. Keep the heading line attached to its content.
    parts = re.split(r"^(#{1,2} .+)$", body, flags=re.MULTILINE)
    # parts[0] is preamble before any heading; parts[1::2] are headings; parts[2::2] are bodies
    if parts[0].strip():
        sections.append(("__preamble__", parts[0].strip()))
    for heading, content in zip(parts[1::2], parts[2::2]):
        sections.append((heading.strip(), content.strip()))
    return sections


def _section_relevance(content: str, project_tags: set[str], project_languages: list[str]) -> tuple[int, list[str]]:
    """Cheap scoring: count tag/language mentions in the section. Returns
    (score, matched_terms). Higher = more relevant to this project."""
    if not content:
        return 0, []
    text = content.lower()
    matched: list[str] = []
    score = 0
    for tag in project_tags:
        if tag.lower() in text:
            score += 2
            matched.append(tag)
    for lang in project_languages:
        if lang.lower() in text:
            score += 3  # languages are stronger signals than abstract tags
            matched.append(lang)
    # Boost for sections that look immediately actionable
    if any(k in text for k in ("install:", "usage:", "example", "```")):
        score += 1
    return score, matched


def _read_external_skill(source: str) -> tuple[str, str] | None:
    """Resolve an external skill identifier to (skill_name, SKILL.md text).
    Accepts: a registered skill id, a local folder path, an owner/repo[@skill]
    string (fetched from GitHub raw)."""
    # Local path?
    p = Path(source).expanduser()
    if p.is_dir() and (p / "SKILL.md").exists():
        return (p.name, (p / "SKILL.md").read_text(encoding="utf-8", errors="replace"))

    # Registered skill?
    reg = load_registry()
    for sk in reg.get("skills", []):
        if sk.get("id") == source:
            # Try the install path
            install_path = Path.home() / ".claude" / "skills" / sk["id"]
            if (install_path / "SKILL.md").exists():
                return (sk["id"], (install_path / "SKILL.md").read_text(encoding="utf-8", errors="replace"))
            # Fall back to fetching from source URL if it's a GitHub repo
            url = sk.get("source", "")
            if "github.com" in url:
                source = url.replace("https://github.com/", "").rstrip("/")
                # Continue to GitHub fetch path below

    # owner/repo[@skill] form
    if "/" in source and not source.startswith("/"):
        owner_repo, _, sub = source.partition("@")
        for branch in ("main", "master"):
            for path_pattern in (f"skills/{sub}/SKILL.md", f"skills/{owner_repo.split('/')[-1]}/SKILL.md", "SKILL.md"):
                if not sub and "/SKILL.md" not in path_pattern.replace("/SKILL.md", ""):
                    continue
                try:
                    raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{path_pattern}"
                    text = _http_get(raw_url, timeout=10)
                    if text and text.startswith("---"):
                        return (sub or owner_repo.split("/")[-1], text)
                except Exception:
                    continue
    return None


def cmd_customize(source: str, project_dir: Path | None = None,
                  emit_fork: bool = True) -> None:
    """Take an external skill and produce a project-tailored customization
    plan + (optionally) a forked SKILL.md the agent can rewrite for this
    specific project."""
    project_dir = project_dir or Path.cwd()
    project_name = project_dir.name

    print(f"🔧 Customizing '{source}' for project: {project_name}\n")

    fetched = _read_external_skill(source)
    if not fetched:
        print(f"❌ Could not resolve '{source}' to a SKILL.md.")
        print(f"   Try a local path, a registered skill id, or owner/repo@skill-name.")
        return
    skill_id, skill_md = fetched
    print(f"   Loaded SKILL.md ({len(skill_md):,} chars)")

    signals = _scan_project(project_dir)
    if not signals.get("tags"):
        print(f"⚠️  No project signals — add a CLAUDE.md or README.md so customization has something to specialize against.")
        return
    project_tags = set(signals["tags"])
    languages = signals.get("languages", [])
    print(f"   Project signals: {', '.join(sorted(project_tags)[:8])}\n")

    sections = _split_skill_sections(skill_md)
    if not sections:
        print(f"⚠️  Could not parse SKILL.md sections.")
        return

    # Score each section
    plan: list[dict] = []
    for heading, content in sections:
        if heading == "__frontmatter__":
            plan.append({"heading": heading, "action": "rewrite-frontmatter",
                         "score": -1, "matched": [],
                         "note": "Update name to '<original>-for-<project>', point homepage to fork"})
            continue
        if heading == "__preamble__":
            plan.append({"heading": heading, "action": "keep",
                         "score": 0, "matched": [], "note": "Pre-heading text — usually safe to keep"})
            continue
        score, matched = _section_relevance(content, project_tags, languages)
        if score >= 5:
            action = "keep-emphasize"
            note = "High project fit — keep verbatim and reinforce relevant examples"
        elif score >= 2:
            action = "keep-trim"
            note = "Some fit — keep the matching parts, trim the rest"
        elif score == 0 and any(k in content.lower() for k in ("vue", "angular", "svelte", "rails", "django")) \
             and any(t in project_tags for t in ("react", "nextjs", "fastapi", "express")):
            action = "rewrite-stack"
            note = "Examples target a stack the project doesn't use — agent should rewrite for project's stack"
        elif score == 0:
            action = "drop-or-rewrite"
            note = "Zero project relevance signals — agent should drop or rewrite for this project"
        else:
            action = "keep-trim"
            note = "Marginal fit — keep but consider trimming"
        plan.append({"heading": heading, "action": action,
                     "score": score, "matched": matched, "note": note,
                     "preview": content[:200].replace("\n", " ")})

    # Print the plan
    print(f"╔══════════════════════════════════════════════════════════════╗")
    print(f"║  Customization plan: {skill_id} → {project_name:<32}║")
    print(f"╚══════════════════════════════════════════════════════════════╝\n")
    for i, p in enumerate(plan, 1):
        h = p['heading']
        if h == "__frontmatter__":
            h = "(YAML frontmatter)"
        elif h == "__preamble__":
            h = "(preamble)"
        action_icon = {"keep-emphasize": "🟢", "keep": "🟢", "keep-trim": "🟡",
                       "rewrite-frontmatter": "✏️", "rewrite-stack": "🔄",
                       "drop-or-rewrite": "🔴"}.get(p["action"], "•")
        print(f"  {i:02}. {action_icon} [{p['action']:<18}] score={p['score']:<3} {h}")
        if p.get("matched"):
            print(f"      Matched : {', '.join(p['matched'][:5])}")
        print(f"      Action  : {p['note']}")
        print()

    if not emit_fork:
        return

    # Emit the fork
    fork_id = f"{skill_id}-for-{project_name}".lower().replace(" ", "-")
    fork_dir = CUSTOMIZE_DIR / fork_id
    fork_dir.mkdir(parents=True, exist_ok=True)
    fork_path = fork_dir / "SKILL.md"

    fork_lines = ["---",
                  f"name: {fork_id}",
                  f"description: |",
                  f"  Project-customized fork of '{skill_id}' for '{project_name}'.",
                  f"  Generated by Skills Curator. Tailored to: {', '.join(sorted(project_tags)[:5])}",
                  f"metadata:",
                  f"  derived_from: {skill_id}",
                  f"  customized_for: {project_name}",
                  f"  customized_at: {date.today()}",
                  f"  customized_by: skills-curator/{VERSION}",
                  "---",
                  "",
                  f"# {fork_id}",
                  "",
                  f"> **Customization in progress.** This fork was generated by `skills-curator --customize`.",
                  f"> The agent should now rewrite each section per the plan below.",
                  "",
                  "## Customization plan",
                  "",
                  "| # | Section | Action | Why |",
                  "|---|---|---|---|"]

    for i, p in enumerate(plan, 1):
        h = p['heading'].replace("__frontmatter__", "(frontmatter)").replace("__preamble__", "(preamble)")
        fork_lines.append(f"| {i} | {h[:60]} | `{p['action']}` | {p['note'][:80]} |")

    fork_lines.extend([
        "",
        "---",
        "",
        "## Original skill source",
        "",
        f"```",
        skill_md[:2000] + ("..." if len(skill_md) > 2000 else ""),
        "```",
        "",
        "---",
        "",
        "## Agent: rewrite this section",
        "",
        "Walk through each row of the plan above. For each section:",
        "",
        "- `keep` / `keep-emphasize` → copy the original section verbatim into this file under its heading",
        "- `keep-trim` → copy the parts that match this project's signals; drop the rest",
        "- `rewrite-stack` → rewrite examples to use this project's stack (replace Vue/Angular/etc. with the project's framework)",
        "- `rewrite-frontmatter` → write a fresh frontmatter block with the fork id and updated metadata",
        "- `drop-or-rewrite` → drop or rewrite from scratch in a project-specific way",
        "",
        "When done, replace this whole 'Customization plan' section with the rewritten content.",
        ""
    ])

    fork_path.write_text("\n".join(fork_lines), encoding="utf-8")
    print(f"  ✅ Fork scaffolded at: {fork_path}")
    print(f"     Next: ask the agent to rewrite sections per the plan above.")
    print(f"     The agent should read the original SKILL.md, follow the action column, and replace")
    print(f"     the 'Customization plan' section with the rewritten content.")


def cmd_recommend(project_dir: Path | None = None,
                  refresh: bool = False, max_n: int = 8) -> None:
    project_dir = project_dir or Path.cwd()
    print(f"🔍 Scanning: {project_dir.name}...")
    signals = _scan_project(project_dir)

    if not signals["tags"]:
        print("⚠️  No signals detected. Add CLAUDE.md or README.md with project description.")
        return

    print(f"   Stack: {', '.join(signals['languages'][:5])}")
    tags = set(signals["tags"])

    print("📦 Loading skill catalog...")
    catalog = _load_catalog(refresh)
    registry_ids = {s["id"] for s in load_registry().get("skills", [])}
    existing = set(signals.get("existing_skills", [])) | registry_ids

    scored: list[tuple[int, set[str], dict]] = []
    for skill in catalog:
        if skill["id"] in existing:
            continue
        overlap = tags & set(skill.get("tags", []))
        if not overlap:
            continue
        # Score on fit, not popularity. Tag overlap is the primary signal;
        # trust tier is the tiebreaker.
        score = len(overlap) * 10
        score += {"official": 20, "high": 15, "medium": 5, "community": 2}.get(skill.get("trust", ""), 0)
        scored.append((score, overlap, skill))
    scored.sort(key=lambda x: -x[0])

    if not scored:
        print("\n  ✅ No new recommendations — stack looks well covered.\n")
        return

    capability = [(s, o, sk) for s, o, sk in scored if sk.get("type") == "capability"]
    preference = [(s, o, sk) for s, o, sk in scored if sk.get("type") == "preference"]

    trust_icons = {"official": "🏛️", "high": "✅", "medium": "🟡", "community": "⬜", "unknown": "❓"}

    print(f"\n{'═' * 60}")
    print(f"  Recommendations for: {project_dir.name}")
    print(f"{'═' * 60}")

    def _customize_hint(sk: dict, project_tags: set[str]) -> str | None:
        """One-line customization hint when the skill's tags suggest a stack
        mismatch with the project. Returns None if no obvious mismatch."""
        skill_tags = set(sk.get("tags", []))
        # Vue-tagged skill in a React project (or vice versa) is the canonical
        # case for --customize. Generalize to a few stack pairs.
        rivals = [
            ({"vue", "nuxt"},     {"react", "nextjs"}),
            ({"react", "nextjs"}, {"vue", "nuxt"}),
            ({"angular"},         {"react", "vue"}),
            ({"django", "flask"}, {"fastapi"}),
            ({"fastapi"},         {"django", "flask"}),
        ]
        for skill_set, project_set in rivals:
            if skill_set & skill_tags and project_set & project_tags:
                return (f"Stack mismatch ({', '.join(sorted(skill_set & skill_tags))} "
                        f"in skill vs {', '.join(sorted(project_set & project_tags))} in project) "
                        f"— run `--customize {sk['id']}` to fork with rewritten examples.")
        return None

    def show(group: list, label: str, icon: str, max_show: int) -> None:
        if not group:
            return
        print(f"\n  {icon} {label}\n")
        for i, (_, overlap, sk) in enumerate(group[:max_show], 1):
            t = trust_icons.get(sk.get("trust", ""), "❓")
            print(f"  {i:02}. {t} {sk['name']}")
            print(f"       Why     : [{', '.join(sorted(overlap)[:3])}]")
            print(f"       What    : {sk.get('description', '')[:75]}")
            print(f"       Trust   : {sk.get('trust', '?')}")
            for p in sk.get("pros", [])[:2]:
                print(f"       ✓ Pro   : {p}")
            for c in sk.get("cons", [])[:2]:
                print(f"       ✗ Con   : {c}")
            hint = _customize_hint(sk, tags)
            if hint:
                print(f"       💡 Tip   : {hint}")
            print(f"       Install : {sk['install']}")
            print()

    show(capability, "CAPABILITY — new abilities", "⚡", min(max_n, 5))
    show(preference, "PREFERENCE — better defaults", "🎨", min(max_n, 4))

    recs = [{"id": sk["id"], "name": sk["name"], "install": sk["install"],
             "score": s, "overlap": sorted(o)} for s, o, sk in scored[:10]]
    history: dict = {}
    if RECOMMENDATIONS_FILE.exists():
        try:
            with open(RECOMMENDATIONS_FILE, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = {}
    history[project_dir.name] = {"date": str(date.today()), "recommendations": recs}
    with open(RECOMMENDATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    print(f"  💾 Saved to recommendations.json")


def cmd_discover(term: str | None = None, refresh: bool = False) -> None:
    catalog = _load_catalog(refresh)
    trust_icons = {"official": "🏛️", "high": "✅", "medium": "🟡", "community": "⬜", "unknown": "❓"}

    trust_rank = {"official": 0, "high": 1, "medium": 2, "community": 3, "unknown": 4}

    if term:
        tl = term.lower()
        results = [
            s for s in catalog
            if tl in " ".join(
                [s.get("id", ""), s.get("name", ""), s.get("description", "")]
                + s.get("tags", [])
            ).lower()
        ]
        results.sort(key=lambda x: trust_rank.get(x.get("trust", ""), 99))
        print(f"\n🔍 Catalog search '{term}' — {len(results)} result(s)\n")
        for s in results[:10]:
            t = trust_icons.get(s.get("trust", ""), "❓")
            print(f"  {t} {s['name']:35}  {s.get('trust', '?'):10}  [{s['id']}]")
            print(f"     {s.get('description', '')[:75]}")
            print(f"     {s['install']}")
    else:
        catalog_sorted = sorted(catalog, key=lambda x: trust_rank.get(x.get("trust", ""), 99))
        print(f"\n📋 Skill Catalog — {len(catalog_sorted)} skills\n")
        for s in catalog_sorted:
            t = trust_icons.get(s.get("trust", ""), "❓")
            print(f"  {t} {s['name']:40} {s.get('type', '?'):12}  trust:{s.get('trust', '?'):10}  [{s['id']}]")
    print()


def cmd_scan(project_dir: Path | None = None) -> None:
    project_dir = project_dir or Path.cwd()
    signals = _scan_project(project_dir)
    print(f"\n{'═' * 52}")
    print(f"  Project Scan: {project_dir.name}")
    print(f"{'═' * 52}")
    print(f"  Languages : {', '.join(signals['languages']) or 'none'}")
    print(f"  Tags      : {', '.join(signals['tags'][:12]) or 'none'}")
    print(f"  Skills    : {', '.join(signals.get('existing_skills', [])) or 'none'}\n")


# ─── Security Scan ────────────────────────────────────────────────────────────

def _strip_scanner_ignored(text: str) -> str:
    """Remove lines or blocks the author has explicitly opted out of scanning.

    Markers (case-insensitive) recognized in any source/markdown file:
      - `scanner:ignore`             → strip just the line containing it
      - `scanner:ignore-block-start` → strip lines until `scanner:ignore-block-end`
    """
    out: list[str] = []
    in_block = False
    for line in text.splitlines(keepends=True):
        low = line.lower()
        if "scanner:ignore-block-start" in low:
            in_block = True
            continue
        if "scanner:ignore-block-end" in low:
            in_block = False
            continue
        if in_block:
            continue
        if "scanner:ignore" in low:
            continue
        out.append(line)
    return "".join(out)


def cmd_check(skill_path: str) -> None:
    """Scan a skill folder for security risks before installing."""
    path = Path(skill_path).expanduser()
    if not path.exists():
        print(f"❌ Path not found: {path}")
        return

    print(f"\n🔒 Security Scan: {path.name}")
    print(f"{'─' * 52}")

    findings: list[tuple[str, str, str]] = []
    files_scanned = 0
    scannable_exts = {".py", ".sh", ".js", ".ts", ".md", ".yaml", ".yml", ".json", ""}

    for fpath in path.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix not in scannable_exts:
            continue
        try:
            raw = fpath.read_text(errors="ignore")
            # Strip lines/blocks marked scanner:ignore so docs and pattern
            # definitions don't trigger false positives on their own literals.
            content = _strip_scanner_ignored(raw)
            files_scanned += 1
            for pattern, severity, description in SECURITY_RISK_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    findings.append((severity, description, str(fpath.relative_to(path))))
        except Exception:
            continue

    print(f"  Files scanned: {files_scanned}")

    if not findings:
        print(f"  ✅ No risks detected\n")
        _mark_security_reviewed(path, [])
        return

    critical = [f for f in findings if "CRITICAL" in f[0]]
    high     = [f for f in findings if "HIGH" in f[0]]
    medium   = [f for f in findings if "MEDIUM" in f[0]]

    for group, label in [(critical, "CRITICAL"), (high, "HIGH"), (medium, "MEDIUM")]:
        if group:
            print(f"\n  {group[0][0]} {label} ({len(group)} finding(s)):")
            for sev, desc, fname in group:
                print(f"     • {desc}")
                print(f"       in: {fname}")

    if critical or high:
        print(f"\n  ❌ DO NOT INSTALL — critical/high risks found.")
        print(f"     Review the files above before proceeding.\n")
        # Don't auto-mark reviewed when there are critical/high findings
    else:
        print(f"\n  ⚠️  Review medium risks before installing.\n")
        _mark_security_reviewed(path, findings)


def _mark_security_reviewed(scanned_path: Path, findings: list) -> None:
    """Mark a skill as security-reviewed in registry, with a clear warning if the
    folder name doesn't match any registered skill id."""
    folder = scanned_path.name
    registry = load_registry()
    matched = None
    for s in registry["skills"]:
        if s["id"] == folder:
            matched = s
            break
    if matched is None:
        # Try matching by source URL fragment
        for s in registry["skills"]:
            src = s.get("source", "").lower()
            if folder.lower() in src:
                matched = s
                break

    if matched is None:
        print(f"  ℹ️  Folder '{folder}' is not registered. Run --add to track it,")
        print(f"     then re-run --check to mark it security-reviewed.")
        return

    matched["security_reviewed"] = True
    matched["security_scan"] = {
        "date": str(date.today()),
        "result": "clean" if not findings else "review-needed",
        "findings": [{"severity": f[0], "description": f[1], "file": f[2]} for f in findings],
    }
    save_registry(registry)
    print(f"  🔒 Marked '{matched['id']}' as security-reviewed in registry")


# ─── Duplicate & Conflict Audit ──────────────────────────────────────────────

def cmd_audit() -> None:
    """Detect duplicate skills and preference conflicts."""
    registry = load_registry()
    skills = registry.get("skills", [])
    print(f"\n{'═' * 56}")
    print(f"  Skill Audit  ·  {len(skills)} skill(s)")
    print(f"{'═' * 56}\n")

    # 1. Duplicate detection by source URL
    source_map: dict[str, list] = {}
    for s in skills:
        src = s.get("source", "").lower().strip("/")
        if src and src != "auto-detected":
            source_map.setdefault(src, []).append(s)
    dupes = {k: v for k, v in source_map.items() if len(v) > 1}
    if dupes:
        print(f"  🟡 DUPLICATES ({len(dupes)} group(s))")
        for src, group in dupes.items():
            ids = [s["id"] for s in group]
            print(f"     Same source: {src}")
            print(f"     IDs: {', '.join(ids)}")
            print(f"     → Keep: {ids[0]}  Remove: {', '.join(ids[1:])}")
        print()
    else:
        print("  ✅ No duplicate sources\n")

    # 2. Preference skill conflict detection
    DOMAIN_TAGS = {
        "frontend-style": {"frontend", "design", "css", "ui"},
        "react-patterns": {"react", "nextjs", "jsx", "tsx"},
        "git-workflow":   {"git", "commits", "version-control"},
        "testing":        {"testing", "jest", "vitest", "playwright"},
        "backend-api":    {"backend", "api", "nodejs", "python"},
        "security":       {"security", "audit", "owasp"},
    }
    prefs = [s for s in skills if s.get("type") == "preference"]
    conflicts: list[tuple[str, list]] = []
    for domain, domain_tags in DOMAIN_TAGS.items():
        overlap = [s for s in prefs if domain_tags & set(s.get("tags", []))]
        if len(overlap) > 1:
            conflicts.append((domain, overlap))

    if conflicts:
        print(f"  🟠 PREFERENCE CONFLICTS ({len(conflicts)} domain(s))")
        for domain, group in conflicts:
            print(f"     Domain: {domain.replace('-', ' ').title()}")
            for s in group:
                ev = s.get("evaluation_history", [])
                verdict = f"[{ev[-1]['verdict'].upper()}]" if ev else "[unevaluated]"
                print(f"       • {s['name']}  {verdict}")
            print(f"     → Two preference skills may give Claude conflicting instructions.")
        print()
    else:
        print("  ✅ No preference conflicts detected\n")

    # 3. Unevaluated skills
    unevaluated = [s for s in skills if not s.get("evaluation_history")]
    if unevaluated:
        print(f"  ⬜ UNEVALUATED ({len(unevaluated)} skill(s))")
        for s in unevaluated:
            print(f"     • {s['name']}  [{s['id']}]")
        print(f"     → Run --eval <id> <project> <verdict> '<summary>' for each\n")
    else:
        print("  ✅ All skills have evaluations\n")

    # 4. Security unreviewed
    unreviewed = [s for s in skills if not s.get("security_reviewed")]
    if unreviewed:
        print(f"  🔓 SECURITY UNREVIEWED ({len(unreviewed)} skill(s))")
        for s in unreviewed:
            src = s.get("source", "?")
            print(f"     • {s['name']}  (source: {src})")
        print(f"     → Run --check <installed-path> for community skills\n")
    else:
        print("  ✅ All skills security-reviewed\n")


# ─── Health Scoring ───────────────────────────────────────────────────────────

def cmd_health() -> None:
    """Score each registered skill on quality and completeness."""
    registry = load_registry()
    skills = registry.get("skills", [])
    if not skills:
        print("📭 No skills registered.")
        return

    scores: list[tuple[int, dict, list[str]]] = []
    for s in skills:
        score = 0
        breakdown: list[str] = []
        ev = s.get("evaluation_history", [])

        if ev:
            score += HEALTH_WEIGHTS["has_evaluation"]
            breakdown.append(f"+{HEALTH_WEIGHTS['has_evaluation']} evaluated")
            try:
                last_date = datetime.fromisoformat(ev[-1]["date"])
                if (datetime.now() - last_date).days <= 90:
                    score += HEALTH_WEIGHTS["recent_eval"]
                    breakdown.append(f"+{HEALTH_WEIGHTS['recent_eval']} recent")
            except Exception:
                pass

        if s.get("security_reviewed"):
            score += HEALTH_WEIGHTS["security_reviewed"]
            breakdown.append(f"+{HEALTH_WEIGHTS['security_reviewed']} security✓")
        if s.get("description"):
            score += HEALTH_WEIGHTS["has_description"]
        if s.get("tags"):
            score += HEALTH_WEIGHTS["has_tags"]
        if s.get("source") and s["source"] != "auto-detected":
            score += HEALTH_WEIGHTS["has_source"]
        if s.get("install_command") and s["install_command"] != "unknown":
            score += HEALTH_WEIGHTS["has_install"]
        if s.get("compatibility"):
            score += HEALTH_WEIGHTS["has_compatibility"]

        scores.append((score, s, breakdown))

    scores.sort(key=lambda x: -x[0])
    max_score = sum(HEALTH_WEIGHTS.values())

    print(f"\n{'═' * 56}")
    print(f"  Skill Health Report  ·  {len(skills)} skill(s)  ·  max={max_score}")
    print(f"{'═' * 56}\n")

    for score, s, breakdown in scores:
        pct = int(score / max_score * 100)
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        grade = "A" if pct >= 80 else "B" if pct >= 60 else "C" if pct >= 40 else "D"
        ev = s.get("evaluation_history", [])
        verdict = f"[{ev[-1]['verdict'].upper()}]" if ev else "[unevaluated]"

        print(f"  {grade} [{bar}] {pct:3}%  {s['name']}  {verdict}")
        if pct < 80:
            missing: list[str] = []
            if not ev:                          missing.append("needs evaluation")
            if not s.get("security_reviewed"):  missing.append("not security-reviewed")
            if not s.get("tags"):               missing.append("no tags")
            if not s.get("description"):        missing.append("no description")
            if missing:
                print(f"       ↳ {', '.join(missing)}")
    print()


# ─── Stale Version Check ──────────────────────────────────────────────────────

def cmd_stale() -> None:
    """Check if installed skills have newer versions on GitHub."""
    registry = load_registry()
    skills = registry.get("skills", [])
    checkable = [
        s for s in skills
        if "github.com" in s.get("source", "").lower() or "/" in s.get("source", "")
    ]
    if not checkable:
        print("⬜ No GitHub-sourced skills to check.")
        return

    print(f"\n🔄 Checking {len(checkable)} skill(s) for updates...\n")
    stale: list[tuple[dict, str, str]] = []
    current: list[tuple[dict, str]] = []
    errors: list[str] = []

    for s in checkable:
        src = s.get("source", "")
        parts = src.replace("https://github.com/", "").strip("/").split("/")
        if len(parts) < 2:
            errors.append(s["id"])
            continue
        owner, repo = parts[0], parts[1].split("@")[0]

        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
            headers = {"User-Agent": f"skills-curator/{VERSION}"}
            if GITHUB_TOKEN:
                headers["Authorization"] = f"token {GITHUB_TOKEN}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read())
            latest_tag = data.get("tag_name", "")
            installed = s.get("installed_version", "")
            if latest_tag and installed and latest_tag != installed:
                stale.append((s, installed, latest_tag))
            elif latest_tag:
                current.append((s, latest_tag))
            else:
                errors.append(s["id"])
        except Exception:
            errors.append(s["id"])

    if stale:
        print(f"  🟡 UPDATES AVAILABLE ({len(stale)})")
        for s, installed, latest in stale:
            print(f"     {s['name']}  installed={installed or '?'}  latest={latest}")
            print(f"     Reinstall: {s.get('install_command', '?')}")
        print()
    if current:
        print(f"  ✅ UP TO DATE ({len(current)}): {', '.join(s['name'] for s, _ in current)}")
    if errors:
        print(f"  ❓ COULD NOT CHECK ({len(errors)}): {', '.join(errors)}")
    print()


# ─── Cross-Agent Migration ────────────────────────────────────────────────────

def cmd_platforms(verbose: bool = False) -> None:
    """List every supported agent platform with detection status."""
    detected = set(_detect_platforms())
    total = len(PLATFORMS)
    primary = {"claude-code", "github-copilot"}

    print()
    print("═" * 64)
    print(f"  Skills Curator Platforms  ·  Detected {len(detected)} of {total}")
    print("═" * 64)
    if detected:
        names = ", ".join(PLATFORMS[p]["display"] for p in sorted(detected))
        print(f"\n  Detected on this machine: {names}\n")
    else:
        print("\n  No supported agents detected on this machine.\n")
    print(f"  {'PLATFORM':22}  {'STATUS':10}  DIR")
    print(f"  {'-' * 22}  {'-' * 10}  ---")

    def _row(pid: str) -> str:
        meta = PLATFORMS[pid]
        status = "✓ detected" if pid in detected else ("default" if pid in primary else "")
        path_str = str(meta["dir"]).replace(str(HOME), "~")
        return f"  {meta['display']:22}  {status:10}  {path_str}"

    # Primary first, then detected (non-primary), then everything else.
    primary_rows = [pid for pid in PLATFORMS if pid in primary]
    other_detected = [pid for pid in PLATFORMS if pid in detected and pid not in primary]
    rest = [pid for pid in PLATFORMS if pid not in detected and pid not in primary]
    ordered = primary_rows + other_detected + (rest if verbose else [])
    for pid in ordered:
        print(_row(pid))
    if not verbose and rest:
        print(f"\n  ({len(rest)} more not shown — use --platforms --verbose to list all)")
    print()


def cmd_migrate(target_spec: str | None = None, all_detected: bool = False) -> None:
    """Copy installed Claude Code skills to one or more other agents.

    Accepts:
      - None / empty   → list platforms and prompt the user (TTY) or default to Claude Code
      - "<id>"         → single target (e.g. "cursor")
      - "<a>,<b>,<c>"  → multi-target
      - "detected"     → every platform detected on this machine
      - all_detected=True (from --all-detected flag) → same as "detected"
    """
    src_dir = PLATFORMS["claude-code"]["dir"]
    if not src_dir.exists():
        print(f"❌ Claude Code skills dir not found: {src_dir}")
        return

    detected = _detect_platforms()
    valid = set(PLATFORMS.keys())

    if all_detected or (target_spec and target_spec.strip().lower() == "detected"):
        targets = [p for p in detected if p != "claude-code"] or DEFAULT_PLATFORMS
    elif not target_spec:
        # No target: show platforms then prompt (TTY) or fall back to defaults.
        cmd_platforms(verbose=False)
        if sys.stdin.isatty():
            print("  Enter target platform(s) — comma-separated id(s), 'detected' for all installed,")
            print(f"  or press Enter for default ({', '.join(DEFAULT_PLATFORMS)}):")
            raw = input("  > ").strip()
            if not raw:
                targets = list(DEFAULT_PLATFORMS)
            elif raw.lower() == "detected":
                targets = [p for p in detected if p != "claude-code"] or list(DEFAULT_PLATFORMS)
            else:
                targets = [t.strip() for t in raw.split(",") if t.strip()]
        else:
            print(f"  No target specified, no TTY — defaulting to: {', '.join(DEFAULT_PLATFORMS)}\n")
            targets = list(DEFAULT_PLATFORMS)
    else:
        targets = [t.strip() for t in target_spec.split(",") if t.strip()]

    invalid = [t for t in targets if t not in valid]
    if invalid:
        print(f"❌ Unknown platform(s): {', '.join(invalid)}")
        print(f"   Run --platforms to see all {len(valid)} supported platforms.")
        return
    if not targets:
        print("⬜ No targets selected — nothing to migrate.")
        return

    import shutil
    skills = [d for d in src_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    if not skills:
        print(f"⬜ No skills found in {src_dir}")
        return

    print(f"\n📦 Migrating {len(skills)} skill(s) → {', '.join(targets)}\n")
    summary: list[tuple[str, int, int]] = []
    for tgt in targets:
        dst_dir = PLATFORMS[tgt]["dir"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        migrated, skipped = 0, 0
        print(f"  → {PLATFORMS[tgt]['display']}  ({dst_dir})")
        for skill_dir in skills:
            dst = dst_dir / skill_dir.name
            if dst.exists():
                skipped += 1
            else:
                shutil.copytree(str(skill_dir), str(dst))
                migrated += 1
        summary.append((tgt, migrated, skipped))
        print(f"     {migrated} copied, {skipped} skipped (already present)\n")

    total_copied = sum(s[1] for s in summary)
    total_skipped = sum(s[2] for s in summary)
    print(f"  Done — {total_copied} copies across {len(targets)} platform(s), {total_skipped} skipped\n")


# ─── Skill Authoring Scaffold ─────────────────────────────────────────────────

def cmd_author() -> None:
    """Interactive scaffold for creating a new SKILL.md."""
    print(f"\n{'═' * 52}")
    print(f"  Skill Author  ·  Create a new SKILL.md")
    print(f"{'═' * 52}\n")
    print("  Answer a few questions. Press Enter to use defaults.\n")

    def ask(prompt: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        val = input(f"  {prompt}{suffix}: ").strip()
        return val or default

    name    = ask("Skill name (kebab-case)", "my-skill")
    desc    = ask("One-line description + trigger phrase")
    stype   = ask("Type: capability or preference", "capability")
    tools   = ask("allowed-tools (comma-separated, e.g. Bash,Read)", "Bash,Read")
    trigger = ask("When should it auto-activate? (describe scenario)")
    author  = ask("Your GitHub username")

    skill_dir = Path.cwd() / name
    skill_dir.mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)

    tools_list = "\n  - ".join(t.strip() for t in tools.split(","))
    skill_md = f"""---
name: {name}
description: >
  {desc}
  Use when: {trigger}
metadata:
  version: "1.0.0"
  author: {author}
  license: MIT
when_to_use:
  - {trigger}
user-invocable: true
allowed-tools:
  - {tools_list}
---

# {name.replace('-', ' ').title()}

Brief description of what this skill does and why it exists.

---

## Workflow

1. First step
2. Second step
3. Third step

---

## Output Format

Describe expected output here.

---

## Examples

**Example 1:**
Input: what the user says
Output: what Claude produces
"""

    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    manifest = f"""bundle: {name}
bundle_version: 1.0.0
files:
  - path: SKILL.md
    role: skill
    version: 1.0.0
    sha256: ""
"""
    (skill_dir / "MANIFEST.yaml").write_text(manifest, encoding="utf-8")

    changelog = f"""# {name} Changelog

## 1.0.0 — {date.today()}
- Initial release
"""
    (skill_dir / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    print(f"\n  ✅ Scaffold created: {skill_dir}/")
    print(f"     {name}/SKILL.md")
    print(f"     {name}/MANIFEST.yaml  (skill-provenance compatible)")
    print(f"     {name}/CHANGELOG.md")
    print(f"     {name}/references/")
    print(f"     {name}/scripts/")
    print(f"\n  Next: edit SKILL.md, then run --check {name}/ before sharing\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description=f"Skills Curator v{VERSION} — evaluate, track, discover",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Registry
    p.add_argument("--list",       action="store_true")
    p.add_argument("--type",       choices=VALID_TYPES)
    p.add_argument("--search",     metavar="TERM")
    p.add_argument("--detect",     action="store_true")
    p.add_argument("--status",     action="store_true")
    p.add_argument("--validate",   action="store_true")
    p.add_argument("--strict",     action="store_true")
    p.add_argument("--export",     action="store_true")
    p.add_argument("--sync",       action="store_true")
    p.add_argument("--push",       action="store_true")
    p.add_argument("--history",    metavar="SKILL_ID")
    p.add_argument("--remove",     metavar="SKILL_ID")
    p.add_argument("--add",        nargs=4, metavar=("ID", "NAME", "SOURCE", "INSTALL"))
    p.add_argument("--eval",       nargs=4, metavar=("ID", "PROJECT", "VERDICT", "SUMMARY"))
    p.add_argument("--pros",       help="Comma-separated pros for --eval")
    p.add_argument("--cons",       help="Comma-separated cons for --eval")
    p.add_argument("--conflicts",  help="Comma-separated conflicts for --eval")
    p.add_argument("--skill-type", choices=VALID_TYPES, default="capability")
    # Discovery
    p.add_argument("--recommend",  action="store_true")
    p.add_argument("--discover",   nargs="?", const="", metavar="TERM")
    p.add_argument("--find",       nargs="?", const="", metavar="TERM",
                   help="Alias for --discover (familiar name from npx skills find)")
    p.add_argument("--scan",       action="store_true")
    # Intelligence layer (proactive)
    p.add_argument("--auto",       action="store_true",
                   help="Proactive scan + recommend, only re-runs on project drift")
    p.add_argument("--symptoms",   metavar="PHRASE",
                   help="Map a user-described problem ('slow tests', 'ugly UI') to skills")
    p.add_argument("--refresh",    action="store_true")
    p.add_argument("--max",        type=int, default=8)
    p.add_argument("--path",       type=Path, default=None)
    # Safety + authoring
    p.add_argument("--check",      metavar="PATH")
    p.add_argument("--audit",      action="store_true")
    p.add_argument("--health",     action="store_true")
    p.add_argument("--stale",      action="store_true")
    p.add_argument("--migrate",    nargs="?", const="", metavar="AGENT[,AGENT...]",
                   help="Copy installed skills to one or more platforms (comma-separated, 'detected', or no arg to prompt)")
    p.add_argument("--all-detected", action="store_true",
                   help="With --migrate, target every platform detected on this machine")
    p.add_argument("--platforms",  action="store_true",
                   help="List supported agent platforms with detection status")
    p.add_argument("--verbose",    action="store_true",
                   help="With --platforms, show every platform (not just detected + primary)")
    p.add_argument("--author",     action="store_true")
    p.add_argument("--customize",  metavar="SOURCE",
                   help="Fork an external skill as a project-customized version (SOURCE = registered id, local path, or owner/repo@skill)")
    p.add_argument("--no-fork",    action="store_true",
                   help="With --customize, only print the plan; don't write the fork")
    p.add_argument("--export-eval", dest="export_eval", metavar="SKILL_ID",
                   help="Emit latest evaluation as shareable markdown")
    p.add_argument("--version",    action="version", version=f"%(prog)s {VERSION}")

    args = p.parse_args()
    proj = args.path or Path.cwd()

    if args.list:                       cmd_list(args.type)
    elif args.search:                   cmd_search(args.search)
    elif args.detect:                   cmd_detect(proj)
    elif args.status:                   cmd_status(proj)
    elif args.validate:                 cmd_validate(args.strict)
    elif args.export:                   print(json.dumps(load_registry(), indent=2))
    elif args.sync:                     gist_pull()
    elif args.push:                     gist_push(load_registry())
    elif args.history:                  cmd_history(args.history)
    elif args.remove:                   cmd_remove(args.remove)
    elif args.add:                      cmd_add(*args.add, skill_type=args.skill_type)
    elif args.eval:                     cmd_eval(*args.eval,
                                                 pros=_split_csv(args.pros),
                                                 cons=_split_csv(args.cons),
                                                 conflicts=_split_csv(args.conflicts))
    elif args.auto:                     cmd_auto(proj, args.refresh)
    elif args.symptoms:                 cmd_symptoms(args.symptoms)
    elif args.customize:                cmd_customize(args.customize, proj, emit_fork=not args.no_fork)
    elif args.recommend:                cmd_recommend(proj, args.refresh, args.max)
    elif args.discover is not None:     cmd_discover(args.discover or None, args.refresh)
    elif args.find is not None:         cmd_discover(args.find or None, args.refresh)
    elif args.scan:                     cmd_scan(proj)
    elif args.check:                    cmd_check(args.check)
    elif args.audit:                    cmd_audit()
    elif args.health:                   cmd_health()
    elif args.stale:                    cmd_stale()
    elif args.platforms:                cmd_platforms(verbose=args.verbose)
    elif args.migrate is not None:      cmd_migrate(args.migrate or None, all_detected=args.all_detected)
    elif args.author:                   cmd_author()
    elif args.export_eval:              cmd_export_eval(args.export_eval)
    else:                               cmd_init()


if __name__ == "__main__":
    main()
