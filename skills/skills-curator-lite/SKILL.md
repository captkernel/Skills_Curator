---
name: skills-curator-lite
description: >
  Skills Curator without Python. Same judgment-first model — evaluate before
  installing, persist your decisions, recommend by project fit — but the agent
  does the work directly using Bash, Read, Glob, and Grep. Choose this over the
  full version if you don't have Python, want zero dependencies, or prefer the
  agent reasoning explicitly over an opaque engine.
metadata:
  version: "1.0.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  license: MIT
  derived_from: skills-curator
when_to_use:
  - User mentions a new skill, plugin, or tool by name
  - User asks "should I install X" or "what skills fit this project"
  - User asks for skill recommendations based on the current project
  - User wants to check if a skill is safe to install
  - User wants to share an evaluation of a skill
  - User does NOT have Python installed (this is the no-Python version)
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

This is a markdown-only companion to [Skills Curator](https://github.com/captkernel/Skills_Curator). Same model, no engine: the agent reads project files, applies the rules below, writes to a JSON registry directly, and runs grep-based security checks. Use this when:

- Python isn't available on the system
- You want a transparent flow you can follow line-by-line
- You don't need Gist sync or GitHub release-version checks (those need Python)

If you have Python, prefer the full `skills-curator` skill — it's faster on big projects and ships with `--auto` (project fingerprinting), `--symptoms`, `--customize`, and 26 unit tests.

---

## Where the registry lives

```
~/.claude/skills/skills-curator-lite/registry.json
```

Initialize it the first time:

```bash
mkdir -p ~/.claude/skills/skills-curator-lite
[ -f ~/.claude/skills/skills-curator-lite/registry.json ] || \
  echo '{"version":"3.0","skills":[]}' > ~/.claude/skills/skills-curator-lite/registry.json
```

Schema is identical to the full version (so you can switch later): `version`, `last_updated`, `skills[]` where each skill has `id`, `name`, `source`, `install`, `type`, `tags`, `evaluations[]`, `security_scan`, `installed_version`.

---

## The three verbs

### 1. RECOMMEND — what skills fit this project?

The agent does these steps in order:

1. **Scan the project for signals.** Use Glob to detect languages, then Read on key config files:
   ```bash
   ls package.json requirements.txt pyproject.toml Pipfile go.mod Cargo.toml 2>/dev/null
   ```
   For each file present, Read it. Extract framework keywords using the Framework Signals table below.

2. **Read CLAUDE.md and README.md** if present. Extract goal keywords using the Goal Signals table.

3. **Build a tag set** = (languages detected) ∪ (framework matches) ∪ (goal matches).

4. **Match against the embedded catalog** (see "Catalog" below). For each catalog skill, count tag overlap with project tags. Skip skills already in the registry.

5. **Score** = `len(overlap) * 10 + trust_bonus` where trust_bonus is `official: 20, high: 15, medium: 5, community: 2`.

6. **Sort descending. Show top 5.** Group by capability vs preference.

Present each recommendation in the response template:
```
I found a skill that might help: <Name> (<trust-emoji> <trust-level>)

What it does: <one-line>
Why it fits: matches [<top-3-overlapping-tags>]

Install:
  npx skills add <owner/repo> --skill <skill-id>

Evaluate first:
  /skill-evaluate <skill-id>
```

### 2. EVALUATE — should I install this specific skill?

The agent does these steps in order:

1. **Check the registry first.** Read `~/.claude/skills/skills-curator-lite/registry.json` and look for the skill id. If present, surface the prior verdict + summary instead of re-evaluating.

2. **If the skill is a local folder, run a security scan.** Use Grep with the patterns in the "Security Scan Patterns" section below. Any HIGH or CRITICAL match → stop and report.

3. **Read CLAUDE.md.** Use this to ground the evaluation against what the project actually does, not against imagined goals.

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

5. **Persist the decision.** Update the registry by writing a new evaluations entry. Use Bash + jq if available, or write the whole file via Read → modify → Write:
   ```bash
   # Append an evaluation entry (requires jq)
   REG=~/.claude/skills/skills-curator-lite/registry.json
   jq --arg id "<skill-id>" \
      --arg ev '{"date":"<YYYY-MM-DD>","project":"<project>","verdict":"<adopt|partial|skip>","summary":"<text>","pros":[],"cons":[],"conflicts":[]}' \
      '(.skills[] | select(.id == $id) | .evaluations) += [($ev | fromjson)]' \
      "$REG" > "$REG.tmp" && mv "$REG.tmp" "$REG"
   ```
   If `jq` isn't available, the agent should Read the registry, parse it as JSON, modify the right skill's `evaluations` array, and Write the whole file back.

### 3. AUDIT — review my whole stack

The agent does these checks in one pass:

1. **Duplicates.** Group registered skills by tag overlap > 60%. Flag pairs that look like they do the same thing.
2. **Preference conflicts.** For skills with `type: preference`, look for contradictory rules (e.g., two style guides). Flag pairs.
3. **Security gaps.** List skills where `security_scan` is missing or empty. Recommend running EVALUATE on each.
4. **Stale evaluations.** List skills last evaluated > 6 months ago.

Present as a triaged punch list — most-critical first.

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

### Goal Signals (keywords found in CLAUDE.md / README.md)

| Phrase pattern (case-insensitive) | Tags emitted |
|---|---|
| `scrape`, `crawl`, `extract data` | `scraping, data-extraction` |
| `auth`, `login`, `session` | `auth, session-management` |
| `dashboard`, `admin panel` | `frontend, dashboard` |
| `migrate`, `migration` | `database, migration` |
| `agent`, `LLM`, `AI` | `ai, agents` |
| `test`, `testing`, `coverage` | `testing` |
| `deploy`, `CI/CD`, `release` | `ci-cd, deploy` |
| `documentation`, `docs` | `docs` |
| `accessibility`, `a11y` | `accessibility, ui` |

---

## Embedded catalog

The full version fetches from skills.sh; Lite uses this curated subset (top trusted entries verified May 2026):

```yaml
- id: agent-browser
  name: Agent Browser
  source: https://github.com/vercel-labs/agent-browser
  install: npx skills add vercel-labs/agent-browser --skill agent-browser
  type: capability
  trust: high
  tags: [browser-automation, scraping, playwright, testing, web]
  description: Browser automation via CDP. Element refs, 6 auth methods, screenshots, form fill.

- id: frontend-design
  name: Frontend Design
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill frontend-design
  type: preference
  trust: official
  tags: [frontend, design, ui, react, design-system]
  description: Bold design philosophy before writing UI code. Prevents AI-slop aesthetics.

- id: vercel-react-best-practices
  name: React Best Practices
  source: https://github.com/vercel-labs/agent-skills
  install: npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices
  type: preference
  trust: high
  tags: [react, frontend, nextjs, performance]
  description: React/Next.js performance rules ordered by impact.

- id: web-design-guidelines
  name: Web Design Guidelines
  source: https://github.com/vercel-labs/agent-skills
  install: npx skills add vercel-labs/agent-skills --skill web-design-guidelines
  type: preference
  trust: high
  tags: [frontend, design, accessibility, ui]
  description: UI/UX rules — accessibility, typography, dark mode.

- id: artifacts-builder
  name: Artifacts Builder
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill artifacts-builder
  type: capability
  trust: official
  tags: [artifacts, react, ui, demo]
  description: Build standalone HTML/React artifacts you can paste anywhere.

- id: pdf-handler
  name: PDF Handler
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill pdf
  type: capability
  trust: official
  tags: [pdf, documents, document-processing]
  description: Read, parse, and extract from PDF files.

- id: docx-handler
  name: DOCX Handler
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill docx
  type: capability
  trust: official
  tags: [docx, documents, document-processing]
  description: Read and write Microsoft Word documents.

- id: xlsx-handler
  name: XLSX Handler
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill xlsx
  type: capability
  trust: official
  tags: [xlsx, spreadsheet, document-processing]
  description: Read and write Excel files.

- id: superpowers-tdd
  name: Test-Driven Development
  source: https://github.com/anthropics/skills
  install: npx skills add anthropics/skills --skill superpowers-tdd
  type: preference
  trust: official
  tags: [testing, tdd, code-quality]
  description: Strict TDD discipline — write tests first, refactor under green.

- id: skills-curator
  name: Skills Curator (full)
  source: https://github.com/captkernel/Skills_Curator
  install: npx skills add captkernel/Skills_Curator
  type: capability
  trust: high
  tags: [meta, skill-management, registry, evaluation]
  description: The Python version of this skill. More features. Requires Python 3.10+.
```

To extend the catalog, add entries here in the same shape. Higher trust + tag count = better recommendations.

---

## Symptom → skill mapping

When the user describes a problem instead of naming a skill, match against this table and search the catalog by tag:

| User says (substring) | Look for skills tagged |
|---|---|
| `slow test`, `tests are slow` | `testing, performance` |
| `failing ci`, `ci is broken` | `ci-cd, github-actions` |
| `ugly ui`, `design is bad` | `frontend-design, design-system, ui` |
| `manual deploy` | `ci-cd, deploy` |
| `no docs`, `missing docs` | `docs, docgen` |
| `messy commits`, `bad commit messages` | `commit-writer, conventional-commits` |
| `slow build` | `build-tools, performance` |
| `auth broken`, `login issue` | `auth, session-management` |
| `scraping broken`, `browser auth` | `scraping, browser-automation` |
| `accessibility`, `a11y` | `accessibility, ui` |
| `pr review takes` | `pr-review, code-review` |

---

## Security Scan Patterns (for `--check`)

When evaluating a local skill folder, the agent runs Grep with these patterns. Any match counts as a finding; CRITICAL/HIGH should stop the install.

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

Example:
```bash
SKILL_PATH=$1
echo "Scanning $SKILL_PATH..."
grep -rE 'curl\s+\S+\|\s*(sh|bash)' "$SKILL_PATH" && echo "CRITICAL: pipe-to-shell"
grep -rE 'sk-[A-Za-z0-9]{32,}' "$SKILL_PATH" && echo "HIGH: hardcoded API key"
# ...etc
```

---

## When to recommend the full Skills Curator instead

If the user says any of:

- "I want recommendations updated automatically" → full version's `--auto` does fingerprint-based drift detection
- "I want to sync my registry across machines" → full version supports private GitHub Gist sync
- "I want to fork an external skill for my project" → full version's `--customize` does this
- "I want to migrate skills to Cursor / Codex / etc." → full version's `--migrate` writes to 9 agent paths
- "I want unit tests on the registry tool" → full version ships 26 pytest cases

Tell them: `npx skills add captkernel/Skills_Curator` (Python 3.10+ required).

---

## Why Lite exists

The Python engine is fast and tested, but it's a barrier for users who don't have Python or don't want it. Lite proves the same model works as pure prompt engineering — the agent reads the spec, reasons about the project, writes the registry, runs the grep checks. Slower per-call, but **zero install**.

The two skills don't conflict — install both if you like. They use different registry paths.
