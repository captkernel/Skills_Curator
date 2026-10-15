# Skills Curator, distribution kit

Copy-paste ready, posted from the captKernel accounts (handle `@captkernel`). Repo is public (MIT). Voice is founder-to-builders: direct, lowercase-leaning, honest about the rough edges, and it ends on a real question. No em dashes. The install line is prominent in every post. Reddit, LinkedIn and Show HN posts open with the problem and put the Install and Repo lines at the end of the body (on Reddit because self-promotion filters on newer accounts tend to remove posts that lead with an install command). When and where to post: the launch checklist in the Claunchpad repo, `docs/launch/CHECKLIST.md` (Launch 1): https://github.com/captkernel/Claunchpad/blob/master/docs/launch/CHECKLIST.md

**The links**
```
Install:      /plugin marketplace add captkernel/plugins
              /plugin install skills-curator@captkernel
Repo:         https://github.com/captkernel/Skills_Curator
Reel:         https://github.com/captkernel/Skills_Curator/raw/main/docs/video/skills-curator-reel.mp4
              (4:5 feed cut: https://github.com/captkernel/Skills_Curator/raw/main/docs/video/skills-curator-reel-4x5.mp4)
How it works: https://htmlpreview.github.io/?https://github.com/captkernel/Skills_Curator/blob/main/docs/how-it-works.html
Token report: https://htmlpreview.github.io/?https://github.com/captkernel/Skills_Curator/blob/main/docs/token-cost-report.html
Other:        npx skills add captkernel/Skills_Curator, or the claude.ai zip (dist/skills-curator-claudeai.zip)
```

**Headline facts** (every figure here is from `README.md` or `docs/token-cost-analysis.md`; don't add numbers from anywhere else; the install-count scraping removal is from `CHANGELOG.md` (v4.0 "Removed") and `docs/reference.md` ("Why no install counts?")): a skill that handles judgment about other skills. It reads your project (stack, dependencies, CLAUDE.md) and recommends what fits, evaluates a skill before you install it (pros, cons, conflicts, verdict), runs a pre-install security scan (15 risk patterns), and saves every decision to a local registry, so re-asking about a skill costs about 13 tokens instead of about 4,060. `--customize` splits an external SKILL.md into sections, scores each against your project, and writes a fork that keeps what fits and rewrites mismatched examples in your stack. Token cost is measured, not estimated: 249 tokens always-on per session, at most 1,140 tokens per command, flat from an empty folder to a 17,680-file project. Catalog of 19 curated entries plus live GitHub topic search. Migrates skills across 55 agent platforms. Three editions (Lite with no Python, Python, claude.ai). v4.6.2, 37 tests, MIT.

**Narrative beats to lean on:**
1. Skill tools wait for you to ask. You don't know what exists until you go searching, and six months later you're re-evaluating a skill you already decided about.
2. Every skill you bolt on imports its author's voice. Stack five and your project speaks in five accents. Infuse, don't invoke.
3. Decide once. The verdict persists, so the second ask is ~13 tokens, not a fresh evaluation.
4. Cheap by construction: the engine reads your files in a subprocess, so project size doesn't move the token cost.
5. Honest by policy: no scraped install counts, a security scanner that would rather flag a benign `eval()` than miss something.

**Rough edges to be upfront about** (from the same sources):
- Token counts were measured with `tiktoken` (`cl100k_base`), not Anthropic's tokenizer; the analysis puts that within ~5 to 10% of what Claude sees.
- The Lite edition's SKILL.md body is 10,988 tokens when it activates (Python tier: 3,359). The 249-token figure is the always-on cost, not the activated cost.
- `--customize` writes the plan; the agent does the rewriting, so the fork is only as good as that rewrite.
- The `--check` scanner is deliberately conservative and will flag benign code. Review, don't panic.

**Assets:**
- Launch reel, 32s: `../../video/skills-curator-reel.mp4` (9:16) and `../../video/skills-curator-reel-4x5.mp4` (4:5), poster `../../video/skills-curator-poster.jpg`.
- Interactive walkthrough: `../../how-it-works.html`. Token cost report: `../../token-cost-report.html`.
- Screenshots for posts: `../../images/screenshot-claude-session.png`, `../../images/screenshot-customize.png`.

---

## 1. Reddit, r/ClaudeAI

Angle: the problem with how skills get adopted (author's voice, re-deciding, not knowing what exists) and the `--customize` idea. Broad audience, so less terminal detail.

**Title:**
```
Every skill you install brings its author's stack with it, so I built something that rewrites skills for yours
```

**Body:**
```markdown
The problem with skills: the tools for them (`npx skills`, `asm`, find-skills) are plumbing. Install, list, sync. They wait for you to ask, and they assume you already know what to look for. Three problems follow:

- You don't know what skills exist until you go searching.
- Six months later you're re-evaluating a skill you already decided about.
- Every skill you add brings its author's voice with it: their examples, their stack, their assumptions. Five external skills and a project speaks in five accents.

(I built this, MIT; links at the bottom.) Skills Curator is my attempt at the judgment layer on top of that plumbing:

**It reads what you're building and recommends.** Stack, dependencies, CLAUDE.md. Ask "what skills fit this project?" and you get a ranked list with pros, cons and install commands. In `--auto` mode it re-runs recommendations only when your project's key files change.

**It evaluates before you install, and remembers.** "Should I install X?" gets a verdict (ADOPT / PARTIAL / SKIP) with evidence and a pre-install security scan (15 risk patterns). The verdict is saved to a local registry, so asking again later costs about 13 tokens instead of about 4,060.

**`--customize`: infuse, don't invoke.** Instead of installing a skill as-is, it splits the SKILL.md into sections, scores each against your project, and writes a fork: keep what fits, rewrite stack-mismatched examples in your stack, drop the rest. Vue snippets become React snippets. The capability transfers; the author's accent doesn't.

What I learned building it: the hard part isn't recommending, it's being honest. I took out install-count scraping because it was brittle and popularity isn't fit. The security scanner is conservative on purpose and will flag benign code. And `--customize` produces the plan; the agent does the rewriting, so the result depends on that rewrite.

It's MIT, runs on Claude Code (a Lite edition with no Python, plus an optional Python tier) and has a separate claude.ai edition. The 32s reel is linked in the README.

How do you decide whether to add a skill today, and have you ever kept one you'd rather have half of?

**Install (Claude Code):** `/plugin marketplace add captkernel/plugins` then `/plugin install skills-curator@captkernel`
**Repo:** https://github.com/captkernel/Skills_Curator
```

**Time to post:** the day after r/ClaudeCode (see the checklist). Reply to every comment.

---

## 2. Reddit, r/ClaudeCode

Angle: the engineering, specifically how it keeps token cost flat regardless of project size, with the measurements. This audience runs Claude Code daily and cares about context budget. Not a copy of the r/ClaudeAI post.

**Title:**
```
An always-on skill's context cost doesn't have to grow with project size: measured 249 tokens from 1 to 17,680 files, and here's why it stays flat
```

**Body:**
```markdown
The obvious question for any always-on skill is what it costs in context, and the honest answer shouldn't be a guess. (I built this one, Skills Curator, MIT; links at the bottom.) It evaluates, recommends and customizes other skills, and I measured it with `tiktoken` against 5 real projects, from 1 file to 17,680 files, plus every CLI verb in both tiers.

What came out:

- **Always-on cost: 249 tokens per session.** That's the frontmatter description, the only thing loaded until the skill activates.
- **Per command: at most 1,140 tokens of stdout** (on a 48-file repo). The 17,680-file Next.js project maxed at 965.
- **Project size has no measurable effect.** 10 verbs are constant across all projects; the other 14 vary by about 200 tokens or less, driven by catalog match count, not file count.
- **Heavy session, 7 skill interactions:** 8,382 tokens with it vs 28,420 doing the same evaluations ad hoc. That's 20,038 tokens saved (71%), mostly because verdicts persist.

How it stays flat:

- **The engine runs as a subprocess.** The Python tier is one stdlib-only script, `registry.py`. Claude only sees its stdout, so ~27,900 tokens of source cost 0 tokens of context.
- **Inputs are capped.** The project scan reads CLAUDE.md, README.md and dependency manifests, and truncates doc reads to 4,000 chars. File contents are never emitted; `rglob` only counts extensions for language detection.
- **Output is capped.** Catalog matches are deduplicated and limited to 8 by default.
- **Persistence.** Re-asking about an evaluated skill (`--history`) is about 13 tokens vs about 4,060 re-evaluating from scratch.

Rough edges, honestly: `tiktoken` `cl100k_base` is an approximation of Anthropic's tokenizer (the analysis puts it within ~5 to 10%). And the Lite edition, the no-Python default, has a 10,988-token SKILL.md body when it activates, against 3,359 for the Python tier. Lite trades context for zero dependencies. The audit scripts are in the repo (`docs/audit/`) if you want to rerun it on your own codebases.

What do you budget for always-on skill cost, and does anyone else measure it, or is it vibes?

**Install:** `/plugin marketplace add captkernel/plugins` then `/plugin install skills-curator@captkernel`
**Repo:** https://github.com/captkernel/Skills_Curator
```

**Time to post:** Launch 1 day, after X and LinkedIn (see the checklist). Reply to every comment.

---

## 3. Hacker News, Show HN

**Title** (≤ 80 chars):
```
Show HN: Skills Curator, evaluate Claude Code skills and fork them to your stack
```
**URL:** `https://github.com/captkernel/Skills_Curator`

**First comment** (post it right after submitting; with a URL set, HN shows no body text):
```
I built this because the tools for Claude skills (npx skills and similar) handle install and sync, but not the judgment: does this skill fit my project, is it safe, and did I already decide about it?

What it does:
- Reads the project (stack, dependencies, CLAUDE.md) and recommends skills from a catalog of 19 curated entries plus live GitHub topic search.
- Evaluates a skill before install: pros, cons, conflicts, a verdict, and a pre-install scan for 15 risk patterns. The result is saved to a local JSON registry, so a repeat question is about 13 tokens instead of about 4,060.
- --customize splits an external SKILL.md into sections, scores each against the project fingerprint, tags an action (keep-emphasize, keep-trim, rewrite-stack, drop-or-rewrite, rewrite-frontmatter) and writes a fork at ~/.claude/skills/<name>-for-<project>/. The agent then rewrites the mismatched sections in the project's stack.
- Migrates skills across 55 agent platforms.

How it works: the Python tier is a single stdlib-only script run as a subprocess, so Claude sees only its stdout. Project scans read a few known files and truncate docs to 4,000 chars. Measured with tiktoken across 5 projects up to 17,680 files: 249 tokens always-on, at most 1,140 per command, no measurable effect from project size. There's also a Lite edition with no Python (the agent does the work with Bash, Read, Grep and curl) and a claude.ai edition.

What's rough: token counts use tiktoken cl100k_base, an approximation of Anthropic's tokenizer. Lite's SKILL.md body is 10,988 tokens when it activates. The security scanner is conservative and flags benign code. The fork is a plan plus an agent rewrite, so its quality depends on the model.

Network: GET requests to GitHub only (topic search, SKILL.md fetches when customizing a remote skill). Gist sync of the registry is opt-in. MIT.

Install in Claude Code: /plugin marketplace add captkernel/plugins, then /plugin install skills-curator@captkernel

What would make you trust a pre-install verdict on a third-party skill: the scan rules, the evidence, or something else?
```

---

## 4. X / Twitter thread

**1 (hook), attach the 32s reel:**
```
every Claude skill you install brings its author's voice with it

their examples, their stack, their assumptions. stack five and your project speaks in five accents

so i built Skills Curator: it decides what fits your project, then rewrites skills in your stack instead of installing them as-is
```
**2 (the problem):**
```
skill tools wait for you to ask

you don't know what exists until you go searching, and six months later you're re-evaluating a skill you already decided about

the missing piece wasn't install. it was judgment that sticks
```
**3 (--customize), attach the customize screenshot:**
```
--customize splits a SKILL.md into sections, scores each one against your project, and writes a fork

keep what fits, rewrite mismatched examples in your stack, drop the rest

Vue snippets become React snippets. the capability transfers, the accent doesn't
```
**4 (decide once):**
```
every evaluation is saved: pros, cons, conflicts, verdict, plus a pre-install security scan

asking about the same skill again costs ~13 tokens instead of ~4,060

decide once, never re-decide
```
**5 (token cost):**
```
measured, not estimated

249 tokens always-on per session, at most 1,140 per command, flat from an empty folder to a 17,680-file project

the engine reads your files in a subprocess, so project size doesn't touch your context
```
**6 (close):**
```
/plugin marketplace add captkernel/plugins
/plugin install skills-curator@captkernel

github.com/captkernel/Skills_Curator

open source, MIT

how do you decide whether a skill is worth adding?
```
Tag `@AnthropicAI` on tweet 1.

---

## 5. LinkedIn post

```
Every Claude skill you install comes with its author's voice.

Their examples. Their stack. Their assumptions. Add five external skills and your project ends up speaking in five accents. And the tools for managing skills mostly handle the plumbing: install, list, sync. They wait for you to know what to ask for.

The gap isn't installing skills. It's judgment. Does this one fit my project? Is it safe? Didn't I already decide about it six months ago?

So I built Skills Curator, an open-source skill for Claude Code that handles that judgment:

• It reads your project (stack, dependencies, CLAUDE.md) and recommends what fits, with pros and cons.
• It evaluates a skill before you install it, including a pre-install security scan, and saves the verdict. Asking again later costs about 13 tokens instead of about 4,060.
• Its --customize command splits a skill into sections, scores each against your project, and writes a fork that keeps what fits and rewrites the rest in your stack. The capability transfers; the author's accent doesn't.

I also measured what it costs, rather than guessing: 249 tokens always-on per session, at most 1,140 per command, flat from an empty folder to a 17,680-file project.

It isn't perfect. The security scanner is deliberately conservative and flags benign code, and a fork is only as good as the rewrite the agent does. I'd rather say that upfront.

It's MIT. Repo, install command and a 32-second reel in the comments.

If you use Claude skills: how do you decide which ones earn a place in your project?
```

First comment (drop the links here, not in the post body, for reach):
```
Install in Claude Code: /plugin marketplace add captkernel/plugins, then /plugin install skills-curator@captkernel
Repo: https://github.com/captkernel/Skills_Curator
32s reel: https://github.com/captkernel/Skills_Curator/raw/main/docs/video/skills-curator-reel.mp4
How it works: https://htmlpreview.github.io/?https://github.com/captkernel/Skills_Curator/blob/main/docs/how-it-works.html
```

---

## 6. Instagram caption (for the 32s reel)

Post the 9:16 reel (`docs/video/skills-curator-reel.mp4`) as a Reel, or the 4:5 cut as a feed post.

```
Every Claude skill you install brings its author's voice with it.

So I built Skills Curator: one skill for Claude Code that decides which skills fit your project, then rewrites them in your stack instead of installing them as-is.

→ Recommends what fits your project, with pros and cons
→ Evaluates and security-scans a skill before you install it
→ Remembers every verdict, so you decide once
→ --customize: keep what fits, rewrite the rest (infuse, don't invoke)

249 tokens always-on. Free and open source (MIT).

Link in bio, or search "Skills Curator" on GitHub.

Save this for the next time you're about to install a skill. How do you decide which ones are worth adding?

.
.
#claudecode #anthropic #claude #aitools #aiagents #buildinpublic #devtools #opensource #vibecoding #softwareengineering #promptengineering #indiehacker
```

---

## 7. Posting order

The order, timing and accounts live in the checklist (Launch 1): X, then LinkedIn, then r/ClaudeCode, r/ClaudeAI the next day, Show HN Tue to Thu 8 to 10am US ET, Instagram the same day as HN. Tag @AnthropicAI on tweet 1, put LinkedIn links in the first comment, and stay around for the first 90 minutes of the HN post.

Stagger by a few hours, don't fire everything in one window. Lead with honesty about the rough edges, that's what reads as real.
