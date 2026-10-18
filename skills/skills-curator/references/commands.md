# Skills Curator — Command Reference

All commands are CLI flags on `scripts/registry.py`. Slash commands live in `.claude/commands/` (see "Slash Commands" below).

---

## Quick Reference

| Flag | Purpose |
|---|---|
| (no flag) | Status + help |
| `--list [--type capability\|preference]` | All registered skills, grouped by verdict |
| `--search TERM` | Find by name, tag, description, or source |
| `--detect` | Scan current project, auto-register found skills |
| `--status` | Active vs inactive in current project |
| `--add ID NAME SOURCE INSTALL [--skill-type T]` | Register a skill manually |
| `--eval ID PROJECT VERDICT SUMMARY [--pros …] [--cons …] [--conflicts …]` | Save an evaluation |
| `--history SKILL_ID` | Full evaluation history |
| `--remove SKILL_ID` | Remove from registry |
| `--validate [--strict]` | Schema integrity check |
| `--export` | Print full registry as JSON |

## Discovery

| Flag | Purpose |
|---|---|
| `--curate "QUERY" [--limit N]` | **Fast path.** One call searches the skills.sh index (~1.38M skills) plus the curated + GitHub-topic catalog, blended-ranks for this project, prints top N (default 5) with a `why:` line, install command and skills.sh link. Installed/adopted skills excluded |
| `--recommend [--refresh] [--max N]` | Project-aware recommendations (blended rank, no query) |
| `--discover [TERM] [--refresh]` | Full catalog search (curated + GitHub topics), blended rank; no TERM lists the catalog |
| `--find [TERM]` | Legacy alias of `--discover` (kept for backward compatibility) |
| `--scan` | Project signals only |

## Safety (v4)

| Flag | Purpose |
|---|---|
| `--check PATH` | Security-scan a skill folder (14 risk patterns); shows third-party audits (advisory) when the registered skill has a known source |
| `--audit` | Duplicates + conflicts + gaps; flags `find-skills` as overlapping with Skills Curator |
| `--health` | A–D health score per skill |
| `--stale` | Check GitHub releases for newer versions |

## Authoring (v4)

| Flag | Purpose |
|---|---|
| `--author` | Interactive scaffold (SKILL.md + MANIFEST.yaml + CHANGELOG) |
| `--customize SOURCE [--no-fork]` | Fork an external skill for the current project; archives every section so dropped functionality stays recoverable |
| `--restore FORK_ID [--apply]` | Re-evaluate the fork's archive against the project's *current* signals; surface (or splice back) sections that now fit (v4.6+) |

## Platforms (v4.3)

| Flag | Purpose |
|---|---|
| `--platforms` | Show detected + primary platforms |
| `--platforms --verbose` | Show all 55 supported platforms |
| `--migrate` | Interactive: prints platforms table, prompts for target(s) |
| `--migrate AGENT` | Single target (e.g. `cursor`) |
| `--migrate A,B,C` | Multi-target — comma-separated id list |
| `--migrate detected` | Every platform detected on this machine |
| `--migrate --all-detected` | Same as above, flag form |

Skills Curator knows 55 platforms (sourced from `vercel-labs/skills` `dist/cli.mjs`). Primary first-class: `claude-code`, `github-copilot`. The full list rendered by `--platforms --verbose` includes: `aider-desk`, `amp`, `antigravity`, `augment`, `bob`, `claude-code`, `openclaw`, `cline`, `codearts-agent`, `codebuddy`, `codemaker`, `codestudio`, `codex`, `command-code`, `continue`, `cortex`, `crush`, `cursor`, `deepagents`, `devin`, `dexto`, `droid`, `firebender`, `forgecode`, `gemini-cli`, `github-copilot`, `goose`, `hermes-agent`, `junie`, `iflow-cli`, `kilo`, `kimi-cli`, `kiro-cli`, `kode`, `mcpjam`, `mistral-vibe`, `mux`, `opencode`, `openhands`, `pi`, `qoder`, `qwen-code`, `replit`, `rovodev`, `roo`, `tabnine-cli`, `trae`, `trae-cn`, `warp`, `windsurf`, `zencoder`, `neovate`, `pochi`, `adal`, plus the cross-tool `agents` convention.

## Sync

| Flag | Purpose |
|---|---|
| `--sync` | Pull registry from GitHub Gist |
| `--push` | Push local registry to GitHub Gist |

---

## CLI Examples

```bash
R="<this skill folder>/scripts/registry.py"   # the path SKILL.md Setup shows; plugin installs are not under ~/.claude/skills

python "$R" --list
python "$R" --search "browser"
python "$R" --detect
python "$R" --status
python "$R" --history agent-browser

# Register a skill
python "$R" --add agent-browser "Agent Browser" \
  "https://github.com/vercel-labs/agent-browser" \
  "npx skills add vercel-labs/agent-browser --skill agent-browser"

# Save a rich evaluation
python "$R" --eval agent-browser my-scraper partial \
  "Useful for auth flows, overkill for static data" \
  --pros "Handles JS-heavy pages,Session import auth" \
  --cons "Requires Chrome,Token-heavy" \
  --conflicts "Overlaps with Playwright"

python "$R" --curate "react performance"            # skills.sh + catalog, top 5
python "$R" --curate "e2e testing" --limit 10
python "$R" --recommend
python "$R" --discover react
python "$R" --check ~/.claude/skills/agent-browser/
python "$R" --audit
python "$R" --health
python "$R" --stale
python "$R" --migrate cursor
python "$R" --validate --strict
python "$R" --sync
python "$R" --push
```

Windows PowerShell:
```powershell
$R = "<this skill folder>\scripts\registry.py"   # the path SKILL.md Setup shows; plugin installs are not under ~/.claude/skills
python $R --list
```

---

## Slash Commands

`.claude/commands/skill-*.md` registers Claude Code slash commands. After installing the skill, restart your Claude Code session and these become available:

| Slash command | Equivalent |
|---|---|
| `/skill-list` | `--list` |
| `/skill-recommend` | `--recommend` |
| `/skill-discover [term]` | `--discover [term]` |
| `/skill-check <path>` | `--check <path>` |
| `/skill-audit` | `--audit` |
| `/skill-health` | `--health` |
| `/skill-stale` | `--stale` |

You can also just talk to Claude in natural language — the skill auto-activates on relevant prompts ("should I install X", "what skills fit this project", etc.). Slash commands are a shortcut, not a requirement.

---

## Blended ranking (`--curate`, `--discover TERM`, `--recommend`)

```
score = 0.35*relevance + 0.30*fit + 0.20*trust + 0.15*popularity     (each in [0,1])
```

- **relevance** — share of query terms matched (id/name 1.0, tags 0.8, description 0.6); 1.0 with no query; skills.sh hits floor at 0.3 (the index already matched them).
- **fit** — project signals from `_scan_project` found in the entry's tags/name/description; 3 matches (or all, for small projects) = 1.0.
- **trust** — official 1.0, high .8, medium .6, community .4, unknown .2 (by author, `_classify_trust`).
- **popularity** — `min(1, log10(installs+1)/6)`; skills.sh installs, else GitHub stars, else 0.
- **Decision history** — latest SKIP for this project → score × 0.3, labelled `previously rejected`; ADOPT / active here / on disk → `already installed` (excluded from `--curate` and `--recommend`).

Every result prints a `why:` line with the components, e.g.
`why: match 1.0 · fit .67 (nextjs, react) · trust high · 185K installs  [score 0.86]`.

Install advice is project-scope: `npx skills add <owner/repo> --skill <name>` (never `-g`, never `-y`). `--curate` ends with `Scan before installing: registry.py --check <path>`.

## Network

skills.sh search (`GET https://skills.sh/api/search?q=…&limit=20`, 5s timeout) and partner audits (`GET https://www.skills.sh/tele/audit?source=…&skills=…`, 3s timeout) are best-effort JSON calls; any failure means "no results", never an error. `SKILLS_NO_TELEMETRY=1` disables both (along with GitHub topic search and SKILL.md fetches). `SKILLS_SH_API_KEY`, if set, is sent as `Authorization: Bearer` on skills.sh calls — optional.

## Security scan patterns checked by `--check`

<!-- scanner:ignore-block-start -->
Remote code execution (curl/wget pipe), destructive commands (`rm -rf /`), hardcoded secrets (OpenAI key, Anthropic key, GitHub PAT, passwords), `eval()` / `exec()`, suspicious HTTP endpoints, dynamic imports, base64 obfuscation, credential store access. See `SECURITY_RISK_PATTERNS` in `scripts/registry.py` for the full list.
<!-- scanner:ignore-block-end -->
