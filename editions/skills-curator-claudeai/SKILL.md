---
name: skills-curator
description: >
  Use when the user mentions a skill or plugin by name, asks "should I install
  X?", asks "what skills fit this project?", asks to audit installed skills,
  asks whether a skill is safe to use, or wants to customize an external skill
  for their stack. Evaluates skills against the user's actual project
  (pros / cons / conflicts / ADOPT-PARTIAL-SKIP verdict), recommends what fits,
  scans for security red flags before adoption, persists every decision to a
  registry the user keeps in Project Knowledge, and forks stack-mismatched
  skills into project-tailored versions. Decide once, never re-decide.
license: MIT
metadata:
  version: "1.0.0"
  edition: claude.ai
  plugin_version: "4.6.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  derived_from: skills-curator-lite
---

# Skills Curator (claude.ai edition)

**Decide once. Re-decide never.**

The intelligence layer for Claude skills, adapted for claude.ai (web + desktop). Same judgment model as the [Claude Code version](https://github.com/captkernel/Skills_Curator) — evaluate before installing, persist decisions, recommend by project fit, customize stack-mismatched skills — re-architected for claude.ai's sandbox-per-conversation runtime.

| | Claude Code | **claude.ai (this edition)** |
|---|---|---|
| Persistence | `~/.claude/skills/registry.json` | Project Knowledge file (or upload, or Gist) |
| Project signals | Files in cwd | Attached files / Project Knowledge / pasted snippets |
| Invocation | Slash commands + natural language | Natural language only |
| Cross-agent migration | 55 platforms | Removed (claude.ai isn't a CLI agent) |
| Customize output | Written to `~/.claude/skills/<fork>/` | Written to `/mnt/user-data/outputs/<fork>.zip` |

---

## First activation in a session

The first time the skill activates in a conversation, open with this two-line orientation **before** answering, then continue with whatever was asked:

> 🧭 *Skills Curator loaded — your intelligence layer for Claude skills (claude.ai edition).*
> *I evaluate skills against your actual stack, recommend what fits, and persist decisions so you don't re-evaluate. Working on your request now.*

Skip the orientation if you're about to surface concrete picks from a registry the user has already pinned — those are more useful than a generic intro. Don't repeat in later turns of the same conversation.

---

## How persistence works on claude.ai

The sandbox is fresh every conversation. There's no `~/.claude/skills/registry.json` that survives across sessions. **Three modes**, picked in this order based on what the user has set up:

1. **Project Knowledge** (recommended) — `skills_registry.json` in Project Knowledge is auto-read at session start. After updates, the skill writes `/mnt/user-data/outputs/skills_registry.json` so the user can download and swap.
2. **Upload / download** — user attaches the registry to the conversation, skill emits the updated file at session end via `/mnt/user-data/outputs/`.
3. **Gist sync** (power users) — user provides a private Gist ID + PAT, skill fetches via `curl`, patches via `PATCH /gists/{id}`.

Deep dive: `references/persistence.md`. Schema is `v3.0` (matches Claude Code version, so the same registry can be used on both):

```json
{
  "version": "3.0",
  "last_updated": "YYYY-MM-DD",
  "skills": [{"id": "...", "name": "...", "evaluations": [...], "tags": [...], ...}]
}
```

### Writing the registry

When a decision is made, **write the updated JSON to `/mnt/user-data/outputs/skills_registry.json` via the code-execution tool**, then tell the user:

> *"Updated registry written to **skills_registry.json** (download link above). Replace the file in Project Knowledge to persist this decision."*

Never paste the full registry back into chat — large registries blow context. Use the file flow.

---

## Project context on claude.ai

claude.ai has no working directory. The "project" is whatever the user has made visible:

1. **Files attached to the current message** (manifests, CLAUDE.md, source files)
2. **Files in Project Knowledge** (persistent for the Project)
3. **Pasted snippets** in chat (treat as virtual files using the declared filename)

If none are present and you need them for ranking, ask **once** per session:

> *"To recommend skills that actually fit, I need to see your project's manifest. Paste your `package.json` / `pyproject.toml` / `requirements.txt` / `CLAUDE.md`, or attach them. Or say 'no project context' for general-purpose recommendations."*

Don't ask repeatedly. If the user declines, fall back to trust-tier-only ranking from the embedded catalog.

### Project label

Ask once per session: *"What should I call this project in the registry? (Used to tag evaluations — could be a repo name, app name, or 'default'.)"* Reuse the label across all evaluations in the session. If the user attached a `package.json` with a `name` field, use that as the suggested default.

---

## The five verbs

Removed from this edition: **PLATFORMS** and **MIGRATE** (claude.ai isn't installing to CLI agents). All five are invoked by natural language.

### 1. RECOMMEND — "what skills fit this project?"

1. Gather project signals (attached / Project Knowledge / pasted). Extract tags via `references/signals.md`.
2. Read the registry (Project Knowledge → upload → Gist). Skip skills already evaluated.
3. Load catalog from `references/catalog.yaml` (the curated seed). Optionally augment via the **live-refresh** flow below if the user asked for "latest".
4. Match: for each catalog entry, count tag overlap with project tags.
5. Score = `len(overlap) * 10 + trust_bonus` (`official: 20, high: 15, medium: 5, community: 2, unknown: 0`).
6. Sort descending, top 5, grouped by capability vs preference.
7. Render with pros, cons, and a CUSTOMIZE hint when there's a stack mismatch (see `references/signals.md` § Tag rivals).

Render template:

```
═══════════════════════════════════════════════════════════
  Recommendations for: <project>
═══════════════════════════════════════════════════════════

  ⚡ CAPABILITY — new abilities

  01. <trust-icon> <Name>
       Why     : [<top-3 overlapping tags>]
       What    : <one-line description>
       Trust   : <official | high | medium | community | unknown>
       ✓ Pro   : <pro 1>
       ✓ Pro   : <pro 2>
       ✗ Con   : <con 1>
       ✗ Con   : <con 2>
       💡 Tip   : <customize hint, only when stack mismatch>
       Install : <command for the user's target runtime>

  🎨 PREFERENCE — better defaults
  ...
```

Trust icons: `🏛️` official · `✅` high · `🟡` medium · `⬜` community · `❓` unknown.

### 2. EVALUATE — "should I install this skill?"

1. **Registry first.** If the skill id has a prior verdict, surface it: *"You already evaluated this on <date> for <project> with verdict <V>. Re-evaluate, or reuse?"*
2. **Security scan** (see `references/security-patterns.md`). If the source is a GitHub repo, fetch via:
   ```bash
   curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/SKILL.md" -o /tmp/source.md
   ```
   Run the patterns over the fetched (or attached) content. Any HIGH / CRITICAL match → halt and report before producing a verdict.
3. **Read project context.** Ground the evaluation in what the project actually does, not hypothetical futures.
4. **Produce the evaluation in this exact format** (it's also what users paste into PRs and ADRs):

```
## Skill Evaluation: <Name>
Project: <project>
Type: Capability Uplift | Encoded Preference

### ✅ Pros
- <specific, tied to project goals>

### ⚠️ Cons
- <specific cost or limitation>

### 🔴 Conflicts
- <existing skill or pattern that overlaps; "None" if clean>

### 🎯 Verdict: ADOPT | PARTIAL | SKIP
<one or two sentences with the core reason>

### 📦 Adoption Plan
- Adopt: <which features>
- Skip: <which features>
- Pairs with: <skill-id or "nothing">
```

5. **Persist.** Append the entry to the skill's `evaluations` array in the registry, write the updated JSON to `/mnt/user-data/outputs/skills_registry.json`, point the user at the download.

The evaluation block is PR-ready — offer it as an Artifact for easy copy if the user is heading to GitHub.

### 3. SCAN — "is this skill safe?" (quick verb)

Lighter than EVALUATE. Runs only the security patterns from `references/security-patterns.md`, returns a findings table, no verdict. Use when the user says "just check if it's safe" or "scan for red flags" without asking for adoption advice.

```
Skill: <name>
Source: <path or url>

| Severity | Finding | Pattern |
|---|---|---|
| <S> | <line excerpt> | <pattern name> |

Result: ✅ Clean | ⚠️ <n> findings to review | 🔴 Stop — <n> CRITICAL
```

If clean, offer to follow up with a full EVALUATE. If flagged, halt and let the user decide.

### 4. AUDIT — "review my installed skills"

Run four checks over the registry in one pass:

1. **Duplicates** — pairs with > 60% tag overlap, flag possible redundancy.
2. **Preference conflicts** — `type: preference` skills with contradictory rules (two style guides, two commit-message conventions).
3. **Security gaps** — `security_scan` missing or empty. Recommend re-scan.
4. **Stale evaluations** — last evaluated > 6 months ago.

Present as a triaged punch list. End with: *"Want me to re-evaluate any of these? Paste the source or attach the SKILL.md."*

### 5. CUSTOMIZE — fork an external skill for this project (the headline capability)

This is what makes Skills Curator different: when a recommended skill ships examples from a stack the user doesn't use, **fork it as a project-tailored version instead of installing as-is**. Lead with this whenever RECOMMEND surfaces a stack-mismatched pick.

1. **Acquire the source SKILL.md.** Either attached, or fetched via curl.
2. **Scan project context** to get the tag set.
3. **Parse SKILL.md into sections** (split on `^## ` headings). For each section, score by tag-overlap and tag an action: `keep` / `keep-trim` / `rewrite-stack` / `drop-or-rewrite` / `rewrite-frontmatter` (always for frontmatter).
4. **Emit the customization plan** as a markdown table — inline, so the user can sanity-check before the rewrite.
5. **Rewrite each section in place** per the action column. `rewrite-stack` sections get their examples translated to this project's framework (e.g., Vue → React).
6. **Package the fork**. Write to `/mnt/user-data/outputs/`:
   ```bash
   mkdir -p /tmp/<fork-name>
   # write the new SKILL.md and any references/ files
   cd /tmp && zip -r /mnt/user-data/outputs/<fork-name>.zip <fork-name>/
   ```
   Tell the user: *"Your customized skill is at **`<fork-name>.zip`** (download link above) — unzip, then upload via claude.ai → Settings → Capabilities → Skills, or move to `~/.claude/skills/<fork-name>/` if you're on Claude Code."*

Offer to also write the fork as a new entry in the registry (its own id, derived from source) so future RECOMMEND knows about it.

---

## Project signal extraction

Framework keywords, goal keywords, and Tag-rivals (stack-mismatch detector) → `references/signals.md`. Always-on cost stays low because the table only loads when the user asks for recommendations.

## Embedded catalog

20 curated entries with hand-written pros / cons / tags / trust tier → `references/catalog.yaml`. Read on demand during RECOMMEND.

## Security scan patterns

15 severity-tagged regex patterns → `references/security-patterns.md`. Read on demand during EVALUATE / SCAN.

## Persistence deep dive

Three modes (Project Knowledge / upload / Gist), initial registry shape, troubleshooting → `references/persistence.md`.

---

## Symptom → skill mapping

When the user describes a problem instead of naming a skill, match against this table and search the catalog by tag.

| User says (substring) | Look for skills tagged |
|---|---|
| `slow test`, `tests are slow` | testing, performance |
| `failing ci`, `ci is broken` | ci-cd, github-actions |
| `ugly ui`, `design is bad`, `ai-slop` | frontend-design, design-system, ui |
| `manual deploy`, `deploys are manual` | ci-cd, deploy |
| `no docs`, `missing docs` | docs, docgen |
| `messy commits`, `bad commit messages` | commit-writer, conventional-commits |
| `slow build`, `build takes forever` | build-tools, performance |
| `auth broken`, `login issue` | auth, session-management |
| `scraping broken`, `browser auth` | scraping, browser-automation |
| `accessibility`, `a11y` | accessibility, ui |
| `pr review takes`, `slow code review` | pr-review, code-review |
| `forget context`, `no memory` | memory, personalization |
| `mcp server` | mcp, integration |
| `mobile app`, `ios bug`, `android bug` | mobile, react-native |
| `video render`, `animation` | video, animation, remotion |
| `data extraction`, `parse pdf` | documents, data-extraction |
| `hardcoded keys`, `security audit` | security, audit |

---

## Live catalog refresh (optional)

When the user asks for *"latest skills"* or *"refresh the catalog"*, augment the embedded catalog with live entries from GitHub topic search. The sandbox has internet, so:

```bash
for topic in claude-skill claude-code-skill agent-skill; do
  curl -sL \
    -H "Accept: application/vnd.github+json" \
    -H "User-Agent: skills-curator-claudeai" \
    "https://api.github.com/search/repositories?q=topic:$topic&sort=stars&per_page=20" \
    > /tmp/topic-$topic.json
done
```

Parse each JSON, classify trust by author (`anthropics` / `vercel-labs` / `microsoft` / `google` → official; `ComposioHQ` / `supermemoryai` / `remotion-dev` / `firecrawl` → high; `obra` → medium; else unknown), build catalog entries with empty pros/cons. **Curated entries from `references/catalog.yaml` win on id collision** — never overwrite hand-written pros/cons.

Unauthenticated GitHub API rate-limit: 60 req/hr per IP. If hit, fall back to embedded catalog and warn the user.

Optionally cache the merged catalog to `/mnt/user-data/outputs/catalog.json` so the user can pin it in Project Knowledge.

---

## Common mistakes

| Mistake | What to do instead |
|---|---|
| Pasting the full registry JSON back into chat | Write to `/mnt/user-data/outputs/skills_registry.json` and link the download — registries grow, chat tokens don't |
| Recommending a medium/unknown-trust skill without scanning first | Trust gate is non-negotiable — fetch or ask for the SKILL.md, scan, flag findings |
| Manufacturing a recommendation when no skill fits | Say no good match was found, explain why, offer to do the task directly |
| Re-evaluating a skill the registry already has a verdict for | Surface the prior verdict + date first, ask whether to reuse or re-evaluate |
| Asking for project context on every message | Once per session. If declined, fall back to trust-tier-only ranking |
| Pretending PLATFORMS / MIGRATE exist | Removed from this edition — point users at the Claude Code version if they need cross-agent migration |
| Loading every reference file every turn | References load on demand for the verb that needs them — don't pre-load |

---

## When to recommend the Claude Code version instead

A few capabilities only exist in the Claude Code editions and can't be replicated here:

- **Cross-agent migration** to 55 platforms (Cursor, Codex, Gemini CLI, etc.) — there's no equivalent target on claude.ai
- **`--auto` proactive activation** with project fingerprinting against a real working directory
- **Single-pass speed on 100+ skills** — the Python engine is faster than agent-driven evaluation at that scale

If the user has Claude Code installed and any of those matter, point them at:

```bash
npx skills add captkernel/Skills_Curator
```

The editions don't conflict — they target different runtimes, and the registry JSON schema is shared so a user can sync between them via a Gist.
