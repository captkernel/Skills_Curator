# Skills Curator — developer notes

This is the source repo for Skills Curator. The end-user README is `README.md`. This file is for **maintainers and Claude Code instances** working on the skill itself.

---

## What this folder is

A plugin that handles judgment about other skills: pre-install evaluation, security scanning, project-aware recommendation, persistent decision history, cross-agent migration. Single-file Python engine + three SKILL.md variants + 3 slash commands + a plugin manifest.

The pitch: *"Decide once. Re-decide never."* Other tools manage skills; Skills Curator persists your judgment.

## Three editions (as of v4.5.0)

The plugin ships **three** SKILL.md variants targeting **two** different runtimes:

| Edition | Runtime | Install path | Notes |
|---|---|---|---|
| `skills-curator-lite/` | Claude Code (CLI) | Auto via `npx skills add captkernel/Skills_Curator` | Default tier — no Python. Lite is tracked at its own internal version (`2.0.0`); only the plugin's outer version follows SemVer for the whole repo. |
| `skills-curator/` | Claude Code (CLI) | `--with-python` opt-in via the same install command | Python 3.10+ tier. `VERSION` constant in `scripts/registry.py` tracks plugin version. |
| `skills-curator-claudeai/` | claude.ai (web + desktop) | Manual zip + upload via Settings → Capabilities → Skills | **NOT in `plugin.json` `skills[]`** — that array is for Claude Code's plugin loader. Shipping the claude.ai variant via that path would incorrectly drop it into `~/.claude/skills/`. |

**Why not all in `plugin.json` skills[]:** The `skills[]` array tells Claude Code's plugin loader which subfolders to auto-install into `~/.claude/skills/`. The claude.ai edition uses different persistence (Project Knowledge, not `~/.claude/`), different invocation (natural language, not slash commands), and doesn't make sense as a Claude Code skill. It's distributed via the same repo but a different channel (the zip flow documented in its `INSTALL.md`).

**Registry schema is shared across editions:** `v3.0` JSON. A registry written by any edition can be read by any other. Power users can roam a single registry across all three runtimes via Gist sync (Python edition has `--sync`; claude.ai edition has Mode C).

---

## Quick local install (development)

```powershell
# Windows — copies skill + slash commands into ~\.claude\skills + ~\.claude\commands
powershell -ExecutionPolicy Bypass -File install_local.ps1

# Then deploy to GitHub
$env:GITHUB_TOKEN = "your-fine-grained-pat"
python deploy.py
```

```bash
# macOS / Linux
bash install.sh                                     # same as install_local.ps1, but cross-platform
GITHUB_TOKEN="your-pat" python3 deploy.py
```

---

## File layout

```
Skills_Curator/                             ← repo root
├── README.md                               ← public README (end users)
├── CLAUDE.md                               ← this file (maintainers)
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE                                 ← MIT
├── deploy.py                               ← maintainer-only; pushes to GitHub
├── install.sh / install.ps1                ← end-user installers (require clone)
├── install_local.ps1                       ← maintainer dev install
├── .gitignore
├── .claude-plugin/plugin.json              ← Claude Code plugin manifest
├── .claude/commands/
│   ├── skill-evaluate.md                   ← slash commands (3 verbs)
│   ├── skill-recommend.md
│   └── skill-audit.md
├── .github/
│   ├── workflows/validate.yml              ← CI: 3 OS × 4 Python versions
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug-report.yml
│       ├── skill-submission.yml
│       └── report-bad-skill.yml
├── docs/gist-sync.md
├── skills/skills-curator/                  ← Python edition (Claude Code)
│   ├── SKILL.md                            ← agent brain (auto-loaded)
│   ├── references/                         ← progressive disclosure
│   │   ├── commands.md
│   │   ├── evaluation.md
│   │   ├── discovery.md
│   │   └── schema.md
│   └── scripts/
│       └── registry.py                     ← stdlib-only engine, ~2.3k lines
├── skills/skills-curator-lite/             ← Lite edition (Claude Code default)
│   └── SKILL.md                            ← embedded catalog + spec, no engine
├── skills/skills-curator-claudeai/         ← claude.ai edition (web + desktop, v4.5.0+)
│   ├── SKILL.md                            ← slim spec (~250 lines)
│   ├── INSTALL.md                          ← user install guide (zip + upload)
│   └── references/                         ← progressive disclosure
│       ├── catalog.yaml
│       ├── signals.md
│       ├── security-patterns.md
│       └── persistence.md
└── tests/                                  ← 37 pytest cases (Python edition only)
    ├── conftest.py                         ← isolated tmp_path fixture
    ├── test_registry_core.py
    ├── test_migration.py
    ├── test_security_scan.py
    ├── test_project_scan.py
    ├── test_validate.py
    ├── test_history_display.py
    └── test_export_eval.py
```

---

## Pre-deploy checklist

Before running `deploy.py`:

1. `python -m pytest tests/` — all 37 pass
2. `python skills/skills-curator/scripts/registry.py --validate --strict` — exit 0
3. `python skills/skills-curator/scripts/registry.py --version` — matches `VERSION`, `plugin.json`, `SKILL.md` metadata, `CHANGELOG.md`
4. README claims match what's actually shipped (especially command lists)
5. CI workflow runs cleanly on a fresh clone (test on a feature branch first)

---

## Deploy to GitHub

1. Create empty repo at `github.com/captkernel/Skills_Curator` (public, no README, no .gitignore, no LICENSE — `deploy.py` adds them all)
2. Generate fine-grained PAT scoped to that repo with:
   - **Contents:** Read and write
   - **Administration:** Read and write (for setting topics + description)
3. ```powershell
   $env:GITHUB_TOKEN = "your-pat"
   python deploy.py
   ```
4. Verify: `npx skills add captkernel/Skills_Curator --list`
5. Tag the release: `git tag v4.0.0 && git push origin v4.0.0` — or use the GitHub UI

`deploy.py` uses the Trees API for a single squashed commit, not a commit per file. Don't replace it with a per-file Contents API push; the history will be ugly.

---

## Why no install counts?

skills.sh has no public JSON API for per-skill telemetry. The `sk_live_` API gates everything behind email-Vercel-for-a-key. Earlier versions scraped HTML — that was brittle and dishonest for a tool whose pitch is judgment over popularity. Removed in v4.0.

If a future version adds it back, the env var should be `SKILLS_SH_API_KEY` (already plumbed in `_http_get`), and the source of truth should be the API not scrape. Don't add scraping back unless skills.sh provides a stable public schema.

---

## Schema versions

`registry.py` migrates v1 → v2 → v3 in `_migrate()`. Migration **persists once on first read** (this was a v3.x bug — used to print the migration banner on every load).

When bumping schema:
1. Add the new field to `_migrate()` with a `setdefault` for old skills
2. Bump `SCHEMA_VERSION`
3. Update `references/schema.md`
4. Add a test in `tests/test_migration.py`
