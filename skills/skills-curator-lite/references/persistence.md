# Persistence, registry, live enrichment, migration

## Where state lives

```
~/.claude/skills/skills-curator-lite/registry.json
~/.claude/skills/skills-curator-lite/auto_state.json
~/.claude/skills/skills-curator-lite/catalog.json     (optional cache, refreshed via --refresh)
```

Initialize the first time:

```bash
mkdir -p ~/.claude/skills/skills-curator-lite
[ -f ~/.claude/skills/skills-curator-lite/registry.json ] || \
  echo '{"version":"3.0","last_updated":"","skills":[]}' > ~/.claude/skills/skills-curator-lite/registry.json
[ -f ~/.claude/skills/skills-curator-lite/auto_state.json ] || \
  echo '{}' > ~/.claude/skills/skills-curator-lite/auto_state.json
```

Schema is identical to the full version (switch any time): `version`, `last_updated`, `skills[]` where each skill has `id`, `name`, `source`, `install`, `type`, `tags`, `evaluations[]`, `security_scan`, `installed_version`, `pairs_with`.
Evaluation entry: `date`, `project`, `verdict` (adopt|partial|skip), `summary`, `pros[]`, `cons[]`, `conflicts[]`.

## Persisting an evaluation

Read registry.json, append to the skill's `evaluations`, Write the whole file back. If `jq` exists:

```bash
REG=~/.claude/skills/skills-curator-lite/registry.json
jq --arg id "<skill-id>" \
   --argjson ev '{"date":"2026-05-08","project":"my-app","verdict":"adopt","summary":"...","pros":["a"],"cons":["b"],"conflicts":[]}' \
   '(.skills[] | select(.id == $id) | .evaluations) += [$ev]' \
   "$REG" > "$REG.tmp" && mv "$REG.tmp" "$REG"
```

## auto_state.json (proactive activation)

```json
{
  "<project_path>": {
    "fingerprint": "<concatenated-bytes-and-prefix>",
    "scanned_at": "<YYYY-MM-DD>",
    "top_picks": [{"id": "...", "name": "...", "score": 65}]
  }
}
```

## Live catalog enrichment (GitHub topics)

On `--refresh` or "latest skills". Honors `SKILLS_NO_TELEMETRY=1` (skip silently).

```bash
[ "$SKILLS_NO_TELEMETRY" = "1" ] && exit 0
CACHE=~/.claude/skills/skills-curator-lite/catalog.json
mkdir -p ~/.claude/skills/skills-curator-lite
for topic in claude-skill claude-code-skill agent-skill; do
  curl -sL \
    -H "Accept: application/vnd.github+json" \
    -H "User-Agent: skills-curator-lite" \
    ${SKILLS_CURATOR_GITHUB_TOKEN:+-H "Authorization: token $SKILLS_CURATOR_GITHUB_TOKEN"} \
    "https://api.github.com/search/repositories?q=topic:$topic&sort=stars&per_page=20" \
    > /tmp/topic-$topic.json
done
```

Then: (1) Read each `/tmp/topic-*.json`; (2) extract `name`, `full_name`, `description`, `topics`, `stargazers_count`; (3) trust by author: `anthropics`, `vercel-labs`, `microsoft`, `google` = official; `ComposioHQ`, `supermemoryai`, `remotion-dev`, `firecrawl` = high; `obra` = medium; else unknown; (4) build entries with empty pros/cons; (5) merge with catalog.yaml, curated wins on id collision; (6) write `catalog.json` with `fetched_at`. Cache TTL 24h (prefer cached if mtime recent).

Note: skills.sh HTML scraping stays removed (brittle, dishonest for a judgment tool). The skills.sh JSON search endpoint (see SKILL.md) is used instead.

## MIGRATE (copy skills to other agents)

1. Default source `~/.claude/skills/`.
2. Confirm targets: validate named platforms against platforms.md; for "all detected"/unspecified, run detection and exclude `claude-code`.
3. Per target, create the dir and copy skill folders, never clobbering.

```bash
SRC="$HOME/.claude/skills"
DST="$HOME/.cursor/skills"          # from platforms.md
mkdir -p "$DST"
for skill in "$SRC"/*/SKILL.md; do
  name=$(basename "$(dirname "$skill")")
  if [ ! -d "$DST/$name" ]; then
    cp -r "$SRC/$name" "$DST/$name" && echo "Copied $name -> $DST"
  else
    echo "Skip $name (already exists in $DST)"
  fi
done
```

Loop for multi-target. Default to `claude-code` only if no target given and no agents detected. Primary first-class: `claude-code`, `github-copilot`; the other 53 use the same flow.

## PLATFORMS detection

```bash
for path in "$HOME/.claude" "$HOME/.copilot" "$HOME/.codex" "$HOME/.cursor" "$HOME/.gemini" "$HOME/.cline" "$HOME/.codeium/windsurf"; do
  [ -d "$path" ] && echo "DETECTED: $path"
done
```
(Detection paths for all 55: platforms.md.) Render:

```
════════════════════════════════════════════════════════════════
  Skills Curator Platforms  ·  Detected <n> of 55
════════════════════════════════════════════════════════════════
  Detected on this machine: <comma-separated names>

  PLATFORM                STATUS      DIR
  Claude Code             ✓ detected  ~/.claude/skills
  ...
  (52 more not shown — ask for full list)
```
If asked for the full list, render every row of platforms.md.
