<div align="center">

# Skills Curator

**Decide once. Re-decide never.**

The first Claude Code skill with **judgment that activates without being asked**. It learns your project at session start, watches for drift, recommends only what fits — and persists every verdict so you never re-decide.

[![Install](https://img.shields.io/badge/install-npx%20skills%20add-blue?style=flat-square)](https://github.com/captkernel/Skills_Curator)
[![Version](https://img.shields.io/badge/version-4.0.0-green?style=flat-square)](https://github.com/captkernel/Skills_Curator/releases)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/captkernel/Skills_Curator/validate.yml?branch=main&style=flat-square)](.github/workflows/validate.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](#requirements)

```bash
npx skills add captkernel/Skills_Curator
```

</div>

---

## Why Skills Curator is different

> **Every other skill tool answers *"how do I install this?"*. Skills Curator answers *"should I?"* — proactively, before you even ask, with a verdict persisted forever.**

There are 90,000+ Claude skills and the catalog grows daily. Existing tools (`npx skills`, `asm`, `buzhangsan`, vercel-labs/find-skills, etc.) all wait for you to ask. They solve plumbing — install, list, sync — and rely on you to know what to look for. **That's the wrong default**, because:

- You don't know what skills *exist* until you go searching.
- Searching by popularity surfaces the same generic recommendations everyone else gets.
- And you forget — six months later, you're re-evaluating a skill you already decided about.

Skills Curator inverts the model: it watches the project, learns the stack, and tells *you* what's worth considering. The judgment runs in the background; you only see output when something actually changed or the user describes a pain point.

| | Other skill managers | **Skills Curator** |
|---|---|---|
| **Auto-activates without being asked** (project fingerprint, drift detection) | ❌ | ✅ `--auto` |
| **Listens for symptoms** (*"slow tests"* → recommends test-perf skills) | ❌ | ✅ `--symptoms` |
| Install / list skills | ✅ | ✅ |
| **Pre-install evaluation** with pros / cons / conflicts / verdict | ❌ | ✅ Persisted forever |
| **Project-aware recommendation** (ranked by tag overlap × trust, not popularity) | ❌ | ✅ |
| **Pre-install security scan** (14 risk patterns, 2-second AST scan) | ⚠️ post-install only | ✅ Pre-install, automatic |
| **Stack audit** — find duplicates, preference conflicts, unreviewed skills | ❌ | ✅ One pass |
| **Health scoring** — A–D grade per skill with what's missing | ❌ | ✅ |
| **PR-ready markdown export** of every decision | ❌ | ✅ Paste into ADRs |
| **Cross-agent migration** with verified paths (May 2026) | ⚠️ partial | ✅ 9 agents |
| **Cross-device sync** via private GitHub Gist | ❌ | ✅ |
| Stdlib-only Python — no `pip install` | varies | ✅ |
| Honest about install counts (no fake popularity scraping) | ❌ | ✅ Refuses to lie |

### The intelligence layer (the main USP)

Skills Curator's distinguishing feature isn't the registry — it's **judgment that activates without prompting**.

**`--auto` (project fingerprint + drift detection)**
At session start, the agent runs `python registry.py --auto`. Skills Curator hashes the project's key files (`package.json`, `requirements.txt`, `CLAUDE.md`, lockfiles, framework configs) and compares against the last known state. If nothing changed, output is one line and nothing happens. If a dep was added, a framework adopted, or CLAUDE.md edited, it re-runs the recommendation engine and surfaces the top 3 — the agent then weaves those into the conversation as a quiet observation, not a sales pitch.

**`--symptoms "<phrase>"` (complaint-driven recommendation)**
When the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, or *"no one writes good commit messages"*, the agent runs `--symptoms`. A built-in 17-pattern table maps complaints to skill categories: *testing+performance*, *ci-cd+deploy*, *frontend-design*, *commit-writer*. The user never has to know what skill to ask for — they describe the problem in their own words and Skills Curator matches it.

**`--find / --discover` (free-text catalog search)**
Familiar verb from `npx skills find` for power users who already know what they want.

These three are the intelligence layer. Everything else (evaluate, audit, migrate, export) is execution on top.

### The other things only Skills Curator does

1. **Saves your judgment as a reviewable artifact.** Every evaluation produces a structured record (pros, cons, conflicts, verdict, partial-adoption plan) that exports as PR-ready markdown — paste it in an ADR, a PR, a team doc.
2. **Recommends by *fit*, not popularity.** A 200-install skill that matches your stack beats a 50,000-install one that doesn't. We refuse to scrape skills.sh for fake popularity numbers.
3. **Scans for danger before install.** 14 risk patterns including remote code execution, hardcoded secrets, GitHub PATs, base64 obfuscation, credential-store access. The `/skill-evaluate` command runs this automatically.
4. **Audits your whole stack in one pass.** Duplicates, preference conflicts, security-unreviewed skills, version drift, low health scores — surfaced together.
5. **Re-deciding is the bug, not the feature.** When the same skill resurfaces six months later, you read your past judgment in 5 seconds.

---

## Quickstart

```bash
# Install (any of these works — pick one)
npx skills add captkernel/Skills_Curator               # one-liner
git clone https://github.com/captkernel/Skills_Curator
cd Skills_Curator && bash install.sh                   # macOS / Linux
powershell -ExecutionPolicy Bypass -File install.ps1   # Windows
```

Then in any Claude Code session:

> *"Should I install agent-browser for this project?"*
> → evaluates against your CLAUDE.md, runs a security scan, gives you ADOPT / PARTIAL / SKIP with evidence

> *"What skills would help this project?"*
> → scans your stack, ranks recommendations by fit (not popularity), returns capability + preference splits

> *"Audit my skills"*
> → finds duplicates, preference conflicts, security-unreviewed community skills, stale versions, and low health scores in one pass

You can also use the slash commands explicitly: `/skill-evaluate`, `/skill-recommend`, `/skill-audit`.

---

## The three things that actually matter

### 1. Persistent decisions, not transient suggestions

The registry at `~/.claude/skills/skills-curator/registry.json` records every evaluation you do — date, project, verdict, pros, cons, conflicts, partial-adoption plan, security findings. When the same skill comes up six months later, you read your past judgment in 5 seconds rather than re-evaluating.

### 2. Export evaluations as PR-ready markdown

```bash
python registry.py --export-eval agent-browser
```

```markdown
# Skill Evaluation: Agent Browser

- **Skill:** [`agent-browser`](https://github.com/vercel-labs/agent-browser)
- **Project:** my-scraper
- **Date:** 2026-05-08
- **Verdict:** PARTIAL

## Summary
Useful for auth flows, overkill for static data extraction.

## Pros
- Handles JS-heavy pages plain HTTP can't reach
- Session import auth covers cookie-based login

## Cons
- Requires Chrome — adds CI dependency

## Conflicts
- Overlaps with existing Playwright setup

## Adoption Plan
- Adopt: session-import auth, element references
- Skip: network inspection
```

Paste into a PR comment, an ADR, a team doc. The decision becomes a reviewable artifact instead of a private hunch.

### 3. Pre-install safety, by default

```bash
python registry.py --check ~/Downloads/some-skill/
```

Scans for 14 patterns including remote code execution, hardcoded API keys, GitHub PATs, suspicious network calls, base64 obfuscation, and credential-store access. Two seconds. The `/skill-evaluate` slash command runs this automatically before any verdict — you don't have to remember.

---

## Commands

```bash
R="$HOME/.claude/skills/skills-curator/scripts/registry.py"

# Intelligence layer (proactive — call at session start)
python "$R" --auto                                # scan only on project drift
python "$R" --symptoms "tests are slow"           # map complaint to skills

# The three verbs
python "$R" --recommend                           # what fits this project
python "$R" --eval ID PROJECT VERDICT "summary" \
              --pros "..." --cons "..." \
              --conflicts "..."                   # save a decision
python "$R" --audit                               # review whole stack

# Decision artifacts
python "$R" --export-eval <skill-id>              # PR-ready markdown
python "$R" --history <skill-id>                  # all past evaluations

# Discovery
python "$R" --discover [term]                     # search live catalog
python "$R" --find [term]                         # alias for --discover
python "$R" --scan                                # project tech signals only

# Safety
python "$R" --check <path>                        # security scan
python "$R" --health                              # A–D health per skill
python "$R" --stale                               # GitHub release version drift

# Inventory
python "$R" --list [--type capability|preference]
python "$R" --search <term>
python "$R" --status                              # this project vs global
python "$R" --detect                              # auto-register found skills
python "$R" --add ID NAME SOURCE INSTALL
python "$R" --remove <skill-id>

# Cross-agent + authoring
python "$R" --migrate cursor                      # copy skills to another agent
python "$R" --author                              # scaffold a new SKILL.md

# Sync
python "$R" --sync   |   --push                   # private GitHub Gist
python "$R" --validate [--strict]
python "$R" --export                              # full registry as JSON
```

---

## Why no install counts?

The skills.sh leaderboard ranks skills by anonymous install telemetry. That signal is **not** publicly accessible — the only way to read it programmatically is via an authenticated `sk_live_` API key emailed by Vercel.

We could scrape HTML for approximate numbers, but a tool whose pitch is *judgment* shouldn't lead with fake popularity. So we don't. Recommendations rank by **tag overlap × trust tier** — a skill with 200 installs that exactly fits your stack is a better match than one with 50,000 that doesn't.

If you want raw popularity, [skills.sh](https://skills.sh) is one click away. If you want fit, use this.

---

## Cross-agent migration

```bash
python registry.py --migrate cursor      # → ~/.cursor/skills
python registry.py --migrate codex       # → ~/.codex/skills
python registry.py --migrate gemini-cli  # → ~/.gemini/skills
```

Verified paths (May 2026): `claude-code`, `codex`, `cursor`, `gemini-cli`, `cline`, `windsurf`, `github-copilot`, `opencode`, `amp`, plus the cross-tool `agents` convention. `aider` has no native skill system and is intentionally excluded.

---

## Cross-device sync

Keep your registry in sync across all your machines via a private GitHub Gist:

```bash
# Create a private Gist with filename `registry.json` and content `{}`
# Generate a PAT with `gist` scope
export SKILLS_CURATOR_GIST_ID="your-gist-id"
export SKILLS_CURATOR_GITHUB_TOKEN="your-pat"

python registry.py --push   # upload local
python registry.py --sync   # pull remote
```

See [docs/gist-sync.md](docs/gist-sync.md) for setup details.

---

## Requirements

- **Python 3.10+** (the install script will refuse to install on older versions)
- **Standard library only** — no `pip install` step
- **Network** — optional. Set `SKILLS_NO_TELEMETRY=1` to disable all outbound calls.

---

## Repository layout

```
Skills_Curator/
├── skills/skills-curator/
│   ├── SKILL.md                ← Auto-loads in Claude Code
│   ├── references/             ← Progressive-disclosure docs
│   │   ├── commands.md
│   │   ├── evaluation.md
│   │   ├── discovery.md
│   │   └── schema.md
│   └── scripts/
│       └── registry.py         ← The whole engine, stdlib only
├── .claude/commands/           ← /skill-evaluate, /skill-recommend, /skill-audit
├── .claude-plugin/plugin.json  ← Plugin manifest
├── .github/workflows/          ← CI matrix: 3 OS × 4 Python versions
├── tests/                      ← 26 pytest cases
├── install.sh / install.ps1
├── deploy.py                   ← Maintainer-only: pushes to GitHub
├── LICENSE                     ← MIT
├── SECURITY.md
├── CHANGELOG.md
└── CONTRIBUTING.md
```

---

## Security

`registry.py` is stdlib-only Python. It reads local files and makes optional network calls to:

- `api.github.com` (Gist sync, release-version checks)
- `skills.sh` (catalog enrichment)

It never sends your code, project content, or registry contents to any external service. Disable all outbound calls with `SKILLS_NO_TELEMETRY=1`.

The `--check` scanner is **conservative** — it flags patterns that *could* be dangerous even when benign (like `eval()` in a registry script). That's intentional. Review flagged files and decide; don't miss something.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Contributing

PRs welcome. High-value contributions:

- **New `SECURITY_RISK_PATTERNS`** — with a justification + a test in `tests/test_security_scan.py`
- **New `KNOWN_SKILLS` catalog entries** — high-trust only, with source link
- **New `FRAMEWORK_SIGNALS` / `GOAL_SIGNALS`** for the project scanner
- **Verified `AGENT_PATHS` corrections** — with a doc URL

See [CONTRIBUTING.md](CONTRIBUTING.md). All PRs must pass `pytest tests/` and `python registry.py --validate --strict`.

---

## License

[MIT](LICENSE).
