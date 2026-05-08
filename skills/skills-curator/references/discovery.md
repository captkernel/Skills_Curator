# Discovery and Recommendation System

---

## How It Works

The recommendation engine in `scripts/registry.py` runs in three stages:

**Stage 1 — Project Scan (`_scan_project`)**
Reads the project directory and extracts structured signals:
- Languages detected from file extensions (`.py`, `.ts`, `.go`, etc.)
- Frameworks detected from `package.json`, `requirements.txt`, `pyproject.toml`, `Pipfile`
- Goals extracted from `CLAUDE.md` and `README.md` via keyword patterns
- Existing skills installed globally and project-locally
- Outputs a unified tag set used for matching

**Stage 2 — Catalog Fetch (`_load_catalog`)**
Loads a curated catalog of trusted skills, enriched live from `skills.sh` if network is available. The merge is keyed by skill `id` — built-in seed entries take precedence, with discovered entries appended.

The catalog is cached at `~/.claude/skills/skills-curator/catalog.json` for 24 hours.
Force refresh with `--refresh`.

**Stage 3 — Match and Rank (`cmd_recommend`)**
For each catalog skill not already in the registry:
- Counts tag overlap between project signals and skill tags
- Adds weighted bonus for popularity (when available)
- Adds trust-level bonus (official > high > medium > community)
- Skips skills already registered (so you only see new suggestions)
- Splits results into Capability vs Preference groups

Recommendation history is saved to `~/.claude/skills/skills-curator/recommendations.json`.

---

## Recommendation Commands

```bash
R=~/.claude/skills/skills-curator/scripts/registry.py

# Recommend for current project
python "$R" --recommend

# Recommend with fresh catalog
python "$R" --recommend --refresh

# Search the live catalog
python "$R" --discover react

# List everything in catalog
python "$R" --discover

# Just scan project signals (no recommendations)
python "$R" --scan
```

Windows PowerShell:
```powershell
$R = "$env:USERPROFILE\.claude\skills\skills-curator\scripts\registry.py"
python $R --recommend
```

---

## How to Act on Recommendations

When the recommendation engine produces output, present it to the user like this:

1. **Show the match reason** — which project tags triggered each recommendation
2. **Group by type** — Capability skills first (new abilities), then Preference skills (better defaults)
3. **Flag trust level** — 🏛️ Official, ✅ High, 🟡 Medium
4. **Suggest evaluation** — offer to run a full pros/cons/conflicts evaluation
5. **Offer to register** — if the user wants to adopt, register it to the global registry

Example response pattern:
```
I scanned your project and found 3 strong skill recommendations:

⚡ CAPABILITY: Agent Browser (✅ high trust)
  Why: Your project does web scraping and form automation — this covers both
       with CDP-level control
  Install: npx skills add vercel-labs/agent-browser --skill agent-browser

🎨 PREFERENCE: React Best Practices (✅ high trust)
  Why: React + Next.js detected in package.json — performance rules from
       Vercel Engineering
  Install: npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices

Want me to evaluate any of these against your project goals, or add them to
your registry?
```

### Single-skill response template

When surfacing one specific skill (after `--find` or `--search` returns a clear winner), use this template:

```
I found a skill that might help: **<Skill Name>** (<trust-emoji> <trust-level>)

What it does: <one-line capability>
Why it fits: <one-line tie-back to project signals>

Install:
  npx skills add <owner/repo> --skill <skill-id>

Evaluate first (recommended):
  /skill-evaluate <skill-id>

Learn more: https://skills.sh/<owner/repo>/<skill-id>
```

Always offer `/skill-evaluate` before install for anything not 🏛️ Official trust.

---

## Skill Categories

The recommendation engine maps project signals to these domains. Use these category names + example queries when explaining recommendations or running `--find`:

| Category | Project signals that trigger | Example `--find` queries |
|---|---|---|
| Web development | `package.json`, React/Next/Vue/Svelte, `tailwind`, `.tsx`/`.jsx` | `react`, `nextjs`, `tailwind`, `frontend-design` |
| Backend / APIs | FastAPI, Express, Flask, Django, `requirements.txt` with web frameworks | `api`, `rest`, `graphql`, `auth` |
| Testing | `pytest`, `jest`, `playwright`, `vitest`, `cypress` directories | `testing`, `e2e`, `playwright`, `unit-test` |
| DevOps / deployment | `Dockerfile`, `.github/workflows/`, Terraform, K8s manifests | `deploy`, `docker`, `kubernetes`, `ci-cd` |
| Documentation | `docs/`, README-heavy repos, `mkdocs.yml` | `docs`, `readme`, `changelog`, `api-docs` |
| Code quality | linters in `package.json`/`pyproject.toml`, `.eslintrc`, `.prettierrc` | `review`, `lint`, `refactor`, `best-practices` |
| Design / UX | Figma exports, `tailwind.config.js`, design tokens | `ui`, `ux`, `design-system`, `accessibility` |
| Data / scraping | `playwright`, `puppeteer`, `requests`, `beautifulsoup`, `scrapy` | `scraping`, `browser-automation`, `data-extraction` |
| Productivity / git | many feature branches, frequent PRs, conventional commits | `commit-writer`, `pr-review`, `git-workflow` |
| Documentation generation | `docusaurus`, `sphinx`, `typedoc` | `docgen`, `api-docs`, `readme-builder` |

If the user's request doesn't map to any category, fall through to `--find <free-text>` and rank results by trust × tag overlap as usual.

---

## Tips for effective searches

1. **Start specific, broaden if empty.** `react testing` first; if zero matches, try `testing`. Don't go broad on the first pass — broad searches return noise.
2. **Try alternative terms.** Skill authors don't agree on naming. `deploy` / `deployment` / `ci-cd` / `release` may all surface different skills.
3. **Check official sources first.** `vercel-labs/agent-skills`, `anthropics/skills`, and `microsoft/*` cover most common domains. If the answer is there, stop.
4. **Use `--scan` to ground the query.** Run `--scan` first, look at the detected tags, and use those as the search vocabulary instead of the user's exact phrasing.
5. **`--find` and `--discover` are aliases.** Use whichever you remember — same engine.

---

## Trust Levels

| Level | Meaning | Examples |
|---|---|---|
| 🏛️ Official | Maintained by Anthropic or a major vendor | anthropics/skills, vercel-labs/* |
| ✅ High | Established company or widely-adopted community skill | remotion-dev, supermemoryai, firecrawl |
| 🟡 Medium | Active community contributor, reasonable adoption | community maintainers |
| ⬜ Community | Open directory — review before installing | Unknown authors |
| ❓ Unknown | Auto-discovered, not yet assessed | needs manual review |

**Security note:** Skills can include executable scripts. Before installing any community skill (medium/unknown trust), read its `SKILL.md` and `scripts/` directory, and run `--check <path>` to scan for risk patterns. Always review before install.

---

## Catalog Sources

1. **skills.sh** — Public skills catalog. Live-fetched if network is available.
2. **anthropics/skills** — Official Anthropic skill collection
3. **vercel-labs/agent-skills** — Vercel Engineering's curated skills
4. **Built-in seed** — Hand-curated high-trust skills always available offline

---

## Scheduling Regular Checks

To get proactive skill suggestions on a schedule:

```bash
# macOS/Linux: weekly check via crontab
0 9 * * MON python ~/.claude/skills/skills-curator/scripts/registry.py --recommend --refresh > /tmp/skill-recs.txt
```

```powershell
# Windows: Task Scheduler weekly trigger
python "$env:USERPROFILE\.claude\skills\skills-curator\scripts\registry.py" --recommend --refresh
```

Recommendation history is always saved to `recommendations.json` so you can review it later.
