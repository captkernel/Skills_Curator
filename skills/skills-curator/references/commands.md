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
| `--recommend [--refresh] [--max N]` | Project-aware recommendations |
| `--discover [TERM] [--refresh]` | Search or list live catalog |
| `--scan` | Project signals only |

## Safety (v4)

| Flag | Purpose |
|---|---|
| `--check PATH` | Security-scan a skill folder (14 risk patterns) |
| `--audit` | Duplicates + conflicts + gaps |
| `--health` | A–D health score per skill |
| `--stale` | Check GitHub releases for newer versions |

## Authoring (v4)

| Flag | Purpose |
|---|---|
| `--author` | Interactive scaffold (SKILL.md + MANIFEST.yaml + CHANGELOG) |

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
R=~/.claude/skills/skills-curator/scripts/registry.py

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
$R = "$env:USERPROFILE\.claude\skills\skills-curator\scripts\registry.py"
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

## Security scan patterns checked by `--check`

<!-- scanner:ignore-block-start -->
Remote code execution (curl/wget pipe), destructive commands (`rm -rf /`), hardcoded secrets (OpenAI key, Anthropic key, GitHub PAT, passwords), `eval()` / `exec()`, suspicious HTTP endpoints, dynamic imports, base64 obfuscation, credential store access. See `SECURITY_RISK_PATTERNS` in `scripts/registry.py` for the full list.
<!-- scanner:ignore-block-end -->
