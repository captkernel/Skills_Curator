---
name: skills-curator-lite
description: >
  The intelligence layer for Claude skills — without Python. Finds skills
  (curated trust-rated catalog + skills.sh search + live GitHub topics),
  identifies what fits your project (stack, deps, CLAUDE.md), ranks by relevance,
  project fit, trust and popularity, recommends with pros/cons and per-project
  customization advice, persists every decision, and migrates across 55
  supported agent platforms. Same model as the full version, no engine — the
  agent does the work via Bash, Read, Glob, Grep, Write.
  Use when the user mentions a skill, asks "how do I do X" (where a skill might
  help), "find a skill for X", "is there a skill that…", "should I install X",
  asks to evaluate / recommend / audit / check a skill, asks "what skills fit
  this project", asks for a list of supported platforms, or wants to migrate
  skills to another agent. Choose this over the full version when you don't
  have Python, want zero dependencies, or prefer transparent agent reasoning.
metadata:
  version: "2.0.0"
  author: captkernel
  homepage: https://github.com/captkernel/Skills_Curator
  license: MIT
  derived_from: skills-curator
when_to_use:
  - User mentions a new skill, plugin, or tool by name
  - User asks "how do I do X", "find a skill for X", or "is there a skill that…"
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

**The intelligence layer for Claude skills — without Python.**

Evaluate before installing, persist your decisions, recommend by project fit, migrate across agent platforms, and **CUSTOMIZE** (the headline capability): fork any external skill into a project-tailored version with examples rewritten for the user's real stack. The agent does the work directly with Bash, Read, Glob, Grep, Write. Full Python version: [Skills Curator](https://github.com/captkernel/Skills_Curator).

**Choose Lite when** Python isn't available, you want zero dependencies, or want readable agent reasoning. **Choose the full version when** you have 100+ skills, want regression-tested code, or need Gist sync.

**Privacy:** no query telemetry. Searches go straight from this machine to skills.sh / GitHub; nothing is sent to the author. Say this briefly the first time you search.

## First activation in a session

Open once with this orientation before answering (skip it if proactive activation is about to surface concrete picks; never repeat):

> 🧭 *Skills Curator Lite loaded — your intelligence layer for Claude skills (Python-free).*
> *I search a trust-rated catalog plus skills.sh, rank by your project, and persist every decision. Working on your request now.*

## Verbs

| Say | Verb | Section |
|---|---|---|
| "find a skill for X", "is there a skill that…", "how do I do X with a skill" | **CURATE** (fast) | below |
| "what skills fit this project", "recommend" | **RECOMMEND** | below |
| "should I install X", "is X safe", "evaluate X" | **EVALUATE** | below |
| "audit my skills", duplicates, stale | **AUDIT** | below |
| "where can I install", "list platforms" | **PLATFORMS** | below |
| "copy my skills to Cursor/Codex…" | **MIGRATE** | below |
| "tailor X to my stack", stack-mismatch pick | **CUSTOMIZE** | references/customize.md |

## Reference files (load on demand, not up front)

| File | Load when |
|---|---|
| `references/catalog.yaml` | any search/recommend: the curated seed catalog (pros/cons, trust, install) |
| `references/signals.md` | scanning a project: Framework + Goal signals, Tag rivals, Symptom to skill map |
| `references/security-patterns.md` | scanning a skill before install/evaluate (regex table + grep example) |
| `references/persistence.md` | reading/writing registry.json, auto_state.json, `--refresh`, MIGRATE, platform detection |
| `references/platforms.md` | PLATFORMS / MIGRATE: all 55 platforms with dirs and detection paths |
| `references/customize.md` | CUSTOMIZE: fork procedure and customization-plan template |
| `references/templates.md` | rendering result rows, the EVALUATE output format, audit line |

## Search sources (used by CURATE and RECOMMEND)

1. **Curated catalog** — `references/catalog.yaml` (or fresh `~/.claude/skills/skills-curator-lite/catalog.json`, mtime < 24h). Has pros/cons.
2. **skills.sh search** (live):
   ```bash
   curl -s --max-time 5 "https://skills.sh/api/search?q=<urlencoded query>&limit=20"
   ```
   Returns `{"skills":[{"id":"owner/repo/skill","source":"owner/repo","skillId":"skill","name":"...","installs":N}]}`. Install string: `npx skills add <source> --skill <skillId>` (fallback to `name` if `skillId` is missing). Link: `https://skills.sh/<source>/<skillId>`. Dedupe on full `id`. On error/timeout, continue with the other sources and say skills.sh was unreachable.
3. **GitHub topic search** — `claude-skill`, `claude-code-skill`, `agent-skill` (details in `references/persistence.md`, only on `--refresh` or "latest skills").

**Merge:** dedupe by `id` (also match on `source`+name). On collision the **curated entry wins** (keep its pros/cons, tags, trust). Auto-discovered entries have empty pros/cons and trust from author (official/high/medium/community; `unknown` otherwise).

## Blended ranking

Compute per candidate:

```
score = 0.35*relevance + 0.30*fit + 0.20*trust + 0.15*popularity
```

- **relevance** 0..1: how well name/description/tags match the query (1.0 when there is no query, e.g. RECOMMEND). Per query term: name/id match 1.0, tag 0.8, description 0.6; average over terms.
- **fit** 0..1: overlap of the skill's tags with the project tag set (from `references/signals.md`), 3 matches = 1.0; 0 if no project is detected. With a query, use fit × relevance so a weak match can't win on fit alone.
- **trust**: official 1.0 · high .8 · medium .6 · community .4 · unknown .2
- **popularity** = `min(1, log10(installs+1)/6)`; 0 when installs unknown.
- Registry check (`registry.json`): verdict **SKIP** for this project → score ×0.3 and label `(previously rejected)`; already installed or **ADOPT**ed → **exclude from CURATE**.
- Each result gets a one-line why: `why: fit .8 (react, nextjs) · trust high · 185K installs`.
- Stack mismatch (Tag rivals in signals.md) → append the `--customize` hint.

Render rows per `references/templates.md`.

## CURATE — fast path

Trigger: "find a skill for X", "is there a skill that…", "how do I do X with a skill".

1. Turn the request into 2-4 keywords; run **one** pass: skills.sh search + curated catalog match (no GitHub refresh, no project deep-scan; read the registry only to drop installed/ADOPT and penalise SKIP).
2. Rank with the blend above. If a project is obvious from cwd (package.json etc.) use it for fit; otherwise fit = 0.
3. Show **top 5**: name, why-line, install command, link when known. No pros/cons or full evaluation. If `find-skills` itself is a result, label it "overlaps Skills Curator".
4. End with: "Want a full EVALUATE on any of these?" Install only after the user picks, via Safe install below.

If nothing matches, say so plainly and suggest rephrasing; don't invent skills.

## RECOMMEND — what fits this project?

1. **Scan signals.** `ls package.json requirements.txt pyproject.toml Pipfile go.mod Cargo.toml CLAUDE.md README.md 2>/dev/null`, Read each present file. Convert via Framework Signals; Read CLAUDE.md/README.md and convert via Goal Signals (`references/signals.md`).
2. **Tag set** = languages ∪ framework matches ∪ goal matches.
3. **Candidates** = curated catalog + skills.sh search on the top 2-3 tags + cached catalog.json; skip skills already in the registry (installed/ADOPT).
4. **Rank** with the blend; show top 5, grouped **⚡ CAPABILITY** vs **🎨 PREFERENCE**.
5. **Render** with up to 2 pros and 2 cons from curated entries, the why-line, and a `--customize` hint on stack mismatch.

## EVALUATE — should I install this skill?

1. **Registry first.** Read `registry.json`; if the skill id exists, surface the prior verdict + summary instead of re-evaluating.
2. **Fetch and scan.** Get the skill's SKILL.md and scripts (local folder, or curl raw GitHub). Scan with `references/security-patterns.md`. Any HIGH/CRITICAL: stop and report.
3. **Ground in the project:** Read CLAUDE.md.
4. **Audits (advisory, optional).** For a public GitHub source, one request:
   ```bash
   curl -s --max-time 4 "https://www.skills.sh/tele/audit?source=<owner/repo>&skills=<skillId>"
   ```
   Response: `{"<skillId>":{"ath":{"risk":..},"socket":{"alerts":N},"snyk":{"risk":..}}}` (ath = Gen; risk in safe/low/medium/high/critical/unknown). Show as one line (templates.md). Missing, empty, or failed = say nothing; **never block on it**. Skip for private/unknown repos (this sends the repo and skill name to skills.sh).
5. **Produce the evaluation** in the exact format in `references/templates.md`, verdict ADOPT | PARTIAL | SKIP.
6. **Persist** the decision: append to the skill's `evaluations[]` in registry.json (`references/persistence.md`).
7. **Rival check.** If vercel-labs `find-skills` is installed (`ls ~/.claude/skills/find-skills .claude/skills/find-skills 2>/dev/null`, or in the registry), tell the user Lite overlaps with it and offer to keep one.

## Safe install

When the user decides to install:

- Always **project-scope**: `npx skills add <source> --skill <skillId>` run from the project root. **Never suggest `-g` or `-y`** (global scope / skipping prompts); the user should see each prompt.
- Before installing, scan the skill's SKILL.md and all scripts with the security patterns; report findings and stop on HIGH/CRITICAL.
- Then record the decision in the registry.

## AUDIT — review my whole stack

One pass, five checks, then a triaged punch list (most critical first):

1. **Duplicates:** registered skills with tag overlap > 60%.
2. **Preference conflicts:** `type: preference` skills with contradictory rules.
3. **Security gaps:** skills with missing/empty `security_scan` — recommend EVALUATE.
4. **Stale evaluations:** last evaluated > 6 months ago.
5. If vercel-labs `find-skills` is installed alongside Lite, flag the overlap.

## PLATFORMS

Run detection (`references/persistence.md` for the loop and render format; all 55 entries in `references/platforms.md`). Render "Detected n of 55" with detected platforms; list all rows only if asked.

## MIGRATE

Default source `~/.claude/skills/`. Confirm targets (named platforms validated against `references/platforms.md`; "all detected" = run detection, exclude claude-code). Copy each skill folder to the target dir, skipping existing destinations (never clobber). Script in `references/persistence.md`. Primary first-class: `claude-code`, `github-copilot`; the other 53 via the same flow.

## CUSTOMIZE

Fork an external skill into `~/.claude/skills/<name>-for-<project>/SKILL.md`: scan source (security), scan project, split source on `## `, assign keep / keep-trim / rewrite-stack / drop-or-rewrite per section, write a customization-plan table, then rewrite. Full procedure and template: `references/customize.md`.

## Proactive activation (the intelligence layer)

Surface relevant skills unprompted, quietly, when project context implies one would help.

**Once per session, silently,** if cwd has `CLAUDE.md`, `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, or `Cargo.toml`:

1. Fingerprint: `wc -c` byte counts + first 200 chars of each existing file, concatenated.
2. Read `~/.claude/skills/skills-curator-lite/auto_state.json` (init `{}` if missing; shape in `references/persistence.md`).
3. Same fingerprint stored for this project path: say nothing.
4. Otherwise: run RECOMMEND silently, store top 3 + new fingerprint, and weave them into your first reply as a quiet observation, e.g. *"I noticed you're using Next.js + Tailwind. There's a `frontend-design` skill (🏛️ official) that fits. Want me to evaluate it?"*

Re-run the fingerprint check when the user adds/removes a dependency, edits CLAUDE.md, or installs a framework.

**Symptoms:** when the user describes a pain ("my tests are slow", "deploys are manual", "the UI looks ugly"), match the Symptom to skill table in `references/signals.md`, then run CURATE on those tags.

**Don't over-trigger:** at most once per session unless the project changes; only on clear pain points; if nothing is strong (low overlap/trust), say nothing — silence is valid.

## When to recommend the full Skills Curator

Lite matches the Python version's judgment model (v4.7). The full version still wins on speed with 100+ skills (one Python pass vs N agent steps), regression tests (58 pytest cases), and cross-device Gist sync. If Python 3.10+ is available and one matters:

```bash
/plugin marketplace add captkernel/plugins
/plugin install skills-curator@captkernel   # ships Lite and the Python tier together
npx skills add captkernel/Skills_Curator    # alternative: adds the Python tier if Python 3.10+ is found
# (the claude.ai edition is a separate download, not part of the plugin)
```

The two don't conflict; install both if you like (different registry paths).

## Why Lite is the default

The Python engine is fast and tested but is a barrier for users without Python 3.10+. Lite proves the same model works as pure prompt engineering: the agent reads the spec, reasons about the project, writes the registry, and runs the security checks. Slower per call, zero install. For a tool whose pitch is judgment, an agent-driven implementation is philosophically consistent.
