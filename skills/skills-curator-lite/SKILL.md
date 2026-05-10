---
name: skills-curator-lite
description: >
  The intelligence layer for Claude skills — without Python. Maintains a
  trust-rated catalog (curated entries + live GitHub topic search via curl),
  identifies what fits your project (stack, deps, CLAUDE.md), recommends with
  pros/cons and per-project customization advice, persists every decision, and
  migrates across 55 supported agent platforms. Same model as the full version,
  no engine — the agent does the work via Bash, Read, Glob, Grep, Write.
  Use when the user mentions a skill, asks "should I install X", asks to
  evaluate / recommend / audit / check a skill, asks "what skills fit this
  project", asks for a list of supported platforms, or wants to migrate skills
  to another agent. Choose this over the full version when you don't have
  Python, want zero dependencies, or prefer transparent agent reasoning.
metadata:
  version: "2.0.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  license: MIT
  derived_from: skills-curator
when_to_use:
  - User mentions a new skill, plugin, or tool by name
  - User asks "should I install X" or "what skills fit this project"
  - User asks to list, search, compare, or evaluate skills
  - User asks for skill recommendations based on the current project
  - User wants to check if a skill is safe to install
  - User asks about duplicate or conflicting skills
  - User wants to migrate skills to another agent
  - User asks for a list of supported platforms
  - User does NOT have Python installed (this is the no-Python version)
  - User wants to share an evaluation of a skill (export to markdown)
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - Grep
---

# Skills Curator Lite

**Decide once. Re-decide never. — without Python.**

The intelligence layer for Claude skills, implemented as pure agent instructions. Same judgment-first model as the full [Skills Curator](https://github.com/captkernel/Skills_Curator) — evaluate before installing, persist your decisions, recommend by project fit, migrate across agent platforms — but the agent does the work directly using Bash, Read, Glob, Grep, and Write.

**Choose this when:** Python isn't available, you want zero dependencies, or you prefer agent reasoning you can read line-by-line.

**Choose the full version when:** you have 100+ skills (single Python pass beats N agent calls), you want regression-tested code, or you need cross-device Gist sync.

---

## First activation in a session

The first time this skill activates in a session, open with this two-line orientation **before** answering, then continue with whatever was asked:

> 🧭 *Skills Curator Lite loaded — your intelligence layer for Claude skills (Python-free).*
> *I maintain a trust-rated catalog (curated entries + live GitHub topic search), identify what fits your project (stack, deps, CLAUDE.md), and on request return ranked lists with pros, cons, and per-project customization advice — persisting every decision so you don't re-evaluate. Working on your request now.*

Skip the orientation entirely if proactive activation (next section) is about to surface concrete picks — those are more useful than a generic intro. Don't repeat orientation in later messages of the same session.

---

## Proactive activation (the intelligence layer)

**Lite's USP, like the full version, is judgment that activates without being asked.** Don't wait for the user to say "evaluate this skill" — surface relevant skills the moment a project context implies one would help.

### Run this at the start of any session in a real project

If the working directory contains `CLAUDE.md`, `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or `Cargo.toml`, do **once, silently** at the start of the session:

1. **Compute a project fingerprint** from these files (whichever exist): byte counts via `wc -c` and the first 200 chars of each. Combine into a deterministic string.
2. **Read** `~/.claude/skills/skills-curator-lite/auto_state.json` (initialize as `{}` if missing).
3. **Compare** against the stored fingerprint for this project path. If matched → say nothing, exit silently.
4. **If different (or first run):** run RECOMMEND silently, take top 3 picks, store them + new fingerprint to `auto_state.json`, and weave them into your first response *as a quiet observation*, not a sales pitch:

> "While we work on this — I noticed you're using Next.js + Tailwind. There's a `frontend-design` skill (🏛️ official) that adds aesthetic guidelines that match your stack. Want me to evaluate it?"

State file shape:
```json
{
  "<project_path>": {
    "fingerprint": "<concatenated-bytes-and-prefix>",
    "scanned_at": "<YYYY-MM-DD>",
    "top_picks": [{"id": "...", "name": "...", "score": 65}]
  }
}
```

### Re-run when the project shifts

After the user adds/removes a dependency, edits CLAUDE.md, or installs a new framework, re-run the fingerprint check. The byte-count comparison detects the drift.

### When the user describes a problem instead of naming a skill

If the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, or any other complaint that hints at a missing capability, match against the **Symptom → skill mapping** table below and search the embedded catalog by tag.

### Don't over-trigger

- Run the fingerprint check **at most once per session** unless the project actually changes.
- Apply symptom mapping only when the user expresses a clear pain point. Don't fire it on every passing reference.
- If the fingerprint check returns nothing strong (no tag overlap, low trust), **say nothing**. Silence is a valid answer when the stack is well-covered.

---

## Where the registry lives

```
~/.claude/skills/skills-curator-lite/registry.json
~/.claude/skills/skills-curator-lite/auto_state.json
~/.claude/skills/skills-curator-lite/catalog.json     (optional, refreshed via --refresh)
```

Initialize the first time:

```bash
mkdir -p ~/.claude/skills/skills-curator-lite
[ -f ~/.claude/skills/skills-curator-lite/registry.json ] || \
  echo '{"version":"3.0","last_updated":"","skills":[]}' > ~/.claude/skills/skills-curator-lite/registry.json
[ -f ~/.claude/skills/skills-curator-lite/auto_state.json ] || \
  echo '{}' > ~/.claude/skills/skills-curator-lite/auto_state.json
```

Schema is identical to the full version (so you can switch later): `version`, `last_updated`, `skills[]` where each skill has `id`, `name`, `source`, `install`, `type`, `tags`, `evaluations[]`, `security_scan`, `installed_version`, `pairs_with`.

---

## The five verbs

### 1. RECOMMEND — what skills fit this project?

Steps the agent runs in order:

1. **Scan the project for signals.** Use Glob to detect languages and Read on key config files:
   ```bash
   ls package.json requirements.txt pyproject.toml Pipfile go.mod Cargo.toml CLAUDE.md README.md 2>/dev/null
   ```
   For each file present, Read it. Extract framework keywords using the **Framework Signals** table.

2. **Read CLAUDE.md and README.md** if present. Extract goal keywords using the **Goal Signals** table.

3. **Build a tag set** = (languages detected) ∪ (framework matches) ∪ (goal matches).

4. **Load the catalog.** Prefer `~/.claude/skills/skills-curator-lite/catalog.json` if fresh (mtime within 24h); otherwise use the **Embedded Catalog** below. The user can run `--refresh` to pull live entries from GitHub.

5. **Match.** For each catalog skill, count tag overlap with project tags. Skip skills already in the registry.

6. **Score** = `len(overlap) * 10 + trust_bonus` where trust_bonus is `official: 20, high: 15, medium: 5, community: 2, unknown: 0`.

7. **Sort descending. Show top 5.** Group by capability vs preference.

8. **Render with pros, cons, and customization hints.** For each pick, surface up to 2 pros and 2 cons from the catalog entry. If the skill's tags imply a stack mismatch with the project (see **Tag rivals** table), append a one-line `--customize` hint.

Render template:

```
═══════════════════════════════════════════════════════════
  Recommendations for: <project>
═══════════════════════════════════════════════════════════

  ⚡ CAPABILITY — new abilities

  01. <trust-icon> <Name>
       Why     : [<top-3-overlapping-tags>]
       What    : <one-line description>
       Trust   : <official|high|medium|community|unknown>
       ✓ Pro   : <pro 1>
       ✓ Pro   : <pro 2>
       ✗ Con   : <con 1>
       ✗ Con   : <con 2>
       💡 Tip   : <customize hint, only if stack mismatch>
       Install : <install command>

  🎨 PREFERENCE — better defaults
  ...
```

Trust icons: `🏛️` official · `✅` high · `🟡` medium · `⬜` community · `❓` unknown.

### 2. EVALUATE — should I install this specific skill?

Steps in order:

1. **Check the registry first.** Read `registry.json` and look for the skill id. If present, surface the prior verdict + summary instead of re-evaluating.

2. **If the skill is a local folder, run a security scan** using the **Security Scan Patterns** table below. Any HIGH or CRITICAL match → stop and report.

3. **Read CLAUDE.md.** Use this to ground the evaluation against what the project actually does.

4. **Produce the evaluation in this exact format** (the user can paste it into a PR):

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

5. **Persist the decision.** Update the registry by writing a new evaluations entry. Use Read → modify → Write:
   ```bash
   # Read current registry
   cat ~/.claude/skills/skills-curator-lite/registry.json
   ```
   Modify the appropriate skill's `evaluations` array (append a new entry with `date`, `project`, `verdict`, `summary`, `pros[]`, `cons[]`, `conflicts[]`), then Write the whole file back.

   If `jq` is available on the system, the agent may use it for in-place updates:
   ```bash
   REG=~/.claude/skills/skills-curator-lite/registry.json
   jq --arg id "<skill-id>" \
      --argjson ev '{"date":"2026-05-08","project":"my-app","verdict":"adopt","summary":"...","pros":["a"],"cons":["b"],"conflicts":[]}' \
      '(.skills[] | select(.id == $id) | .evaluations) += [$ev]' \
      "$REG" > "$REG.tmp" && mv "$REG.tmp" "$REG"
   ```

### 3. AUDIT — review my whole stack

Run all four checks in one pass:

1. **Duplicates.** Group registered skills by tag overlap > 60%. Flag pairs that look like they do the same thing.
2. **Preference conflicts.** For skills with `type: preference`, look for contradictory rules (e.g., two style guides). Flag pairs.
3. **Security gaps.** List skills where `security_scan` is missing or empty. Recommend running EVALUATE on each.
4. **Stale evaluations.** List skills last evaluated > 6 months ago.

Present as a triaged punch list — most-critical first.

### 4. PLATFORMS — what agent platforms can I install to?

When the user asks *"where can I install this?"*, *"what agents do I have?"*, or *"list supported platforms"*, run platform detection:

```bash
# For each platform in the Platforms catalog (below), test if its detection
# directory exists. Mark detected vs not.
for path in \
  "$HOME/.claude" \
  "$HOME/.copilot" \
  "$HOME/.codex" \
  "$HOME/.cursor" \
  "$HOME/.gemini" \
  "$HOME/.cline" \
  "$HOME/.codeium/windsurf" \
  ; do
  [ -d "$path" ] && echo "DETECTED: $path"
done
```

(See the full **Platforms catalog** for all 55 paths.)

Render:

```
════════════════════════════════════════════════════════════════
  Skills Curator Platforms  ·  Detected <n> of 55
════════════════════════════════════════════════════════════════

  Detected on this machine: <comma-separated names>

  PLATFORM                STATUS      DIR
  ----------------------  ----------  ---
  Claude Code             ✓ detected  ~/.claude/skills
  GitHub Copilot          ✓ detected  ~/.copilot/skills
  ...
  (52 more not shown — ask for full list)
```

If the user asks for the full list, render every row from the Platforms catalog.

### 5. MIGRATE — copy skills to other agents

When the user asks *"copy my skills to Cursor"* or *"migrate to Codex and Roo"*:

1. **Default source:** `~/.claude/skills/`
2. **Confirm the target list.** If the user named specific platforms, validate them against the Platforms catalog. If they said *"all detected"* or didn't specify, run platform detection and use those (excluding `claude-code`).
3. **For each target:** create the destination directory, copy each skill folder. Skip existing destinations to avoid clobbering.

```bash
# Single target
SRC="$HOME/.claude/skills"
DST="$HOME/.cursor/skills"          # from Platforms catalog
mkdir -p "$DST"
for skill in "$SRC"/*/SKILL.md; do
  name=$(basename "$(dirname "$skill")")
  if [ ! -d "$DST/$name" ]; then
    cp -r "$SRC/$name" "$DST/$name" && echo "Copied $name → $DST"
  else
    echo "Skip $name (already exists in $DST)"
  fi
done
```

For multi-target, loop the above over the user's confirmed target list. Default to `claude-code` only if the user gave no target and no detected agents are available.

**Primary first-class:** `claude-code`, `github-copilot`. Other 53 platforms reachable via the same flow.

### Bonus: CUSTOMIZE — fork an external skill for this project

When the user wants to install a skill but it ships examples from a stack they don't use:

1. **Read the source SKILL.md.** Either local path, or fetch from GitHub via curl:
   ```bash
   curl -sL "https://raw.githubusercontent.com/<owner>/<repo>/main/<path>/SKILL.md" -o /tmp/source-skill.md
   ```
2. **Scan this project** (same signals as RECOMMEND) to get its tag set.
3. **Parse the SKILL.md into sections** (split on `^## ` headings). For each section:
   - Score by tag-overlap with project tags.
   - Decide an action: `keep` (high overlap), `keep-trim` (some overlap, drop the rest), `rewrite-stack` (overlap with rival framework — needs rewrite), `drop-or-rewrite` (no overlap), `rewrite-frontmatter` (always for the frontmatter block).

4. **Write the fork** to `~/.claude/skills/<name>-for-<project>/SKILL.md`. The fork starts with a customization plan table:

```markdown
---
name: <skill-id>-for-<project>
description: |
  Project-customized fork of '<skill-id>' for '<project>'.
  Tailored to: <top 5 project tags>
metadata:
  derived_from: <skill-id>
  customized_for: <project>
  customized_at: <YYYY-MM-DD>
---

# <skill-id>-for-<project>

> **Customization in progress.** This fork was generated by Skills Curator Lite.
> The agent should now rewrite each section per the plan below.

## Customization plan

| # | Section | Action | Why |
|---|---|---|---|
| 1 | (frontmatter) | rewrite-frontmatter | Update id, derive from |
| 2 | <heading>     | <action>            | <why>                  |
...
```

5. **Then rewrite each section** per the action column. `rewrite-stack` sections should have their examples rewritten to match this project's framework (e.g., Vue → React).

---

## Project signal extraction

When the agent scans a project, it uses these tables to convert raw files into tags.

### Framework Signals (keywords found in package.json / requirements.txt / pyproject.toml / CLAUDE.md / README.md)

| Keyword in file | Tags emitted |
|---|---|
| `react`, `next`, `nextjs` | `react, frontend, nextjs` |
| `vue`, `nuxt` | `vue, frontend` |
| `svelte`, `sveltekit` | `svelte, frontend` |
| `tailwind`, `tailwindcss` | `tailwind, css, design-system` |
| `playwright` | `playwright, browser-automation, testing` |
| `puppeteer` | `puppeteer, browser-automation` |
| `pytest`, `jest`, `vitest`, `cypress` | `testing` |
| `fastapi`, `flask`, `django`, `express` | `backend, api` |
| `prisma`, `drizzle`, `sqlalchemy` | `database, orm` |
| `terraform`, `pulumi`, `kubernetes` | `infra, devops` |
| `docker`, `dockerfile` | `devops, containers` |
| `langchain`, `openai`, `anthropic` | `ai, llm` |
| `pandas`, `numpy`, `torch`, `pytorch` | `data-science, ml` |
| `stripe` | `stripe, payments` |
| `postgres`, `mongodb`, `redis`, `supabase` | `database` |
| `expo` | `expo, react-native, mobile` |
| `remotion` | `remotion, video, animation` |

### Goal Signals (keywords found in CLAUDE.md / README.md, case-insensitive)

| Phrase pattern | Tags emitted |
|---|---|
| `scrape`, `crawl`, `extract data` | `scraping, data-extraction` |
| `auth`, `login`, `session` | `auth, session-management` |
| `dashboard`, `admin panel`, `cms` | `frontend, dashboard` |
| `migrate`, `migration` | `database, migration` |
| `agent`, `LLM`, `AI` | `ai, agents` |
| `test`, `testing`, `coverage` | `testing` |
| `deploy`, `CI/CD`, `release` | `ci-cd, deploy` |
| `documentation`, `docs` | `docs` |
| `accessibility`, `a11y` | `accessibility, ui` |
| `commit`, `pull request` | `git, code-review` |
| `video`, `animation` | `video, animation` |
| `mobile`, `iOS`, `android` | `mobile` |
| `memory`, `personalization`, `recall` | `memory, personalization` |

---

## Embedded catalog

The full version's `KNOWN_SKILLS` list, with pros/cons, mirrored as YAML so the agent can parse without code. The agent should treat this as the seed catalog; live GitHub-discovered entries (via `--refresh`) merge on top.

```yaml
- id: find-skills
  name: Find Skills
  source: vercel-labs/skills
  install: npx skills add vercel-labs/skills --skill find-skills
  type: capability
  trust: official
  tags: [meta, discovery, skill-management]
  description: Discovers and recommends skills from skills.sh based on task context.
  pros:
    - Official Vercel maintenance
    - Wraps skills.sh discovery in one verb
  cons:
    - Popularity-driven; doesn't filter by project fit
    - Overlaps with Skills Curator's --recommend

- id: frontend-design
  name: Frontend Design
  source: anthropics/skills
  install: npx skills add anthropics/skills --skill frontend-design
  type: preference
  trust: official
  tags: [frontend, design, react, css, html, ui, vue]
  description: Bold design philosophy before writing UI code. Prevents AI-slop aesthetics.
  pros:
    - Anthropic-curated
    - Prevents generic-looking UI defaults
    - Stack-agnostic principles
  cons:
    - Strong opinions may conflict with team style guide
    - Adds prompt overhead on non-UI tasks

- id: document-skills
  name: Document Skills
  source: anthropics/skills
  install: npx skills add anthropics/skills --skill document-skills
  type: capability
  trust: official
  tags: [documents, pdf, word, excel, powerpoint, docx, xlsx]
  description: Create and edit PDFs, Word docs, Excel sheets, and presentations.
  pros:
    - Covers all major office formats
    - First-party Anthropic skill
  cons:
    - Useless if your project never produces office files
    - Bundles 5 sub-skills you may not need

- id: skill-creator
  name: Skill Creator
  source: anthropics/skills
  install: npx skills add anthropics/skills --skill skill-creator
  type: capability
  trust: official
  tags: [meta, skill-development, authoring]
  description: Interactive skill authoring. Creates properly structured SKILL.md files.
  pros:
    - Produces canonically-formatted SKILL.md
    - Reduces friction for first-time authors
  cons:
    - Overlaps with Skills Curator's authoring flow
    - Adds context cost when not authoring

- id: vercel-react-best-practices
  name: React Best Practices
  source: vercel-labs/agent-skills
  install: npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices
  type: preference
  trust: high
  tags: [react, nextjs, frontend, performance, typescript]
  description: React/Next.js performance rules ordered by impact.
  pros:
    - Vercel-authored
    - Impact-ranked rules
    - Next.js-aware
  cons:
    - Next.js-biased examples (less useful for plain React)
    - Doesn't cover SSR alternatives

- id: web-design-guidelines
  name: Web Design Guidelines
  source: vercel-labs/agent-skills
  install: npx skills add vercel-labs/agent-skills --skill web-design-guidelines
  type: preference
  trust: high
  tags: [frontend, design, accessibility, ux, css, web]
  description: UI/UX rules — accessibility, typography, dark mode.
  pros:
    - Accessibility-first
    - Specific, validatable rules
  cons:
    - Heavy overlap with frontend-design
    - Vercel design language may not match your brand

- id: agent-browser
  name: Agent Browser
  source: vercel-labs/agent-browser
  install: npx skills add vercel-labs/agent-browser --skill agent-browser
  type: capability
  trust: high
  tags: [browser, automation, scraping, cdp, testing, forms]
  description: Browser automation via CDP. Element refs, 6 auth methods, screenshots, form fill.
  pros:
    - Six auth methods including session import
    - CDP gives access to JS-heavy pages
  cons:
    - Requires Chrome — adds CI dependency
    - Heavyweight for static-page scraping

- id: supermemory
  name: Supermemory
  source: supermemoryai/supermemory
  install: npx skills add supermemoryai/supermemory
  type: capability
  trust: high
  tags: [memory, personalization, context, recall, ai]
  description: Persistent memory across sessions. Tracks facts, resolves contradictions.
  pros:
    - Cross-session persistence
    - Conflict resolution built-in
  cons:
    - Sends context to a third-party service
    - Privacy review required for sensitive projects

- id: remotion-best-practices
  name: Remotion Best Practices
  source: remotion-dev/skills
  install: npx skills add remotion-dev/skills --skill remotion-best-practices
  type: preference
  trust: high
  tags: [remotion, video, animation, react, programmatic-video]
  description: Remotion knowledge — animations, timing, audio, captions, 3D.
  pros:
    - First-party Remotion knowledge
    - Activates automatically on Remotion files
  cons:
    - Useless if you don't use Remotion
    - Adds context cost on every session

- id: firecrawl-cli
  name: Firecrawl CLI
  source: firecrawl/cli
  install: npx skills add firecrawl/cli
  type: capability
  trust: high
  tags: [scraping, web, crawl, data-extraction, js-rendering]
  description: Web scraping with JS rendering. Handles SPAs, auth-gated pages.
  pros:
    - Handles JS-heavy SPAs out of the box
    - Structured-extraction primitives
  cons:
    - Requires Firecrawl API key
    - Paid tier for any meaningful usage

- id: openspace
  name: OpenSpace
  source: HKUDS/OpenSpace
  install: pip install git+https://github.com/HKUDS/OpenSpace.git
  type: capability
  trust: medium
  tags: [meta, self-evolving, mcp, token-efficiency]
  description: Self-evolving skills via MCP. Auto-fix, learn from execution.
  pros:
    - Token-efficient
    - Self-improving over usage
  cons:
    - Requires MCP setup
    - Research-grade — interface may shift

- id: writing-plans
  name: Writing Plans
  source: obra/superpowers
  install: npx skills add obra/superpowers --skill writing-plans
  type: preference
  trust: medium
  tags: [workflow, planning, discipline, process]
  description: Plan-before-code discipline. Reduces agents skipping steps.
  pros:
    - Reduces 'jumped to coding' failures
    - Forces explicit alignment before edits
  cons:
    - Adds friction for trivial one-liner tasks
    - Verbose for simple bug fixes

- id: verification-before-completion
  name: Verification Before Completion
  source: obra/superpowers
  install: npx skills add obra/superpowers --skill verification-before-completion
  type: preference
  trust: medium
  tags: [workflow, verification, quality, testing]
  description: Verify-before-done discipline.
  pros:
    - Catches false-success claims
    - Pairs naturally with TDD
  cons:
    - Requires verification commands to actually exist
    - Slows iteration when verification is expensive

- id: composio-connect
  name: Composio Connect
  source: ComposioHQ/composio-skills
  install: npx skills add ComposioHQ/composio-skills --skill connect
  type: capability
  trust: high
  tags: [integrations, api, gmail, slack, github, notion]
  description: Connect Claude to SaaS apps with managed OAuth.
  pros:
    - Managed OAuth removes credential plumbing
    - 100+ integrations
  cons:
    - Vendor lock-in to Composio
    - Routes data through their proxy

- id: security-auditor
  name: Security Auditor
  source: alirezarezvani/claude-skills
  install: npx skills add alirezarezvani/claude-skills --skill security-auditor
  type: capability
  trust: medium
  tags: [security, audit, vulnerability, owasp, code-review]
  description: Security audit skill. Scans for OWASP top 10, injection vectors, exposed secrets.
  pros:
    - OWASP-mapped
    - Catches obvious vulnerability patterns
  cons:
    - Pattern-based — misses logic-level issues
    - Community-maintained, smaller maintainer pool

- id: git-commit-writer
  name: Git Commit Writer
  source: glebis/claude-skills
  install: npx skills add glebis/claude-skills --skill git-commit-writer
  type: preference
  trust: medium
  tags: [git, commits, workflow, conventional-commits]
  description: Enforces conventional commit message format.
  pros:
    - Consistent commit history
    - Plays well with semantic-release
  cons:
    - Convention may not match team's existing style
    - Wasteful if you already have commitlint

- id: senior-backend
  name: Senior Backend
  source: davila7/claude-code-templates
  install: npx skills add davila7/claude-code-templates --skill senior-backend
  type: preference
  trust: medium
  tags: [backend, api, python, nodejs, go, typescript, database]
  description: Senior backend patterns — API scaffolding, DB optimisation, load testing.
  pros:
    - Multi-language coverage
    - Includes load-testing patterns
  cons:
    - Generic — may not match your stack's idioms
    - Adopting all 4 languages bloats prompt

- id: vercel-react-native-skills
  name: React Native Skills
  source: vercel-labs/agent-skills
  install: npx skills add vercel-labs/agent-skills --skill vercel-react-native-skills
  type: preference
  trust: high
  tags: [react-native, mobile, ios, android, expo]
  description: React Native best practices — Expo patterns, performance, platform handling.
  pros:
    - Expo-aware
    - Platform-handling guidance for iOS/Android divergence
  cons:
    - Expo-biased; less useful for bare React Native
    - No Fabric/Hermes guidance yet

- id: mcp-builder
  name: MCP Builder
  source: ComposioHQ/awesome-claude-skills
  install: npx skills add ComposioHQ/awesome-claude-skills --skill mcp-builder
  type: capability
  trust: medium
  tags: [mcp, integration, api, tools, typescript, python]
  description: Guides creation of high-quality MCP servers for integrating external APIs.
  pros:
    - Tightens MCP server quality
    - TypeScript + Python coverage
  cons:
    - Only useful when authoring an MCP server
    - Heavy overlap with Anthropic MCP docs

- id: skills-curator
  name: Skills Curator (full Python)
  source: captkernel/Skills_Curator
  install: npx skills add captkernel/Skills_Curator
  type: capability
  trust: high
  tags: [meta, skill-management, registry, evaluation]
  description: The Python version of this skill. Single-pass engine, faster on large catalogs, ships with 35 pytest cases.
  pros:
    - Single-pass speed on 100+ skills
    - Regression-tested
    - Cross-device Gist sync
  cons:
    - Requires Python 3.10+
    - Less transparent than Lite (engine code vs markdown)
```

To extend the catalog, add entries here in the same shape. Higher trust + tag count = better recommendations.

---

## Tag rivals (for customization hints)

When a recommended skill's tags imply a stack mismatch with the project, surface a `--customize` hint. Detection rule: if any of the skill's tags appear in column 1 AND any project tag appears in column 2 of the same row, flag a mismatch.

| Skill tags (left) | Project tags (right) — mismatch |
|---|---|
| vue, nuxt | react, nextjs |
| react, nextjs | vue, nuxt |
| angular | react, vue |
| django, flask | fastapi |
| fastapi | django, flask |

Hint format: *"Stack mismatch (`<skill-tag>` in skill vs `<project-tag>` in project) — fork it via CUSTOMIZE to rewrite examples."*

---

## Symptom → skill mapping

When the user describes a problem instead of naming a skill, match against this table and search the catalog by tag:

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

## Platforms catalog (55 supported)

Source: `vercel-labs/skills` `dist/cli.mjs` v1.5.5. Mirror this table when running the PLATFORMS verb. **Primary first-class:** `claude-code`, `github-copilot`. The detection path is what the agent tests with `[ -d ... ]` to determine if the platform is installed.

```yaml
# id: display name | install dir | detection path
- claude-code:     "Claude Code"      | "$HOME/.claude/skills"                  | "$HOME/.claude"
- github-copilot:  "GitHub Copilot"   | "$HOME/.copilot/skills"                 | "$HOME/.copilot"
- codex:           "Codex"            | "$HOME/.codex/skills"                   | "$HOME/.codex"
- cursor:          "Cursor"           | "$HOME/.cursor/skills"                  | "$HOME/.cursor"
- gemini-cli:      "Gemini CLI"       | "$HOME/.gemini/skills"                  | "$HOME/.gemini"
- cline:           "Cline"            | "$HOME/.cline/skills"                   | "$HOME/.cline"
- windsurf:        "Windsurf"         | "$HOME/.codeium/windsurf/skills"        | "$HOME/.codeium/windsurf"
- opencode:        "OpenCode"         | "${XDG_CONFIG_HOME:-$HOME/.config}/opencode/skills" | "${XDG_CONFIG_HOME:-$HOME/.config}/opencode"
- amp:             "Amp"              | "${XDG_CONFIG_HOME:-$HOME/.config}/agents/skills"   | "${XDG_CONFIG_HOME:-$HOME/.config}/amp"
- antigravity:     "Antigravity"      | "$HOME/.gemini/antigravity/skills"      | "$HOME/.gemini/antigravity"
- aider-desk:      "AiderDesk"        | "$HOME/.aider-desk/skills"              | "$HOME/.aider-desk"
- augment:         "Augment"          | "$HOME/.augment/skills"                 | "$HOME/.augment"
- bob:             "IBM Bob"          | "$HOME/.bob/skills"                     | "$HOME/.bob"
- openclaw:        "OpenClaw"         | "$HOME/.openclaw/skills"                | "$HOME/.openclaw"
- codearts-agent:  "CodeArts Agent"   | "$HOME/.codeartsdoer/skills"            | "$HOME/.codeartsdoer"
- codebuddy:       "CodeBuddy"        | "$HOME/.codebuddy/skills"               | "$HOME/.codebuddy"
- codemaker:       "Codemaker"        | "$HOME/.codemaker/skills"               | "$HOME/.codemaker"
- codestudio:      "Code Studio"      | "$HOME/.codestudio/skills"              | "$HOME/.codestudio"
- command-code:    "Command Code"     | "$HOME/.commandcode/skills"             | "$HOME/.commandcode"
- continue:        "Continue"         | "$HOME/.continue/skills"                | "$HOME/.continue"
- cortex:          "Cortex Code"      | "$HOME/.snowflake/cortex/skills"        | "$HOME/.snowflake/cortex"
- crush:           "Crush"            | "$HOME/.config/crush/skills"            | "$HOME/.config/crush"
- deepagents:      "Deep Agents"      | "$HOME/.deepagents/agent/skills"        | "$HOME/.deepagents"
- devin:           "Devin"            | "${XDG_CONFIG_HOME:-$HOME/.config}/devin/skills"    | "${XDG_CONFIG_HOME:-$HOME/.config}/devin"
- dexto:           "Dexto"            | "$HOME/.agents/skills"                  | "$HOME/.dexto"
- droid:           "Droid"            | "$HOME/.factory/skills"                 | "$HOME/.factory"
- firebender:      "Firebender"       | "$HOME/.firebender/skills"              | "$HOME/.firebender"
- forgecode:       "ForgeCode"        | "$HOME/.forge/skills"                   | "$HOME/.forge"
- goose:           "Goose"            | "${XDG_CONFIG_HOME:-$HOME/.config}/goose/skills"    | "${XDG_CONFIG_HOME:-$HOME/.config}/goose"
- hermes-agent:    "Hermes Agent"     | "$HOME/.hermes/skills"                  | "$HOME/.hermes"
- junie:           "Junie"            | "$HOME/.junie/skills"                   | "$HOME/.junie"
- iflow-cli:       "iFlow CLI"        | "$HOME/.iflow/skills"                   | "$HOME/.iflow"
- kilo:            "Kilo Code"        | "$HOME/.kilocode/skills"                | "$HOME/.kilocode"
- kimi-cli:        "Kimi Code CLI"    | "$HOME/.config/agents/skills"           | "$HOME/.kimi"
- kiro-cli:        "Kiro CLI"         | "$HOME/.kiro/skills"                    | "$HOME/.kiro"
- kode:            "Kode"             | "$HOME/.kode/skills"                    | "$HOME/.kode"
- mcpjam:          "MCPJam"           | "$HOME/.mcpjam/skills"                  | "$HOME/.mcpjam"
- mistral-vibe:    "Mistral Vibe"     | "$HOME/.vibe/skills"                    | "$HOME/.vibe"
- mux:             "Mux"              | "$HOME/.mux/skills"                     | "$HOME/.mux"
- openhands:       "OpenHands"        | "$HOME/.openhands/skills"               | "$HOME/.openhands"
- pi:              "Pi"               | "$HOME/.pi/agent/skills"                | "$HOME/.pi/agent"
- qoder:           "Qoder"            | "$HOME/.qoder/skills"                   | "$HOME/.qoder"
- qwen-code:       "Qwen Code"        | "$HOME/.qwen/skills"                    | "$HOME/.qwen"
- replit:          "Replit"           | "${XDG_CONFIG_HOME:-$HOME/.config}/agents/skills"   | "$HOME/.replit"
- rovodev:         "Rovo Dev"         | "$HOME/.rovodev/skills"                 | "$HOME/.rovodev"
- roo:             "Roo Code"         | "$HOME/.roo/skills"                     | "$HOME/.roo"
- tabnine-cli:     "Tabnine CLI"      | "$HOME/.tabnine/agent/skills"           | "$HOME/.tabnine"
- trae:            "Trae"             | "$HOME/.trae/skills"                    | "$HOME/.trae"
- trae-cn:         "Trae CN"          | "$HOME/.trae-cn/skills"                 | "$HOME/.trae-cn"
- warp:            "Warp"             | "$HOME/.agents/skills"                  | "$HOME/.warp"
- zencoder:        "Zencoder"         | "$HOME/.zencoder/skills"                | "$HOME/.zencoder"
- neovate:         "Neovate"          | "$HOME/.neovate/skills"                 | "$HOME/.neovate"
- pochi:           "Pochi"            | "$HOME/.pochi/skills"                   | "$HOME/.pochi"
- adal:            "AdaL"             | "$HOME/.adal/skills"                    | "$HOME/.adal"
- agents:          "Cross-tool ~/.agents/" | "$HOME/.agents/skills"             | "$HOME/.agents"
```

---

## Live catalog enrichment (optional)

When the user runs `--refresh` or asks for *"latest skills"*, augment the embedded catalog with live entries from GitHub topic search. Honors `SKILLS_NO_TELEMETRY=1` — if set, skip silently.

```bash
# Skip if telemetry disabled
[ "$SKILLS_NO_TELEMETRY" = "1" ] && exit 0

# Fetch repos tagged with each topic; merge into catalog.json
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

After fetching, the agent should:
1. Parse each `/tmp/topic-*.json` (Read it, treat as JSON).
2. For each repo: extract `name`, `full_name`, `description`, `topics`, `stargazers_count`.
3. Classify trust by author:
   - `anthropics`, `vercel-labs`, `microsoft`, `google` → official
   - `ComposioHQ`, `supermemoryai`, `remotion-dev`, `firecrawl` → high
   - `obra` → medium
   - everything else → unknown
4. Build a catalog entry for each (with empty `pros`, empty `cons` since they're auto-discovered).
5. Merge with the **Embedded catalog** above — curated entries win on id collision (don't overwrite hand-written pros/cons).
6. Write merged result to `~/.claude/skills/skills-curator-lite/catalog.json` with a `fetched_at` timestamp.

Cache TTL: 24 hours. On subsequent calls, prefer cached catalog.json if its mtime is recent.

**Why no skills.sh scraping:** the full version's project memory documents that skills.sh HTML scraping was deliberately removed in v4.0 (brittle, dishonest for a judgment tool). GitHub topic search is a stable JSON API that gets us breadth without that fragility.

---

## Security Scan Patterns (for safety check)

When evaluating a local skill folder, the agent runs Grep with these patterns. Any HIGH or CRITICAL match should halt the install pending review.

<!-- scanner:ignore-block-start -->
| Severity | Pattern (regex) | Why |
|---|---|---|
| CRITICAL | `curl\s+\S+\|\s*(sh\|bash)` | Remote code execution: pipe-to-shell |
| CRITICAL | `wget\s+\S+\|\s*(sh\|bash)` | Remote code execution: pipe-to-shell |
| CRITICAL | `rm\s+-rf\s+/\s*$` | Destructive root deletion |
| HIGH | `sk-[A-Za-z0-9]{32,}` | Hardcoded OpenAI key |
| HIGH | `sk-ant-[A-Za-z0-9-]{32,}` | Hardcoded Anthropic key |
| HIGH | `gh[pousr]_[A-Za-z0-9]{36,}` | Hardcoded GitHub PAT |
| HIGH | `ghs_[A-Za-z0-9]{36,}` | Hardcoded GitHub server token |
| HIGH | `password\s*=\s*['"][^'"]+['"]` | Hardcoded password literal |
| MEDIUM | `\beval\s*\(` | Dynamic code execution |
| MEDIUM | `\bexec\s*\(` | Dynamic code execution |
| MEDIUM | `import\s*\(.+\$\{` | Dynamic import with interpolation |
| MEDIUM | `base64\.(?:b64)?decode` | Possible obfuscation |
| MEDIUM | `\bkeychain\b\|\bcredmanager\b\|\bsecretservice\b` | OS credential store access |
| LOW | `http://[^"\s]+` (non-localhost) | Unencrypted endpoint |

Example Grep run:
```bash
SKILL_PATH="$1"
echo "Scanning $SKILL_PATH..."
grep -rE 'curl\s+\S+\|\s*(sh|bash)' "$SKILL_PATH" && echo "CRITICAL: pipe-to-shell"
grep -rE 'sk-[A-Za-z0-9]{32,}'      "$SKILL_PATH" && echo "HIGH: hardcoded API key"
# ...etc
```
<!-- scanner:ignore-block-end -->

The agent should run each pattern via the Grep tool (preferred over Bash for performance and permissions). Documentation that lists pattern definitions verbatim should be wrapped in `<!-- scanner:ignore-block-start -->` / `<!-- scanner:ignore-block-end -->` (or `# scanner:ignore` for single-line Python) so the engine and agent skip them during self-scans.

---

## When to recommend the full Skills Curator instead

Lite is feature-parity with v4.3 of the Python version for everything in this file. The full version still wins for:

- **Speed on 100+ skills** — single Python pass beats N agent steps
- **Regression-tested behavior** — 35 pytest cases catch edge cases
- **Cross-device Gist sync** — needs Python's `urllib` + Gist API plumbing

If the user has Python 3.10+ available and one of those matters, point them at:
```bash
npx skills add captkernel/Skills_Curator    # full Python version, both ship in same plugin
```

The two skills don't conflict — install both if you like. Different registry paths.

---

## Why Lite is now the default

The Python engine is fast and tested, but it's a barrier for users who don't have Python 3.10+ or don't want it. Lite proves the same model works as pure prompt engineering — agent reads the spec, reasons about the project, writes the registry, runs the security checks. **Slower per-call, but zero install.**

For a tool whose pitch is *judgment* (already an agent-driven concept), agent-driven implementation is philosophically consistent.
