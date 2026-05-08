---
name: skills-curator
description: >
  The intelligence layer for Claude skills. Maintains a trust-rated catalog
  (curated entries + live GitHub topic search), identifies what fits your
  project (stack, deps, CLAUDE.md), recommends with pros/cons and per-project
  customization advice, persists every decision so you never re-evaluate, and
  migrates across 55 supported agent platforms.
  Use when the user mentions a skill, asks "should I install X", asks to
  evaluate / recommend / audit / check a skill, asks "what skills fit this
  project", asks for a list of supported platforms, or wants to migrate skills
  to another agent.
metadata:
  version: "4.4.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  license: MIT
when_to_use:
  - User mentions a new skill, plugin, or tool by name
  - User asks "should I install X" or "what skills fit this project"
  - User asks to list, search, compare, or evaluate skills
  - User asks for skill recommendations based on the current project
  - User wants to check if a skill is safe to install
  - User asks about duplicate or conflicting skills
  - User wants to create a new skill
  - User wants to migrate skills to another agent (Cursor, Codex, Gemini CLI, etc.)
  - User wants to share an evaluation of a skill (export to markdown)
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
---

# Skills Curator v4

**Decide once. Re-decide never.**

Other tools install skills. Skills Curator **persists your judgment** so you never re-decide. Every evaluation produces a structured record (pros / cons / conflicts / verdict / partial-adoption plan) that becomes part of a personal registry — and a markdown artifact you can paste in PRs, ADRs, or team docs.

Read reference files on demand:
- `references/commands.md` — all commands and flags
- `references/evaluation.md` — evaluation format and principles
- `references/discovery.md` — how recommendations work, response templates, categories
- `references/schema.md` — registry data model

---

## First activation in a session

The first time this skill activates in a session, open with this two-line orientation **before** answering, then continue with whatever was asked:

> 🧭 *Skills Curator loaded — your intelligence layer for Claude skills.*
> *I maintain a trust-rated catalog (curated entries + live GitHub topic search), identify what fits your project (stack, deps, CLAUDE.md), and on request return ranked lists with pros, cons, and per-project customization advice — persisting every decision so you don't re-evaluate. Working on your request now.*

Skip the orientation entirely if `--auto` (next section) is about to surface concrete picks — those are more useful than a generic intro. Don't repeat orientation in later messages of the same session.

---

## Proactive activation (the intelligence layer)

**Skills Curator's main USP is judgment that activates without being asked.** Don't wait for the user to say "evaluate this skill" — surface relevant skills the moment a project context implies one would help.

### Run this at the start of any session in a real project

If the working directory contains `CLAUDE.md`, `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or `Cargo.toml`, run **once, silently** at the start of the session:

```bash
python ~/.claude/skills/skills-curator/scripts/registry.py --auto
```

`--auto` is fingerprint-based: it only does a full re-scan when the project has actually changed (new dep, new framework, new CLAUDE.md content). Otherwise it prints a one-line "no changes since last scan" and exits. **Cheap to run on every session — designed to be called proactively.**

If `--auto` surfaces top picks, weave them into your first response to the user *as a quiet observation*, not a sales pitch:

> "While we work on this — I noticed you're using Next.js + Tailwind. There's a `frontend-design` skill (🏛️ official) that adds aesthetic guidelines that match your stack. Want me to evaluate it?"

### Re-run when the project shifts

After the user adds/removes a dependency, edits CLAUDE.md, or installs a new framework, run `--auto --refresh`. The fingerprint will detect the drift.

### When the user describes a problem instead of naming a skill

If the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, *"no one writes good commit messages"*, or any other complaint that hints at a missing capability, run:

```bash
python registry.py --symptoms "<their phrase>"
```

This maps complaints to skill categories using a built-in symptom→tag table and surfaces matching catalog entries. Don't make the user reverse-engineer "is there a skill for X" — listen for symptoms and recommend.

### Don't over-trigger

- Run `--auto` **at most once per session** unless the project actually changes.
- Run `--symptoms` only when the user expresses a clear pain point. Don't fire it on every passing reference.
- If `--auto` returns nothing strong, **say nothing**. Silence is a valid answer when the stack is well-covered.

---

## When to activate this skill

Use Skills Curator when the user says any of:

- "Should I install [skill]?" / "Is [skill] worth it?"
- "Find a skill for X" / "Is there a skill that does X?"
- "What skills fit this project?" / "Recommend skills"
- "Audit my skills" / "Review my skills" / "Are any of my skills conflicting?"
- "Is [skill] safe?" / "Check this skill"
- "Migrate my skills to Cursor / Codex / Gemini"
- "Have we evaluated [skill] before?" / "What did we decide about [skill]?"
- Mentions a specific skill, plugin, or tool by name in a context that implies adoption

If the request is "how do I do X?" and X is plausibly a skill domain (testing, deploy, design, scraping, docs, etc.), **search the registry and catalog before answering from general knowledge** — there may already be a battle-tested skill for it.

---

## The three verbs

These are the three slash commands surfaced in Claude Code. Everything else is in the CLI for power users.

| Verb | When | What it does |
|---|---|---|
| `/skill-evaluate <id-or-path>` | User asks "should I install X?" | Security-scans, reads CLAUDE.md, produces ADOPT/PARTIAL/SKIP with full evidence, persists the decision |
| `/skill-recommend` | User asks "what skills fit?" | Scans project, ranks by tag-overlap × trust tier (not popularity), splits capability vs preference |
| `/skill-audit` | User asks "review my skills" | Finds duplicates, preference conflicts, security gaps, stale versions, low-health skills |

---

## Setup

```bash
# Registry lives at:
~/.claude/skills/skills-curator/registry.json

# CLI:
python ~/.claude/skills/skills-curator/scripts/registry.py
# Windows:
python "%USERPROFILE%\.claude\skills\skills-curator\scripts\registry.py"
```

---

## Workflow: discover → evaluate → install

The full path from "what could help here?" to "decision saved" is six steps. Don't skip ahead — each step de-risks the next.

**Step 1: Understand what the user actually needs.**
What domain (React, testing, design, deployment, scraping, docs)? What specific task? Is this likely common enough that a skill exists?

**Step 2: Check the registry first.**
If we've evaluated this skill (or one like it) before, surface the prior verdict instead of re-evaluating.
```bash
python registry.py --history <skill-id>
python registry.py --search <term>
```

**Step 3: If unevaluated, recommend or discover.**
- Project-aware ranking (best signal): `python registry.py --recommend`
- Free-text catalog search: `python registry.py --find <query>` (alias for `--discover`)

**Step 4: Verify trust before recommending anything.**
- 🏛️ Official (Anthropic, Vercel, Microsoft) → safe to surface
- ✅ High (established orgs) → safe to surface
- 🟡 Medium / ⬜ Community / ❓ Unknown → only after `--check <path>` security scan
- Never recommend a skill from an unknown author without flagging it.

**Step 5: Run the full evaluation (the only step that produces a verdict).**
Trigger `/skill-evaluate` — runs security scan → project scan → reads CLAUDE.md → produces ADOPT/PARTIAL/SKIP with pros/cons/conflicts → persists. Use the output format below.

**Step 6: Persist + offer the export.**
```bash
python registry.py --eval <id> <project> <verdict> "<summary>" --pros "..." --cons "..." --conflicts "..."
python registry.py --export-eval <id>   # PR-ready markdown
```

### When no skill fits

If `--recommend` returns nothing strong, OR `--find <query>` finds no matches, OR the top match has Medium/Unknown trust + zero evaluations, **don't manufacture a recommendation.** Instead:

1. Tell the user no good match was found and explain *why* (no tag overlap, low trust, security flags).
2. Offer to do the task directly with general capabilities.
3. Offer to scaffold a custom skill: `python registry.py --author`.

A "no recommendation" answer is a feature, not a failure — it's the whole point of judgment over popularity.

---

## Output format for evaluations

Use this structure exactly. Format matters because it's also what `--export-eval` reproduces.

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

Don't pad. The user can read between sections; verbose justifications hide the verdict.

---

## Persisting

After the user agrees with a verdict, save it:

```bash
python registry.py --eval <id> <project> <verdict> "<summary>" \
  --pros "<a>,<b>" --cons "<c>,<d>" --conflicts "<e>"
```

If the skill isn't registered yet, `--add` it first.

---

## Customizing an external skill for this project (`--customize`)

When the user wants to install a skill but it ships examples from a stack they don't use (Vue examples in a React project, Django in a FastAPI project), use `--customize` to fork it as a project-tailored version:

```bash
python registry.py --customize <source>        # source = registered id, local path, or owner/repo@skill
```

The engine:
1. Loads the external `SKILL.md`
2. Scans this project (same signals as `--scan`)
3. Scores each section by relevance to the project
4. Emits a customization plan with per-section actions: `keep`, `keep-trim`, `rewrite-stack`, `drop-or-rewrite`, `rewrite-frontmatter`
5. Writes a fork at `~/.claude/skills/<name>-for-<project>/SKILL.md` containing the plan

**The agent then rewrites each section** per the action column. Sections marked `rewrite-stack` should have their examples rewritten to use this project's framework. Sections marked `drop-or-rewrite` should be dropped or rewritten from scratch. The engine produces the structured plan; the agent does the prose.

Use `--no-fork` to print only the plan without writing the file.

---

## Platform management

Skills Curator knows about every agent platform `skills.sh` supports — 55 in total. Primary first-class support is **Claude Code** and **GitHub Copilot**; everything else is reachable via the same migration verbs.

When the user asks *"where can I install this?"*, *"what agents do I have?"*, or wants to copy a skill across platforms:

```bash
python registry.py --platforms                  # show detected + primary platforms
python registry.py --platforms --verbose        # show all 55
python registry.py --migrate                    # interactive: prints platforms, prompts
python registry.py --migrate cursor             # single target
python registry.py --migrate cursor,codex,roo   # multi-target
python registry.py --migrate detected           # every platform on this machine
python registry.py --migrate --all-detected     # equivalent flag form
```

When migrating without an explicit target in a non-TTY context, Skills Curator defaults to `claude-code` (the primary ecosystem). In TTY, it prompts.

If the user asks *"list all supported platforms"*, run `--platforms --verbose`. Don't read the `PLATFORMS` dict by hand — the engine renders it consistently.

---

## Common other commands

```bash
python registry.py --check <path>              # security scan a folder
python registry.py --list                      # all registered skills
python registry.py --discover [term]           # search live catalog
python registry.py --find [term]               # alias for --discover
python registry.py --health                    # A-D health per skill
python registry.py --stale                     # GitHub release version drift
python registry.py --platforms [--verbose]     # supported agent platforms
python registry.py --migrate [target[,...]]    # cross-agent copy (multi-target)
python registry.py --author                    # scaffold new SKILL.md
python registry.py --customize <source>        # fork external skill for this project
python registry.py --sync   |   --push         # cross-device Gist sync
python registry.py --validate --strict         # CI integrity check
```

**`skills-curator-lite` is the default tier** — same intelligence layer, no Python. The agent does everything via Bash/Read/Glob/Grep using embedded catalogs and rules. Use this Python version when you have 100+ skills (single-pass speed beats N agent steps), need cross-device Gist sync, or want regression-tested behavior. Both ship in the plugin and don't conflict (different registry paths).

Full reference: `references/commands.md`.

---

## Why no install counts

skills.sh has no public JSON API for per-skill telemetry. Skills Curator deliberately ranks on tag overlap × trust tier rather than fake popularity numbers. A skill that fits this project's stack with 200 installs is a better match than one with 50,000 that doesn't. If the user explicitly asks for popularity, point them at skills.sh.
