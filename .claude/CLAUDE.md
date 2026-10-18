# Skills Curator — developer notes

This is the source repo for Skills Curator. The end-user README is `README.md`. This file is for **maintainers and Claude Code instances** working on the skill itself.

---

## What this folder is

A plugin that handles judgment about other skills: pre-install evaluation, security scanning, project-aware recommendation, persistent decision history, cross-agent migration. Single-file Python engine + three SKILL.md variants + 3 slash commands + a plugin manifest.

The headline: *"The intelligence layer for Claude skills."* find-skills tells you what's popular; Skills Curator tells you what fits your project and is safe to install, and persists that judgment.

## Three editions (as of v4.5.0)

The plugin ships **three** SKILL.md variants targeting **two** different runtimes:

| Edition | Runtime | Install path | Notes |
|---|---|---|---|
| `skills-curator-lite/` | Claude Code (CLI) | Auto via `npx skills add captkernel/Skills_Curator` | Default tier — no Python. Lite is tracked at its own internal version (`2.0.0`); only the plugin's outer version follows SemVer for the whole repo. |
| `skills-curator/` | Claude Code (CLI) | `--with-python` opt-in via the same install command | Python 3.10+ tier. `VERSION` constant in `scripts/registry.py` tracks plugin version. |
| `skills-curator-claudeai/` | claude.ai (web + desktop) | Manual zip + upload via Settings → Capabilities → Skills | Lives in editions/, outside skills/, because plugin.json "skills" adds to the default skills/ scan rather than replacing it. |

**Why not all in `plugin.json` skills[]:** The claude.ai edition lives in `editions/`, outside `skills/`, because `plugin.json` `skills` ADDS to the default `skills/` scan; it does not restrict it. Anything under `skills/` loads for plugin users, and this edition must not: it uses different persistence (Project Knowledge, not `~/.claude/`), different invocation (natural language, not slash commands), and doesn't make sense as a Claude Code skill. It's distributed via the same repo but a different channel (the zip flow documented in its `INSTALL.md`).

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
│   ├── SKILL.md                            ← slim spec (≤300 lines), no engine
│   └── references/                         ← catalog.yaml, signals, platforms, security-patterns, persistence, customize, templates
├── editions/skills-curator-claudeai/       ← claude.ai edition (web + desktop, v4.5.0+)
│   ├── SKILL.md                            ← slim spec (~250 lines)
│   ├── INSTALL.md                          ← user install guide (zip + upload)
│   └── references/                         ← progressive disclosure
│       ├── catalog.yaml
│       ├── signals.md
│       ├── security-patterns.md
│       └── persistence.md
└── tests/                                  ← 58 pytest cases (Python edition only)
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

1. `python -m pytest tests/` — all 58 pass
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

## Install counts and skills.sh

skills.sh exposes a public JSON search API (`https://skills.sh/api/search?q=&limit=`) — the same one the official `npx skills find` command uses. Since v4.7.0 it is a third discovery source. Install counts feed popularity, which is capped at 15% of the blended score (0.35 relevance + 0.30 fit + 0.20 trust + 0.15 popularity): judgment over popularity, not instead of it. `SKILLS_SH_API_KEY` is optional.

Still never scrape skills.sh HTML (removed in v4.0, brittle). Partner audits come from `https://www.skills.sh/tele/audit` — undocumented, advisory only, never block on it.
