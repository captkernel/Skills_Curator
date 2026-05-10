<div align="center">

# Skills Curator

**Decide once. Re-decide never.**

The intelligence layer for Claude skills — explore, identify, recommend, and persist your judgment about every skill you ever consider.

[![Version](https://img.shields.io/github/v/release/captkernel/Skills_Curator?style=flat-square&label=version)](https://github.com/captkernel/Skills_Curator/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/captkernel/Skills_Curator/validate.yml?branch=main&style=flat-square&label=ci)](.github/workflows/validate.yml)
[![Tests](https://img.shields.io/badge/tests-37%20passing-success?style=flat-square)](tests/)
[![Tiers](https://img.shields.io/badge/tiers-Lite%20%2B%20Python-blue?style=flat-square)](#two-tiers)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/captkernel/Skills_Curator?style=flat-square)](https://github.com/captkernel/Skills_Curator/commits)
[![Stars](https://img.shields.io/github/stars/captkernel/Skills_Curator?style=flat-square)](https://github.com/captkernel/Skills_Curator/stargazers)

```bash
npx skills add captkernel/Skills_Curator
```

**Status: Stable · v4.4 · 55 supported platforms · Lite (no deps) is default — Python tier is opt-in**

</div>

---

> **TL;DR.** Skills Curator is an **intelligence layer that sits on top of your project**. It watches what you're building, identifies external skills that would help, and surfaces them at the moment they're relevant — without you needing to know they exist, hunt for them, or vet them yourself.
>
> **The differentiator: infuse, don't invoke.** When you adopt a recommended skill, it doesn't get bolted on with the original author's voice intact. Skills Curator **decomposes the external skill into its individual functionalities**, scores each one against your project's stack and goals, and rewrites the keepers in your project's voice. You absorb the *capability* without inheriting another creator's *vision*.
>
> Most skill tools answer *"how do I install this?"* Skills Curator answers *"should I — and on whose terms?"*
>
> **Ships in two tiers.** **Lite** (default) is pure markdown — no Python, no install friction, agent does the work. **Python full** is the same model with a tested ~2.3k-line engine for users who want speed on large catalogs and Gist sync. Install one or both.

---

<details>
<summary><b>Table of contents</b></summary>

- [Quick install](#quick-install)
- [Two tiers](#two-tiers)
- [Demo](#demo)
- [Why this exists](#why-this-exists)
- [Features at a glance](#features-at-a-glance)
- [The intelligence layer](#the-intelligence-layer-the-usp)
- [`--customize` — infuse, don't invoke](#--customize--infuse-dont-invoke)
- [Quickstart](#quickstart)
- [Platforms](#platforms)
- [Architecture](#architecture)
- [Command reference](#command-reference)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Project status](#project-status)
- [Requirements](#requirements)
- [Repository layout](#repository-layout)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

</details>

---

## Quick install

```bash
# Recommended (one-liner, installs Lite by default, adds Python tier if available):
npx skills add captkernel/Skills_Curator

# Or clone + run an installer:
git clone https://github.com/captkernel/Skills_Curator
cd Skills_Curator
bash install.sh                                              # auto: Lite + Python if 3.10+ found
bash install.sh --lite-only                                  # Lite only (no Python check)
bash install.sh --with-python                                # require Python 3.10+ + install both
powershell -ExecutionPolicy Bypass -File install.ps1         # Windows (same modes via -Tier)
```

After install, the skill auto-loads in any new Claude Code session and announces itself once on first activation.

---

## Two tiers

Both ship in the same plugin. **Lite is the default** — pick it unless you have a specific reason to add the Python tier.

| | `skills-curator-lite` (default) | `skills-curator` (Python tier) |
|---|---|---|
| Engine | None — agent does everything via Bash / Read / Glob / Grep | Python 3.10+ (stdlib only, ~2.3k LOC) |
| Install friction | Zero | Python 3.10+ check |
| First-activation orientation | ✅ | ✅ |
| Project fingerprint (`--auto` equivalent) | ✅ byte-count + prefix compare | ✅ MD5-based |
| Symptom mapping (complaint → skill) | ✅ 17 patterns | ✅ 17 patterns |
| Embedded catalog | ✅ 19 entries with pros/cons | ✅ same 19 entries |
| Live catalog (GitHub topic search) | ✅ via `curl` | ✅ via `urllib` |
| Pros/cons in recommendations | ✅ | ✅ |
| Customization hints (stack mismatch detection) | ✅ | ✅ |
| Pre-install security scan | ✅ 14 grep patterns | ✅ 14 patterns |
| Persistent registry | ✅ JSON, agent-managed | ✅ JSON, engine-managed |
| Cross-agent migration | ✅ 55 platforms | ✅ 55 platforms |
| `--customize` (project-fork) | ✅ agent walks sections | ✅ engine scores sections |
| **Cross-device Gist sync** | ❌ | ✅ |
| **Speed on 100+ skills** | Slower (N agent steps) | Single-pass (~1s) |
| **Regression tests** | None | 35 pytest cases |
| **Transparency** | Every step is in SKILL.md you can read | Engine code in `registry.py` |

The two skills don't conflict — they use different registry paths. Install both if you want.

---

## Demo

### What you see on first activation

```
🧭 Skills Curator loaded — your intelligence layer for Claude skills.
I maintain a trust-rated catalog (skills.sh + GitHub), identify what fits
your project (stack, deps, CLAUDE.md), and on request return ranked lists
with pros, cons, and per-project customization advice — persisting every
decision so you don't re-evaluate. Working on your request now.
```

### What `--auto` produces on a real project

```
🔍 Skills Curator · auto-scan
   Project: my-saas-app  (Next.js, Tailwind, Stripe)
   Fingerprint: changed since last scan (added: tailwind, stripe)

   Top 3 picks for this stack:
     🏛️ frontend-design                  trust: official  match: 4 tags
     ✅  vercel-react-best-practices      trust: high      match: 3 tags
     ✅  web-design-guidelines            trust: high      match: 3 tags

   Want me to evaluate any of these?
```

### What `--recommend` looks like with pros/cons (v4.3)

```
🔍 Scanning: my-saas-app...
   Stack: typescript, react

══════════════════════════════════════════════════════════
  Recommendations for: my-saas-app
══════════════════════════════════════════════════════════

  ⚡ CAPABILITY — new abilities

  01. ✅ Agent Browser
       Why     : [automation, browser, scraping]
       What    : Browser automation via CDP. Element refs, 6 auth methods…
       Trust   : high
       ✓ Pro   : Six auth methods including session import
       ✓ Pro   : CDP gives access to JS-heavy pages
       ✗ Con   : Requires Chrome — adds CI dependency
       ✗ Con   : Heavyweight for static-page scraping
       Install : npx skills add vercel-labs/agent-browser --skill agent-browser

  🎨 PREFERENCE — better defaults

  01. 🏛️ Frontend Design
       Why     : [frontend, react, ui]
       What    : Bold design philosophy before writing UI code…
       Trust   : official
       ✓ Pro   : Anthropic-curated
       ✓ Pro   : Prevents generic-looking UI defaults
       ✗ Con   : Strong opinions may conflict with team style guide
       💡 Tip   : Stack mismatch (vue in skill vs react in project) —
                  run `--customize frontend-design` to fork with rewritten examples.
       Install : npx skills add anthropics/skills --skill frontend-design
```

---

## Why this exists

Existing skill tools (`npx skills`, `asm`, `vercel-labs/find-skills`, etc.) all wait for you to ask. They solve plumbing — install, list, sync — and rely on you to know what to look for. **That's the wrong default**, because:

- You don't know what skills *exist* until you go searching.
- Searching by popularity surfaces the same generic recommendations everyone else gets.
- You forget — six months later, you're re-evaluating a skill you already decided about.
- And every skill you bolt on imports its author's voice. Stack five external skills and your project speaks in five accents — examples drawn from stacks you don't use, opinions you didn't endorse, vocabulary that isn't yours.

Skills Curator inverts the model on all four counts. It watches the project, learns the stack, and tells *you* what's worth considering — judgment runs in the background, output only when something actually changed or you described a pain point. And when you do adopt a skill, the customization flow ensures it arrives in your project's voice, not the author's.

**The mental model shift: stop treating external skills as monolithic plugins to invoke. Treat them as capability libraries to absorb selectively.** Your project keeps one author. Yourself.

---

## Features at a glance

| | Other skill managers | **Skills Curator** |
|---|---|---|
| Install / list skills | ✅ | ✅ |
| **Auto-activates without being asked** (project fingerprint, drift detection) | ❌ | ✅ `--auto` |
| **Listens for symptoms** (*"slow tests"* → recommends test-perf skills) | ❌ | ✅ `--symptoms` |
| **Trust-rated catalog** (curated + live GitHub topic search) | ⚠️ varies | ✅ 19 curated + live |
| **Pre-install evaluation** with pros / cons / conflicts / verdict | ❌ | ✅ Persisted forever |
| **Project-aware recommendation** (ranked by tag overlap × trust, not popularity) | ❌ | ✅ |
| **Skill decomposition + project-voice rewrite** (the USP — adopt capability without inheriting voice) | ❌ | ✅ `--customize` |
| **Pros, cons, and customization hints inline in recommendations** | ❌ | ✅ |
| **Pre-install security scan** (14 risk patterns, self-clean as of v4.4.1) | ⚠️ post-install only | ✅ Pre-install, automatic |
| **Stack audit** — find duplicates, preference conflicts, unreviewed skills | ❌ | ✅ One pass |
| **Health scoring** — A–D grade per skill with what's missing | ❌ | ✅ |
| **PR-ready markdown export** of every decision | ❌ | ✅ Paste into ADRs |
| **Cross-agent migration** with verified paths | ⚠️ partial | ✅ **55 platforms** |
| **Cross-device sync** via private GitHub Gist | ❌ | ✅ |
| Stdlib-only Python — no `pip install` | varies | ✅ |
| Honest about install counts (no fake popularity scraping) | ❌ | ✅ Refuses to lie |

---

## The intelligence layer

Half of what makes Skills Curator distinctive is **judgment that activates without prompting** — the engine watches the project and surfaces what's relevant before you ask. The other half (the `--customize` flow below) ensures what you adopt arrives in your project's voice. Both are required for the pitch to hold; either one alone reduces to a lesser tool.

#### `--auto` — project fingerprint + drift detection
At session start, the agent runs `python registry.py --auto`. Skills Curator hashes the project's key files (`package.json`, `requirements.txt`, `CLAUDE.md`, lockfiles, framework configs) and compares against the last known state. If nothing changed, output is one line and nothing happens. If a dep was added, a framework adopted, or CLAUDE.md edited, it re-runs the recommendation engine and surfaces the top 3.

#### `--symptoms "<phrase>"` — complaint-driven recommendation
When the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, or *"no one writes good commit messages"*, the agent runs `--symptoms`. A built-in 17-pattern table maps complaints to skill categories.

#### `--find / --discover` — free-text catalog search
Familiar verb from `npx skills find` for power users who already know what they want.

These three are the intelligence layer. Everything else (evaluate, audit, migrate, export) is execution on top.

---

## `--customize` — infuse, don't invoke

This is the unlock that separates Skills Curator from every other skill manager. The standard model — `npx skills add <author/skill>` — installs an external skill *as-is*: their examples, their stack assumptions, their opinions, their voice. Then your project speaks with their accent.

Skills Curator's `--customize` flow runs differently:

1. **Decomposes the source SKILL.md** into its constituent sections (frontmatter, overview, when-to-use, patterns, examples, anti-patterns, etc.).
2. **Fingerprints your project** — languages, frameworks, deps, goals from CLAUDE.md.
3. **Scores every section** against that fingerprint and tags the action: `keep-emphasize`, `keep-trim`, `rewrite-stack`, `drop-or-rewrite`, or `rewrite-frontmatter`.
4. **Writes a forked SKILL.md** at `~/.claude/skills/<name>-for-<project>/SKILL.md` containing the plan.
5. **The agent rewrites each section in your project's voice** — keep the high-fit material verbatim, rewrite stack-mismatched examples in your stack, drop the irrelevant parts entirely.

The capability transfers. The author's voice doesn't.

### Concrete example

Run `--customize superpowers:test-driven-development` against a Python project, you get a per-section plan like:

```
01. ✏️ [rewrite-frontmatter] score=-1  (YAML frontmatter)
    Action  : Update name to '<original>-for-<project>', point homepage to fork

02. 🔴 [drop-or-rewrite   ] score=0   # Test-Driven Development (TDD)
    Action  : Zero project relevance signals — agent should drop or rewrite

03. 🟢 [keep-emphasize    ] score=7   ## Red-Green-Refactor
    Matched : testing, ai
    Action  : High project fit — keep verbatim and reinforce relevant examples

04. 🔴 [drop-or-rewrite   ] score=0   ## When to Use
    Action  : Zero project relevance signals — agent should drop or rewrite

05. 🟡 [keep-trim         ] score=2   ## Common Rationalizations
    Matched : testing
    Action  : Some fit — keep the matching parts, trim the rest

06. 🟢 [keep-emphasize    ] score=6   ## Why Order Matters
    Matched : testing, documents
    Action  : High project fit — keep verbatim and reinforce relevant examples
...
```

The high-fit sections (Red-Green-Refactor, Why Order Matters) get kept and emphasized. The narrative-only sections that don't ground in your project (`# Test-Driven Development (TDD)`, `## When to Use`) get dropped or rewritten. The frontmatter gets renamed so the fork is clearly *yours-for-this-project*, not the original.

You end up with a skill that **does what the source promised**, written **as if you'd authored it from scratch for this project**. No naming collisions, no stack mismatch, no voice pollution. The original author's contribution becomes invisible the way a great translator's does — the meaning transfers, the accent doesn't.

```bash
python registry.py --customize <source>            # source = registered id, local path, or owner/repo@skill
python registry.py --customize <source> --no-fork  # preview the plan without writing the fork file
```

This is the USP. The intelligence layer surfaces what's relevant. The customize flow ensures what you adopt belongs to *your* project.

---

## Quickstart

In any Claude Code session, ask anything below — the skill activates automatically:

> *"Should I install agent-browser for this project?"*
> → evaluates against your CLAUDE.md, runs a security scan, gives ADOPT / PARTIAL / SKIP with evidence

> *"What skills would help this project?"*
> → scans your stack, ranks recommendations by fit, returns capability + preference splits with pros/cons

> *"Audit my skills"*
> → finds duplicates, preference conflicts, security-unreviewed community skills, stale versions, low health scores

> *"List supported platforms"*
> → shows all 55 platforms with detection status

> *"Migrate my skills to Cursor and Codex"*
> → multi-target copy, with safety checks for existing files

You can also use the slash commands explicitly: `/skill-evaluate`, `/skill-recommend`, `/skill-audit`.

---

## Platforms

Skills Curator supports every agent platform `skills.sh` ships an adapter for — **55 in total** as of v4.3, mirrored from `vercel-labs/skills` `dist/cli.mjs`.

```bash
python registry.py --platforms                # detected + primary
python registry.py --platforms --verbose      # all 55
python registry.py --migrate cursor,codex     # multi-target install
python registry.py --migrate detected         # every platform on this machine
```

**Primary first-class:** `claude-code`, `github-copilot`. **Verified paths:** every platform listed in `references/commands.md`. Cross-tool `agents` convention is included as a synthetic destination.

---

## Architecture

```
                                    ┌──────────────────────┐
                                    │   project_dir        │
                                    │   (your codebase)    │
                                    └──────────┬───────────┘
                                               │
                              ┌────────────────┴─────────────────┐
                              │   _scan_project() — fingerprint  │
                              │   (deps, frameworks, CLAUDE.md)  │
                              └────────────────┬─────────────────┘
                                               │
                  ┌────────────────────────────┼─────────────────────────────┐
                  │                            │                             │
        ┌─────────▼──────────┐       ┌─────────▼─────────┐         ┌─────────▼──────────┐
        │   --auto           │       │   --recommend     │         │   --symptoms       │
        │   drift detect     │       │   tag-overlap     │         │   complaint→tag    │
        │   only-on-change   │       │   × trust tier    │         │   17-pattern table │
        └─────────┬──────────┘       └─────────┬─────────┘         └─────────┬──────────┘
                  │                            │                             │
                  └────────────────┬───────────┴───────────────┬─────────────┘
                                   │                           │
                          ┌────────▼─────────┐        ┌────────▼──────────┐
                          │   _load_catalog  │        │   --evaluate      │
                          │   (curated +     │◄───────┤   security scan + │
                          │    GitHub topic  │        │   project fit +   │
                          │    search)       │        │   verdict         │
                          └────────┬─────────┘        └────────┬──────────┘
                                   │                           │
                                   └─────────────┬─────────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │   registry.json    │
                                       │   (your judgment)  │
                                       └─────────┬──────────┘
                                                 │
                                       ┌─────────▼──────────┐
                                       │   --export-eval    │
                                       │   PR-ready md      │
                                       └────────────────────┘
```

The whole engine fits in `skills/skills-curator/scripts/registry.py` — ~2.3k lines, stdlib only.

---

## Command reference

```bash
R="$HOME/.claude/skills/skills-curator/scripts/registry.py"

# Intelligence layer (proactive — call at session start)
python "$R" --auto                                # scan only on project drift
python "$R" --symptoms "tests are slow"           # map complaint to skills

# The three verbs
python "$R" --recommend                           # what fits this project (with pros/cons)
python "$R" --eval ID PROJECT VERDICT "summary" \
              --pros "..." --cons "..." \
              --conflicts "..."                   # save a decision
python "$R" --audit                               # review whole stack

# Platforms (v4.3)
python "$R" --platforms                           # detected + primary
python "$R" --platforms --verbose                 # all 55
python "$R" --migrate cursor,codex                # multi-target
python "$R" --migrate detected                    # every detected platform

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

# Authoring
python "$R" --author                              # scaffold a new SKILL.md
python "$R" --customize <source>                  # fork external skill for this project

# Sync
python "$R" --sync   |   --push                   # private GitHub Gist
python "$R" --validate [--strict]
python "$R" --export                              # full registry as JSON
```

Full reference: [`skills/skills-curator/references/commands.md`](skills/skills-curator/references/commands.md).

---

## FAQ

<details>
<summary><b>Why no install counts?</b></summary>

The skills.sh leaderboard ranks skills by anonymous install telemetry. That signal is **not** publicly accessible — the only way to read it programmatically is via an authenticated `sk_live_` API key emailed by Vercel. We could scrape HTML for approximate numbers, but a tool whose pitch is *judgment* shouldn't lead with fake popularity. So we don't. Recommendations rank by **tag overlap × trust tier** — a 200-install skill that fits your stack beats a 50,000-install one that doesn't. If you want raw popularity, [skills.sh](https://skills.sh) is one click away.

</details>

<details>
<summary><b>Do I need Python?</b></summary>

For the full version, yes — Python 3.10+ (stdlib only, no `pip install`). For the Lite version, no — the agent does everything via Bash/Read/Glob/Grep. As of v4.4, Lite has **feature parity** with the Python tier — including `--auto`, `--symptoms`, and `--customize`. The only gap is cross-device Gist sync (which needs a longer flow than belongs in a markdown skill).

</details>

<details>
<summary><b>How is this different from `npx skills`?</b></summary>

`npx skills` is install plumbing — find, install, list, sync. Skills Curator is the layer above it: *should* you install, does it conflict with what you already have, and **how do you adopt it without inheriting the author's voice**. We use `npx skills` underneath; we add the intelligence layer that watches your project, surfaces what's relevant, and the customize layer that decomposes the skill before you adopt it.

</details>

<details>
<summary><b>Why "infuse, don't invoke"? What's wrong with just installing skills?</b></summary>

Two problems with the install-as-is model:

**1. Voice pollution.** Every external skill ships with its author's stack, examples, vocabulary, and opinions. A skill written for Vue assumes Vue. A skill written by an Anthropic engineer reads like Anthropic documentation. Stack five external skills and your project speaks five accents — none of them yours. When the agent then reads them all, it averages those voices into something generic.

**2. Capability vs commitment.** When you install a skill as-is, you're committing to *all* of it: their conventions, their edge cases, their opinions about adjacent topics. Often you only want one specific thing they do well. The rest is either irrelevant or actively at odds with how you want your project to read.

`--customize` solves both. It decomposes the source SKILL.md, scores each section against your project, and only retains the parts that fit — rewritten in your voice. You absorb capability without inheriting commitment. The original author's contribution is real but invisible, the way a translator's is.

</details>

<details>
<summary><b>If `--customize` rewrites in my voice, isn't that just "copy and edit"?</b></summary>

It's `copy → automated decomposition → relevance scoring per section → action plan → guided rewrite`. The engine produces the structured plan (which sections to keep, trim, drop, or rewrite); the agent executes the rewrite using your project's CLAUDE.md, your stack, and your existing skill conventions as the source of style.

The difference from naïve copy-and-edit is that you don't accidentally keep the author's mismatched examples just because they happened to be in the section you wanted. The scoring forces a deliberate choice on every section.

</details>

<details>
<summary><b>Does this work on platforms other than Claude Code?</b></summary>

Yes — `--platforms` lists 55 supported agents and `--migrate` copies skills to any of them. First-class targets are Claude Code and GitHub Copilot; everything else is reachable via the same migration verbs.

</details>

<details>
<summary><b>Is my registry private?</b></summary>

Yes. Stored at `~/.claude/skills/skills-curator/registry.json`, never sent anywhere unless you explicitly enable Gist sync (set `SKILLS_CURATOR_GIST_ID` + `SKILLS_CURATOR_GITHUB_TOKEN`). Disable all outbound calls with `SKILLS_NO_TELEMETRY=1`.

</details>

<details>
<summary><b>How does the live catalog scrape work?</b></summary>

A single call to GitHub's Search API per session: `topic:claude-skill`, `claude-code-skill`, `agent-skill`, sorted by stars. Author membership in `_TRUSTED_AUTHORS` (Anthropic, Vercel, Microsoft, Google, ComposioHQ, +5 more) auto-classifies trust. Everything else is `unknown` until you evaluate it. Cached in `catalog.json` for 24 hours. Honors `SKILLS_NO_TELEMETRY=1`. We deliberately do **not** scrape `skills.sh` HTML — that was removed in v4.0 as brittle and dishonest.

</details>

<details>
<summary><b>What if I disagree with a verdict?</b></summary>

Just evaluate again — every record is an entry in `evaluation_history`. The latest entry wins for the current verdict, but the full history is preserved. You can always read why past-you decided what they did via `--history <skill-id>`.

</details>

---

## Roadmap

What's likely in the next releases. Subject to change based on user feedback — open an issue if you have an opinion.

- **v4.5** — Surface customization hints (the `--customize` recommendation) directly in `--auto` and `--symptoms` output, not only in `--recommend`. Make the agent **default to suggesting `--customize` over a raw install** when the project's stack diverges from the source skill. Persist `_TRUSTED_AUTHORS` to a config file so users can curate their own trust list.
- **v4.6** — Skill-author-side helpers: `--validate-skill <path>` to scan your own SKILL.md against best practices before publishing. Bidirectional `--customize` — track when a forked skill drifts from the upstream source so you can pull future improvements without losing your rewrites.
- **v5.0** — Schema v4: store catalog snapshots per evaluation so old verdicts remain auditable even after the catalog moves on.

---

## Project status

| | |
|---|---|
| **Maturity** | Stable. v4.4.1 current. Schema v3 (stable since v4.0). |
| **Tiers** | Lite (default, zero deps) + Python full (opt-in, performance tier). |
| **CI** | 3 OS × 4 Python versions on every PR (Python tier only). |
| **Tests** | 37 pytest cases — registry core, migration, security (incl. `scanner:ignore` regression coverage), project scan, validate, export-eval, history, platforms. Lite has no automated tests (no engine to test). |
| **Lite SKILL.md size** | ~750 lines (every step documented as agent instructions). |
| **Python engine size** | ~2.3k lines, stdlib only. |
| **Catalog size** | 19 curated + live GitHub topic discovery (cached 24h). |
| **Supported platforms** | 55, mirrored from `vercel-labs/skills`. |
| **License** | MIT. |
| **Maintainer** | [@captkernel](https://github.com/captkernel). |

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
├── skills/skills-curator-lite/
│   └── SKILL.md                ← No-Python companion
├── .claude/commands/           ← /skill-evaluate, /skill-recommend, /skill-audit
├── .claude-plugin/plugin.json  ← Plugin manifest
├── .github/workflows/          ← CI matrix: 3 OS × 4 Python versions
├── tests/                      ← 37 pytest cases
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

- `api.github.com` (Gist sync, release-version checks, **catalog topic search**)
- `skills.sh` (catalog enrichment — currently disabled, see [FAQ](#faq))

It never sends your code, project content, or registry contents to any external service. Disable all outbound calls with `SKILLS_NO_TELEMETRY=1`.

The `--check` scanner is **conservative** — it flags patterns that *could* be dangerous even when benign (like `eval()` in a registry script). That's intentional. Review flagged files and decide; don't miss something.

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Contributing

PRs welcome. High-value contributions:

- **New `SECURITY_RISK_PATTERNS`** — with a justification + a test in `tests/test_security_scan.py`
- **New `KNOWN_SKILLS` catalog entries** — high-trust only, with source link and pros/cons
- **New `FRAMEWORK_SIGNALS` / `GOAL_SIGNALS`** for the project scanner
- **New `_TRUSTED_AUTHORS`** entries — for trust auto-classification of GitHub-discovered skills
- **Verified `PLATFORMS` corrections** — with a doc URL

See [CONTRIBUTING.md](CONTRIBUTING.md). All PRs must pass `pytest tests/` and `python registry.py --validate --strict`.

---

## License

[MIT](LICENSE).
