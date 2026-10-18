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

**Stage 2 — Catalog Fetch (`_load_catalog`, `_fetch_skills_sh`)**
Three sources:
1. **Curated seed** (`KNOWN_SKILLS`) — hand-written pros/cons, always available offline.
2. **GitHub topics** (`claude-skill`, `claude-code-skill`, `agent-skill`) — cached with the seed at `~/.claude/skills/skills-curator/catalog.json` for 24 hours. Force refresh with `--refresh`.
3. **skills.sh index** (~1.38M skills) — queried live per search via its JSON API (`https://skills.sh/api/search?q=…&limit=20`, the same endpoint `npx skills find` uses). Query-time only, never cached into the catalog. Each hit maps to `npx skills add <source> --skill <skillId>`, trust by owner, tag `skills-sh`, its install count, and a link `https://skills.sh/<source>/<skillId>`. Used by `--curate`.

Merge: curated entries win on collision (same `owner/repo/skill`) — they keep their pros/cons and only gain the install count. We never scrape skills.sh HTML (removed in v4.0); this is a JSON API.

**Stage 3 — Blended rank (`_rank_entries`, used by `--curate`, `--discover TERM`, `--recommend`)**
`score = 0.35*relevance + 0.30*fit + 0.20*trust + 0.15*popularity`, each in [0,1]:
- relevance — query terms matched over id/name (1.0), tags (0.8), description (0.6); 1.0 when there is no query
- fit — project signals found in the entry's tags/name/description (3 matches = 1.0); with a query, fit × relevance
- trust — official 1.0, high .8, medium .6, community .4, unknown .2
- popularity — `min(1, log10(installs+1)/6)` (skills.sh installs, else GitHub stars, else 0) — capped at 15% of the score: judgment over popularity
- decision history — a SKIP for this project multiplies the score by 0.3 (`previously rejected`); ADOPT / installed skills are `already installed` and excluded from `--curate` and `--recommend`
- every result prints a `why:` line, e.g. `why: match 1.0 · fit .6 (nextjs, react) · trust high · 185K installs`
- `--recommend` additionally requires at least one tag overlap and splits into Capability vs Preference groups

Recommendation history is saved to `~/.claude/skills/skills-curator/recommendations.json`.

---

## Recommendation Commands

```bash
R="<this skill folder>/scripts/registry.py"   # the path SKILL.md Setup shows; plugin installs are not under ~/.claude/skills

# Recommend for current project
python "$R" --recommend

# Recommend with fresh catalog
python "$R" --recommend --refresh

# Fast path: skills.sh + catalog, ranked for this project (top 5)
python "$R" --curate "react performance"
python "$R" --curate "e2e testing" --limit 10

# Full catalog search (curated + GitHub topics), blended rank
python "$R" --discover react

# List everything in catalog
python "$R" --discover

# Just scan project signals (no recommendations)
python "$R" --scan
```

Windows PowerShell:
```powershell
$R = "<this skill folder>\scripts\registry.py"   # the path SKILL.md Setup shows; plugin installs are not under ~/.claude/skills
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

When surfacing one specific skill (after `--curate` or `--search` returns a clear winner), use this template:

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

The recommendation engine maps project signals to these domains. Use these category names + example queries when explaining recommendations or running `--curate`:

| Category | Project signals that trigger | Example `--curate` queries |
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

If the user's request doesn't map to any category, fall through to `--curate "<free-text>"` — it searches the skills.sh index and blended-ranks the hits.

---

## Tips for effective searches

1. **Start specific, broaden if empty.** `react testing` first; if zero matches, try `testing`. Don't go broad on the first pass — broad searches return noise.
2. **Try alternative terms.** Skill authors don't agree on naming. `deploy` / `deployment` / `ci-cd` / `release` may all surface different skills.
3. **Check official sources first.** `vercel-labs/agent-skills`, `anthropics/skills`, and `microsoft/*` cover most common domains. If the answer is there, stop.
4. **Use `--scan` to ground the query.** Run `--scan` first, look at the detected tags, and use those as the search vocabulary instead of the user's exact phrasing.
5. **Use `--curate` first.** It is the fast path (skills.sh + catalog, one call). `--discover` searches only the curated + GitHub-topic catalog; `--find` is a legacy alias of `--discover`.
6. **Rival skill.** If `find-skills` is installed too, `--audit` flags it: both trigger on "find a skill" requests — keep one.

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

1. **skills.sh** — Public index (~1.38M skills), JSON search API queried live by `--curate` (5s timeout, best effort; off with `SKILLS_NO_TELEMETRY=1`; optional `SKILLS_SH_API_KEY` sent as Bearer).
2. **anthropics/skills** — Official Anthropic skill collection
3. **vercel-labs/agent-skills** — Vercel Engineering's curated skills
4. **Built-in seed** — Hand-curated high-trust skills always available offline

---

## Scheduling Regular Checks

To get proactive skill suggestions on a schedule:

```bash
# macOS/Linux: weekly check via crontab
0 9 * * MON python "<this skill folder>/scripts/registry.py" --recommend --refresh > /tmp/skill-recs.txt
```

```powershell
# Windows: Task Scheduler weekly trigger
python "<this skill folder>\scripts\registry.py" --recommend --refresh
```

Recommendation history is always saved to `recommendations.json` so you can review it later.
