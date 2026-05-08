---
name: skills-curator
description: >
  Decide once, re-decide never. Skills Curator evaluates Claude skills against
  your project goals before installing, persists every decision (pros, cons,
  conflicts, security findings) in a personal registry, and exports them as
  PR-ready markdown artifacts. Recommends skills from the live ecosystem
  ranked by project fit, not popularity.
  Use when the user mentions a skill, asks "should I install X", asks to
  evaluate / recommend / audit / check a skill, or wants to migrate skills to
  another agent.
metadata:
  version: "4.0.0"
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
- `references/discovery.md` — how recommendations work
- `references/schema.md` — registry data model

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

## Workflow when user mentions a skill

1. **Check the registry first.** If we've evaluated this skill before, surface the prior verdict + summary instead of re-evaluating from scratch.
   ```bash
   python registry.py --history <skill-id>
   ```
2. **If unevaluated:** run `/skill-evaluate` flow (security scan → project scan → CLAUDE.md read → structured verdict → save).
3. **Always offer the export:** `python registry.py --export-eval <id>` produces a PR-ready markdown artifact.

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

## Common other commands

```bash
python registry.py --check <path>              # security scan a folder
python registry.py --list                      # all registered skills
python registry.py --discover [term]           # search live catalog
python registry.py --health                    # A-D health per skill
python registry.py --stale                     # GitHub release version drift
python registry.py --migrate cursor            # cross-agent copy
python registry.py --author                    # scaffold new SKILL.md
python registry.py --sync   |   --push         # cross-device Gist sync
python registry.py --validate --strict         # CI integrity check
```

Full reference: `references/commands.md`.

---

## Why no install counts

skills.sh has no public JSON API for per-skill telemetry. Skills Curator deliberately ranks on tag overlap × trust tier rather than fake popularity numbers. A skill that fits this project's stack with 200 installs is a better match than one with 50,000 that doesn't. If the user explicitly asks for popularity, point them at skills.sh.
