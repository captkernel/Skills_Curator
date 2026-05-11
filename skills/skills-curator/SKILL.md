---
name: skills-curator
description: Use when the user mentions a skill/plugin by name, asks "should I install X", asks for skill recommendations, wants a security check on a skill, asks about duplicates or conflicts, wants to create a new skill, or wants to migrate skills across agent platforms (Cursor, Codex, Gemini, etc.).
metadata:
  version: "4.4.2"
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

**Skills Curator's main USP is context-aware judgment.** Don't wait for the user to say "evaluate this skill" — surface relevant skills when project context implies one would help.

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

## When to activate

The frontmatter `when_to_use` covers the explicit triggers. One additional rule worth surfacing here:

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

## Customizing an external skill (`--customize`)

When a skill is good but its examples don't match the user's stack (Vue examples in a React project, Django in a FastAPI project), fork it as a project-tailored version:

```bash
python registry.py --customize <source>   # source = registered id, local path, or owner/repo@skill
```

The engine emits a per-section plan (`keep`, `keep-trim`, `rewrite-stack`, `drop-or-rewrite`, `rewrite-frontmatter`) and writes a fork at `~/.claude/skills/<name>-for-<project>/SKILL.md`. **The agent then rewrites each section** per the action column — engine produces the plan, agent does the prose. Use `--no-fork` to preview the plan without writing.

---

## Platform management

Skills Curator supports 55 agent platforms (`claude-code` and `github-copilot` are first-class; the rest are reachable via the same migration verbs).

When the user asks *"where can I install this?"* or wants to copy a skill across platforms, use `--platforms` and `--migrate <target[,...]>`. Targets accept a single id, a comma list, or `detected` (every platform on this machine). Without an explicit target in a non-TTY context, migration defaults to `claude-code`; in a TTY it prompts.

For *"list all supported platforms"*, run `--platforms --verbose` — never read the `PLATFORMS` dict by hand. Full flag reference: `references/commands.md`.

---

## Common Mistakes

| Mistake | What to do instead |
|---|---|
| Recommending a Medium/Unknown-trust skill without `--check` first | Trust gate is non-negotiable — security-scan first, flag findings to user |
| Manufacturing a recommendation when no skill fits | Say no good match was found, explain *why*, offer to do the task directly or scaffold via `--author` |
| Re-evaluating a skill the registry already has a verdict for | Run `--history <id>` first; surface the prior verdict instead of re-deciding |
| Running `--auto` more than once per session | Fingerprint-based; one call is enough until the project changes |
| Padding the evaluation output with prose | Use the locked output format exactly — `--export-eval` reproduces it |
| Reading `references/commands.md` by hand to list flags | Run the engine (`--platforms --verbose`, etc.) — it renders consistently |

---

## Other commands and tier choice

Full CLI reference: `references/commands.md` (covers `--check`, `--list`, `--discover`/`--find`, `--health`, `--stale`, `--platforms`, `--migrate`, `--author`, `--customize`, `--sync`/`--push`, `--validate`).

**Tier choice:** `skills-curator-lite` is the default — same intelligence layer, no Python (Bash/Read/Glob/Grep + embedded catalogs). Use the Python version when you have 100+ skills (single-pass speed beats N agent steps), need cross-device Gist sync, or want regression-tested behavior. Both ship in the plugin and use different registry paths — they don't conflict.
