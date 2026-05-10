# Skills Curator — developer notes

This is the source repo for Skills Curator. The end-user README is `README.md`. This file is for **maintainers and Claude Code instances** working on the skill itself.

---

## What this folder is

A Claude Code skill that handles judgment about other skills: pre-install evaluation, security scanning, project-aware recommendation, persistent decision history, cross-agent migration. Single-file Python engine + a SKILL.md + 3 slash commands + a plugin manifest.

The pitch: *"Decide once. Re-decide never."* Other tools manage skills; Skills Curator persists your judgment.

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
├── skills/skills-curator/                  ← the skill itself
│   ├── SKILL.md                            ← agent brain (auto-loaded)
│   ├── references/                         ← progressive disclosure
│   │   ├── commands.md
│   │   ├── evaluation.md
│   │   ├── discovery.md
│   │   └── schema.md
│   └── scripts/
│       └── registry.py                     ← stdlib-only engine, ~1k lines
└── tests/                                  ← 37 pytest cases
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
