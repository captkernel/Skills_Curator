Reference for Skills Curator. Start with the [README](../README.md).

---

## Editions: full comparison

| | `skills-curator-lite` (Claude Code default) | `skills-curator` (Claude Code Python tier) | `skills-curator-claudeai` (claude.ai edition) |
|---|---|---|---|
| Runtime | Claude Code CLI | Claude Code CLI | claude.ai web + desktop |
| Engine | None — agent runs the spec via Bash / Read / Glob / Grep | Python 3.10+ (stdlib only, ~2.3k LOC) | None — agent runs the spec via code-execution sandbox |
| Install | `npx skills add captkernel/Skills_Curator` (default) | `... --with-python` (opt-in) | Upload zip via Settings → Capabilities → Skills |
| Install friction | Zero | Python 3.10+ check | Manual zip + upload |
| Persistence | `~/.claude/skills/.../registry.json` | `~/.claude/skills/.../registry.json` | Project Knowledge / upload / Gist (see [persistence guide](../editions/skills-curator-claudeai/references/persistence.md)) |
| Project signals | Files in cwd | Files in cwd | Attached files + Project Knowledge + pasted snippets |
| Proactive `--auto` activation | ✅ byte-count fingerprint | ✅ MD5 fingerprint | ❌ (no cwd, no session boundary the skill controls) |
| Symptom mapping (17 patterns) | ✅ | ✅ | ✅ |
| Security scan (15 patterns) | ✅ | ✅ | ✅ |
| `CUSTOMIZE` headline verb | ✅ writes to `~/.claude/skills/<fork>/` | ✅ writes to `~/.claude/skills/<fork>/` | ✅ outputs `<fork>.zip` to `/mnt/user-data/outputs/` (ready to upload back to claude.ai) |
| `RECOMMEND` / `EVALUATE` / `AUDIT` | ✅ | ✅ | ✅ |
| `PLATFORMS` / `MIGRATE` (55 platforms) | ✅ | ✅ | ❌ removed — claude.ai isn't installing to CLI agents |
| Cross-device Gist sync | ❌ | ✅ | ✅ (Mode C — power users) |
| Speed on 100+ skills | Slower (N agent steps) | Single-pass (~1s) | Slower (N agent steps) |
| Regression tests | None | 37 pytest cases | None (no engine to test) |
| Slash commands | `/skill-evaluate` etc. | `/skill-evaluate` etc. | Natural language only |

The Claude Code editions don't conflict — different registry paths. Install both if you want. The claude.ai edition runs in a different product entirely, but shares the registry schema, so a Gist-synced registry roams across all three.

---

## Example: `--recommend` output

```
🔍 Scanning: my-saas-app...   Stack: typescript, react

══════════════════════════════════════════════════════════
  Recommendations for: my-saas-app
══════════════════════════════════════════════════════════

  ⚡ CAPABILITY — new abilities

  01. ✅ Agent Browser
       Why     : [automation, browser, scraping]
       Trust   : high
       ✓ Pro   : Six auth methods including session import
       ✗ Con   : Requires Chrome — adds CI dependency
       Install : npx skills add vercel-labs/agent-browser

  🎨 PREFERENCE — better defaults

  01. 🏛️ Frontend Design
       Why     : [frontend, react, ui]
       Trust   : official
       ✓ Pro   : Prevents generic-looking UI defaults
       ✗ Con   : Strong opinions may conflict with team style guide
       💡 Tip   : Stack mismatch — run `--customize frontend-design`
                  to fork with rewritten examples.
```

---

## The intelligence layer

Half of what makes Skills Curator distinctive is **context-aware judgment** — the engine reads your project and surfaces what's relevant so you don't have to search. The other half (`--customize`) ensures what you adopt arrives in your voice. Both are required for the pitch to hold.

- **`--auto`** — at session start, hashes your project's key files. If nothing changed, output is one line. If a dep was added or CLAUDE.md edited, re-runs recommendations and surfaces the top 3.
- **`--symptoms "<phrase>"`** — when the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, the agent runs this. A built-in 17-pattern table maps complaints to skill categories.
- **`--find / --discover`** — familiar free-text catalog search for power users who already know what they want.

Everything else (evaluate, audit, migrate, export) is execution on top.

---

## Architecture

```
   Claude's context              Subprocess (Python)        External resources
  ┌──────────────────┐         ┌────────────────────┐     ┌──────────────────────┐
  │ SKILL.md (3.4K)  │  Bash   │   registry.py      │     │  project files       │
  │ description (62) │ ──────► │   reads project    │ ◄─► │  GitHub API (24h)    │
  │ stdout (10-1.2K) │ ◄────── │   parses signals   │     │  registry on disk    │
  │ + agent's reads  │ stdout  │   emits stdout     │     └──────────────────────┘
  └──────────────────┘         └────────────────────┘
```

Token cost happens only inside the purple box (Claude's context). Everything else runs in Python memory, free. Full diagram + step-by-step walkthrough: **[`docs/how-it-works.html`](how-it-works.html)**.

---

## Command reference

```bash
R="$HOME/.claude/skills/skills-curator/scripts/registry.py"

# Intelligence layer (proactive)
python "$R" --auto                              # scan only on project drift
python "$R" --symptoms "tests are slow"         # map complaint to skills
python "$R" --recommend                         # what fits this project (with pros/cons)

# Evaluation + history
python "$R" --eval ID PROJECT VERDICT "summary" --pros "..." --cons "..."
python "$R" --history <skill-id>                # all past evaluations
python "$R" --export-eval <skill-id>            # PR-ready markdown

# Customization (the headline capability)
python "$R" --customize <source>                # fork external skill for this project
python "$R" --customize <source> --no-fork      # preview plan only

# Maintenance + discovery
python "$R" --audit                             # duplicates, conflicts, stale, unreviewed
python "$R" --check <path>                      # security scan a skill folder
python "$R" --discover [term]                   # search live catalog
python "$R" --migrate cursor,codex              # cross-agent copy

# Sync (Python tier only)
python "$R" --sync   |   --push                 # private GitHub Gist
```

Full reference (every command + flag): [`skills/skills-curator/references/commands.md`](../skills/skills-curator/references/commands.md).

---

## Platforms

Skills Curator supports **55 agent platforms** as of v4.3, mirrored from `vercel-labs/skills`. **Primary first-class:** `claude-code`, `github-copilot`. Every platform listed in [`references/commands.md`](../skills/skills-curator/references/commands.md) has a verified install path.

```bash
python registry.py --platforms                # detected + primary
python registry.py --platforms --verbose      # all 55
python registry.py --migrate cursor,codex     # multi-target install
python registry.py --migrate detected         # every platform on this machine
```

---

## Token cost

Reproducibly measured against 5 real projects (empty → 17,680 files) and every CLI command. Full report at **[`docs/token-cost-report.html`](token-cost-report.html)** · architecture/feature walkthrough at **[`docs/how-it-works.html`](how-it-works.html)**.

| | Number |
|---|---:|
| Always-on cost per session (both tiers combined) | **249 tokens** (0.025% of a 1M context window) |
| Max single-command stdout, on a 17,680-file Next.js project | **965 tokens** |
| Max single-command stdout, on a 48-file repo | **1,140 tokens** |
| Effect of project size on cost | **None measurable** |
| Heavy-session savings vs ad-hoc evaluation | **20,038 tokens (71%)** |
| Re-asking about a previously evaluated skill | **~13 tokens** vs ~4,060 without persistence |

The Python engine is 27,900 tokens of source code, but **runs as a Bash subprocess** — Claude only sees stdout. Project files (CLAUDE.md, package.json, etc.) are read into the subprocess's own RAM, parsed, and summarized into ~250 tokens of stdout. **The 17,680-file Next.js project costs the same as a 30-file folder** because the engine caps doc reads at 4 KB and emits only summaries.

Regenerate the measurements on any machine: `pip install tiktoken && python docs/audit/deep_token_audit.py && python docs/audit/generate_html.py`.

---

## FAQ

<details>
<summary><b>Why no install counts?</b></summary>

skills.sh telemetry isn't publicly accessible — only via an authenticated `sk_live_` API key. A tool whose pitch is *judgment* shouldn't lead with scraped fake popularity. We rank by **tag overlap × trust tier** instead — a 200-install skill that fits your stack beats a 50,000-install one that doesn't.

</details>

<details>
<summary><b>Do I need Python?</b></summary>

For the full version, yes — Python 3.10+ (stdlib only, no `pip install`). For Lite, no — the agent does everything via Bash/Read/Glob/Grep. Lite has feature parity except for cross-device Gist sync.

</details>

<details>
<summary><b>How is this different from `npx skills`?</b></summary>

`npx skills` is install plumbing — find, install, list, sync. Skills Curator is the layer above it: *should* you install, does it conflict with what you already have, and **how do you adopt it without inheriting the author's voice**. We use `npx skills` underneath.

</details>

<details>
<summary><b>If `--customize` rewrites in my voice, isn't that just "copy and edit"?</b></summary>

It's `copy → automated decomposition → relevance scoring per section → action plan → guided rewrite`. The engine produces a structured plan (keep/trim/drop/rewrite per section); the agent executes the rewrite using your CLAUDE.md and existing skill conventions as the style source. The scoring forces a deliberate choice on every section instead of letting mismatched examples slip through.

</details>

<details>
<summary><b>If the skill reads my project, doesn't that cost tokens?</b></summary>

No — and this is the most-missed point. The engine reads project files in a Python subprocess (its own RAM), parses them, and emits only ~250 tokens of summary to stdout. Claude never sees the raw bytes. A 17,680-file project with a 20 KB CLAUDE.md generates the same stdout size as a 30-file folder. Detailed walkthrough: [`docs/how-it-works.html`](how-it-works.html).

</details>

<details>
<summary><b>Does this work on platforms other than Claude Code?</b></summary>

Yes — `--platforms` lists 55 supported agents and `--migrate` copies skills to any of them. First-class targets are Claude Code and GitHub Copilot.

</details>

<details>
<summary><b>Is my registry private?</b></summary>

Yes. Stored at `~/.claude/skills/skills-curator/registry.json`, never sent anywhere unless you explicitly enable Gist sync (set `SKILLS_CURATOR_GIST_ID` + `SKILLS_CURATOR_GITHUB_TOKEN`). Disable all outbound calls with `SKILLS_NO_TELEMETRY=1`.

</details>

<details>
<summary><b>How does external skills research work?</b></summary>

Three layers: (1) **19 curated entries** built into the script with hand-written pros/cons; (2) **GitHub topic search** (`topic:claude-skill`, `claude-code-skill`, `agent-skill`) — one call per topic, sorted by stars, cached 24h, metadata only (no SKILL.md fetched at this stage); (3) **on-demand SKILL.md fetch** when `--check` / `--customize` / `--evaluate` triggers it. Trust tier auto-classified by author membership in `_TRUSTED_AUTHORS`.

</details>

<details>
<summary><b>What if I disagree with a verdict?</b></summary>

Just evaluate again — every record is an entry in `evaluation_history`. The latest entry wins for the current verdict, but the full history is preserved. Read why past-you decided what they did via `--history <skill-id>`.

</details>

---

## Requirements

- **Python 3.10+** for the full tier (Lite has no Python requirement)
- **Standard library only** — no `pip install` step
- **Network** — optional. Set `SKILLS_NO_TELEMETRY=1` to disable all outbound calls.

---

## Repository layout

```
Skills_Curator/
├── skills/skills-curator/         ← Python tier
│   ├── SKILL.md                   ← Auto-loads in Claude Code
│   ├── references/                ← Progressive-disclosure docs
│   └── scripts/registry.py        ← The whole engine, stdlib only (~2.3k LOC)
├── skills/skills-curator-lite/    ← Lite tier (no Python)
│   └── SKILL.md
├── .claude/commands/              ← /skill-evaluate, /skill-recommend, /skill-audit
├── .claude-plugin/plugin.json     ← Plugin manifest
├── docs/
│   ├── token-cost-report.html     ← Empirical token measurements
│   ├── how-it-works.html          ← Feature walkthrough + architecture
│   └── audit/                     ← Reproducibility scripts
├── tests/                         ← 37 pytest cases
├── install.sh / install.ps1
└── deploy.py                      ← Maintainer-only
```
