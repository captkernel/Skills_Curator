---
name: skills-curator
description: Use when the user mentions a skill/plugin by name, asks "should I install X", asks "how do I do X", "find a skill for X" or "is there a skill that...", asks for skill recommendations, wants a security check on a skill, asks about duplicates or conflicts, wants to create a new skill, or wants to migrate skills across agent platforms (Cursor, Codex, Gemini, etc.).
metadata:
  version: "4.7.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  license: MIT
when_to_use:
  - User mentions a new skill, plugin, or tool by name
  - User asks "should I install X" or "what skills fit this project"
  - User asks "find a skill for X", "is there a skill that...", or "how do I do X" where X is a skill domain
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

**The intelligence layer for Claude skills — find-skills plus judgment.**

Skill finders tell you what is popular; Skills Curator tells you what fits your project and is safe to install. Other skill managers stop at install. Skills Curator's headline capability is **`--customize`**: take any external skill, scan the user's project, and produce a project-tailored fork with examples rewritten for *their* stack (Vue → React, Django → FastAPI, generic CI → their CI). The engine emits a per-section action plan (`keep`, `keep-trim`, `rewrite-stack`, `drop-or-rewrite`, `rewrite-frontmatter`); the agent does the prose. Nothing else in the ecosystem does this.

The second pillar is **persistent judgment**: every evaluation produces a structured record (pros / cons / conflicts / verdict / partial-adoption plan) saved to a personal registry — so the same skill is never re-evaluated from scratch, and decisions become PR-pasteable artifacts.

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

Skip the orientation if `--auto` (next section) is about to surface concrete picks. Don't repeat it later in the session.

---

## Proactive activation (the intelligence layer)

Customization is the headline capability; **proactive activation** is what makes it useful unprompted. Don't wait for the user to say "evaluate this skill" — surface relevant skills when project context implies one would help, and lead with `--customize` when the skill's stack doesn't match.

### Run this at the start of any session in a real project

If the working directory contains `CLAUDE.md`, `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or `Cargo.toml`, run **once, silently** at the start of the session:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/registry.py" --auto
```

`--auto` is fingerprint-based: it only does a full re-scan when the project has actually changed (new dep, new framework, new CLAUDE.md content). Otherwise it prints a one-line "no changes since last scan" and exits. **Cheap to run on every session — designed to be called proactively.**

If `--auto` surfaces top picks, weave them into your first response to the user *as a quiet observation*, not a sales pitch:

> "While we work on this — I noticed you're using Next.js + Tailwind. There's a `frontend-design` skill (🏛️ official) that adds aesthetic guidelines that match your stack. Want me to evaluate it?"

After the user adds/removes a dependency or edits CLAUDE.md, run `--auto --refresh`; the fingerprint detects drift.

### When the user describes a problem instead of naming a skill

If the user says *"my tests are slow"*, *"deploys are manual"*, *"the UI looks ugly"*, *"no one writes good commit messages"*, or any other complaint that hints at a missing capability, run:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/registry.py" --symptoms "<their phrase>"
```

This maps complaints to skill categories and surfaces matching catalog entries — listen for symptoms and recommend.

### Don't over-trigger

Run `--auto` at most once per session unless the project changes, and `--symptoms` only on a clear pain point. If `--auto` finds nothing strong, say nothing.

---

## When to activate

The frontmatter `when_to_use` covers the explicit triggers. If the request is "how do I do X?" or "find a skill for X" and X is plausibly a skill domain (testing, deploy, design, scraping, docs, etc.), **run the CURATE fast path below before answering from general knowledge**.

---

## CURATE fast path: "find a skill for X"

```bash
python "${CLAUDE_SKILL_DIR}/scripts/registry.py" --curate "<query>" [--limit N]    # default 5
```

Searches three sources — the curated catalog, GitHub topic search, and skills.sh (`https://skills.sh/api/search`, per-skill results installed with `npx skills add <source> --skill <name>`). Results use a blended ranking: 0.35 relevance + 0.30 project fit + 0.20 trust + 0.15 popularity (log-scaled installs/stars); with a query, fit counts as fit × relevance. Previously rejected (SKIP) skills are ×0.3 and labelled; installed ones are excluded. Every result prints a `why:` line, a project-scope install command, a skills.sh link when known, and a "scan before installing" footer.

Relay the top picks with their `why:` lines. Before the user installs anything Medium/Community/Unknown trust, run `--check` or `/skill-evaluate`. Third-party audits (Socket/Snyk/Gen via skills.sh) appear in `--eval`/`--check`/`--export-eval` as **advisory only** — they never replace our own scan. Queries are not logged by us.

**Rival note:** if `vercel-labs/find-skills` is installed, the engine flags it as overlapping — it searches the same index but ranks by install count only. Suggest keeping one finder; Skills Curator adds project fit, the security scan, persistence, and `--customize`.

---

## The three verbs

These are the three slash commands surfaced in Claude Code. Everything else is in the CLI for power users.

| Verb | When | What it does |
|---|---|---|
| `/skill-evaluate <id-or-path>` | User asks "should I install X?" | Security-scans, reads CLAUDE.md, produces ADOPT/PARTIAL/SKIP with full evidence, persists the decision |
| `/skill-recommend` | User asks "what skills fit?" | Scans project, blended rank (fit, trust, capped popularity) with a `why:` line, splits capability vs preference |
| `/skill-audit` | User asks "review my skills" | Finds duplicates, preference conflicts, security gaps, stale versions, low-health skills |

---

## Setup

```bash
# Registry lives at:
~/.claude/skills/skills-curator/registry.json

# CLI (the script ships in this skill's own scripts/ folder; Claude Code
# fills in this skill's folder for manual and plugin installs alike):
python "${CLAUDE_SKILL_DIR}/scripts/registry.py"
```

Every `python registry.py ...` command below means `python "${CLAUDE_SKILL_DIR}/scripts/registry.py" ...`.

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
- Free-text search across all sources: `python registry.py --curate "<query>"` (see CURATE fast path)

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

If `--recommend` returns nothing strong, OR `--curate <query>` finds no matches, OR the top match has Medium/Unknown trust + zero evaluations, **don't manufacture a recommendation.** Instead:

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

## `--customize`: the headline capability

Most skills ship with examples written for someone else's codebase. Adopting them means tolerating mismatched examples or rewriting by hand. `--customize` is the one feature that solves this end-to-end.

```bash
python registry.py --customize <source>   # source = registered id, local path, or owner/repo@skill
```

**What it does, step by step:**

1. **Resolves the source.** Accepts a registered skill id, a local path, or a GitHub `owner/repo@skill-name` — fetches the SKILL.md from any of them.
2. **Scans the current project** for signals (tags, languages, framework keywords from `package.json`, `requirements.txt`, `CLAUDE.md`, etc.).
3. **Splits the source SKILL.md into sections** and scores each one against the project's tag set + languages.
4. **Emits a per-section action plan** with one of: `keep`, `keep-emphasize`, `keep-trim`, `rewrite-stack` (examples target a stack the project doesn't use), `drop-or-rewrite`, `rewrite-frontmatter`.
5. **Scaffolds the fork** at `~/.claude/skills/<name>-for-<project>/SKILL.md` with the plan baked in as a table the agent walks row-by-row.
6. **The agent then rewrites each section** per the action column — engine produces the plan, agent does the prose. Vue snippets become React snippets. Django routes become FastAPI routes. Generic deploy scripts become your CI's deploy scripts.

Use `--no-fork` to preview the plan without writing the fork.

**Why this is the USP:** installation is a solved problem; *adaptation* isn't. Every other skill manager assumes one-size-fits-all SKILL.md content. Skills Curator is the only one that treats SKILL.md as a template to be specialized per project — and the only one that does it with a project-aware action plan instead of a blanket find-and-replace.

When you recommend a skill via `--recommend` and detect a stack mismatch (Vue skill in a React project), surface a one-line `--customize` hint instead of just suggesting "install it" — that's the moment this feature pays off.

### Nothing is permanently dropped: the `_archive/` scaffold (v4.6+)

`--customize` doesn't *delete* sections that don't fit — it **archives** them. Every fork written by `--customize` also gets:

- `<fork>/_archive/SKILL.original.md` — the source SKILL.md verbatim, so the agent always has a faithful copy to diff against
- `<fork>/_archive/dropped.json` — every section of the source preserved as JSON, with its original content, its action at customize time (`drop-or-rewrite`, `rewrite-stack`, `keep-trim`, etc.), the stack/framework keywords it mentions, and the project signals that were in effect when the call ran

This means dropped functionality is recoverable. A fork written when the project was "React + FastAPI" can be patched later when Vue is added — without re-customizing from scratch and without the agent having to re-derive what was originally there.

### `--restore <fork-id>`: patch dropped functionality back in

```bash
python registry.py --restore <fork-id>          # preview: which archived sections now fit?
python registry.py --restore <fork-id> --apply  # splice them back into the fork's SKILL.md
```

`--restore` re-scans the project for its **current** signals, re-scores every archived section against them, and surfaces the ones whose relevance has grown. Typical trigger: the project added a stack the original `--customize` call had no signal for.

Run `--restore <fork-id>` proactively after a meaningful project shift (new framework added, CLAUDE.md rewritten) on any fork that lives at `~/.claude/skills/<id>-for-<project>`. Output is silent when nothing has changed — running it is cheap.

With `--apply`, the patch candidates are appended to the fork's SKILL.md under a `## Restored from archive (<date>)` banner. The agent then integrates them into the right places and removes the banner. Engine produces the patch, agent does the prose — same split as `--customize` itself.

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
| Installing with `npx skills add ... -g -y` (global, no confirmation) | Never. Install at project scope and let the user confirm; scan first |
| Reading `references/commands.md` by hand to list flags | Run the engine (`--platforms --verbose`, etc.) — it renders consistently |

---

## Other commands and tier choice

Full CLI reference: `references/commands.md` (covers `--check`, `--list`, `--discover`/`--find`, `--health`, `--stale`, `--platforms`, `--migrate`, `--author`, `--customize`, `--sync`/`--push`, `--validate`).

**Tier choice:** `skills-curator-lite` is the default — same intelligence layer, no Python (Bash/Read/Glob/Grep + embedded catalogs). Use the Python version when you have 100+ skills (single-pass speed beats N agent steps), need cross-device Gist sync, or want regression-tested behavior. Both ship in the plugin and use different registry paths — they don't conflict.
