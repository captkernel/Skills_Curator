# Changelog

All notable changes to Skills Curator. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.6.0] — 2026-05-18

`--customize` now scaffolds an archive of every section of the source SKILL.md so dropped/trimmed functionality stays recoverable. A new `--restore <fork-id>` command re-evaluates that archive against the project's *current* signals and surfaces (or splices back) any sections whose relevance has grown — e.g. a Vue section dropped from a React-only fork can be patched back when Vue is added to the project, without re-customizing from scratch.

### Added

- **`--customize` archive scaffold** — every fork now also gets `<fork>/_archive/SKILL.original.md` (verbatim source) and `<fork>/_archive/dropped.json` (every section with its original content, the action taken at customize time, the stack/framework keywords it mentions, and a snapshot of the project signals in effect). Schema: `customize-archive/1.0`. Format is intentionally simple so power users and other tools can read it without the engine.
- **`--restore FORK_ID`** — re-scans the project for current signals, re-scores every archived section against them, and lists patch candidates (sections whose relevance has grown, or whose original stack is now in the project). Preview-only by default.
- **`--restore FORK_ID --apply`** — splices the patch candidates into the fork's SKILL.md under a dated `## Restored from archive` banner. Engine produces the patch; the agent then integrates it into the proper place and removes the banner (same split as `--customize`).
- **`_extract_section_stack_signals` / `_STACK_KEYWORDS`** — internal helper + vocabulary that recognizes ~60 framework/language/infra keywords in section prose so the archive knows *what stack each section was for*. Aligned with the tag/language vocabulary `_scan_project` produces.

### Changed

- **Plugin version 4.5.0 → 4.6.0** in `plugin.json`, `registry.py VERSION` constant, and the Python tier's `SKILL.md` metadata. Lite tier and claude.ai edition are unchanged in this release.
- **SKILL.md `--customize` section** now documents the `_archive/` scaffold and the `--restore` companion.
- **`references/commands.md`** authoring table updated to list `--customize` and `--restore`.

### Notes

- Forks created before 4.6.0 have no `_archive/`; running `--restore` on them prints a friendly note suggesting a re-run of `--customize` to regenerate the archive. The behavior is non-destructive.
- The archive deliberately preserves *all* sections (not just the dropped ones) so future re-analysis has the original full context, but only sections originally marked `drop-or-rewrite`, `rewrite-stack`, or `keep-trim` are flagged `restorable: true`.

## [4.5.0] — 2026-05-14

Third edition. Skills Curator now ships for **claude.ai (web + desktop)** in addition to the two existing Claude Code editions (Lite and Python full). Same judgment model, same registry schema — re-architected for a runtime that has no persistent `~/.claude/` filesystem and no slash commands. The Claude Code editions are unchanged in behavior; this is purely additive.

### Added

- **`skills/skills-curator-claudeai/`** — new edition bundle for the claude.ai Skills feature. Slim `SKILL.md` (~250 lines) with progressive disclosure to four reference files. Designed to be zipped and uploaded via claude.ai → Settings → Capabilities → Skills.
- **`skills/skills-curator-claudeai/references/catalog.yaml`** — 20-entry curated catalog, mirrored from the Lite edition's embedded YAML. Loaded on demand during RECOMMEND to keep activation cost low.
- **`skills/skills-curator-claudeai/references/signals.md`** — framework + goal signal extraction tables and the Tag-rivals stack-mismatch detector. Loaded on demand during RECOMMEND and CUSTOMIZE.
- **`skills/skills-curator-claudeai/references/security-patterns.md`** — 15 severity-tagged regex patterns for pre-install scanning. Loaded on demand during EVALUATE and SCAN.
- **`skills/skills-curator-claudeai/references/persistence.md`** — deep dive on the three persistence modes (Project Knowledge / upload / Gist sync), schema field-by-field, migration rules, troubleshooting.
- **`skills/skills-curator-claudeai/INSTALL.md`** — end-user install guide: prerequisites, zip command (PowerShell + bash), upload steps, Project Knowledge setup for Mode A persistence, verification check.
- **New verb on the claude.ai edition: `SCAN`** — lightweight quick-scan that runs only the security patterns and returns a findings table, no full ADOPT/PARTIAL/SKIP verdict. Use when the user just wants a safety check without adoption advice.
- **`/mnt/user-data/outputs/` persistence flow** — the claude.ai edition writes the updated registry to a downloadable file rather than pasting it back into chat. Eliminates the context-cost problem registries would otherwise cause.
- **`CUSTOMIZE` outputs a zip** — on the claude.ai edition, the headline `CUSTOMIZE` verb packages the fork as `/mnt/user-data/outputs/<fork-name>.zip` so the user can upload it back to claude.ai (or move to `~/.claude/skills/` if they're also on Claude Code) in one step.
- **README "Editions" section** replacing the old "Two tiers" section. Three-column comparison covering runtime, engine, install, persistence, verbs supported, and tradeoffs. Old "Two tiers" anchor preserved as a redirect via the new heading.

### Changed

- **Plugin description** in `.claude-plugin/plugin.json` updated to describe three editions, not two. New `claude-ai` keyword added.
- **Plugin version 4.4.5 → 4.5.0** in `plugin.json`, `registry.py VERSION` constant, and the Python tier's `SKILL.md` metadata. Lite tier's internal version (`2.0.0`) is unchanged — Lite tracks separately and didn't change in this release.
- **README header status line** rewritten to mention the third edition. Editions badge replaces the old Tiers badge.

### Notes

- The claude.ai edition is **not** auto-installed by `npx skills add captkernel/Skills_Curator` — that command installs the Claude Code editions to `~/.claude/skills/`. The claude.ai edition lives in the repo at `skills/skills-curator-claudeai/` and is installed via the standalone zip + upload flow documented in its `INSTALL.md`. Adding it to `plugin.json`'s `skills[]` array would incorrectly drop the claude.ai variant into Claude Code installations.
- **Registry JSON schema is shared** across all three editions (`v3.0`). A registry written by one edition can be read by another. Power users can use Gist sync (the Python tier's existing `--sync` feature, or the claude.ai edition's Mode C) to roam a single registry across all three runtimes.
- claude.ai isn't one of the engine's 55 supported platforms — those are all CLI/IDE agents. `--migrate` does not produce a claude.ai-compatible bundle. This was a manual port informed by claude.ai's runtime constraints (sandbox-per-conversation, no `~/.claude/`, no slash commands, Project Knowledge as the only durable storage Claude can read on its own).
- No engine code changed. All 37 pytest cases continue to pass.

## [4.4.5] — 2026-05-13

USP repositioning + empirical token-cost docs. `--customize` is now the headline capability in both SKILL.md files; the intelligence-layer messaging is reframed as the activation model that surfaces the right skill, not the USP itself. New reproducible token-cost audit ships in `docs/audit/`, with two self-contained HTML reports for transparency. No engine or CLI behavior changes.

### Added
- **`docs/token-cost-report.html`** — empirical token-cost measurements across 5 real projects (1 file → 17,680 files), every CLI command, both tiers. Single-file HTML with inline CSS and SVG charts. Demonstrates that engine output is bounded regardless of project size (the engine reads project files in a Python subprocess; only stdout enters Claude's context).
- **`docs/how-it-works.html`** — feature-by-feature walkthrough with architecture diagram, glossary (command/verb, tier, subprocess vs agent), and honest per-command token accounting. Includes the 17 symptom patterns, 15 security patterns, and 31 framework signals, rendered from source. Cross-linked with the token-cost report.
- **`docs/token-cost-analysis.md`** — concise markdown summary of the audit findings for readers who don't want HTML.
- **`docs/audit/`** — reproducibility scripts: `deep_token_audit.py` (runs every CLI command against configurable test projects, counts stdout tokens with `tiktoken`), `generate_html.py` and `generate_walkthrough.py` (emit the two HTML reports), plus `audit_results.json` for the committed measurements. Override default projects via `--projects path1,path2,...`.

### Changed
- **`--customize` repositioned as the headline USP in both SKILL.md files.** The Python tier opens with "Install the skill. Customize it to your stack. Decide once, never re-decide." and expands the customize section with a 6-step pipeline breakdown. The Lite tier's "Bonus: CUSTOMIZE" framing is gone — it's now section 6, "the headline capability." The intelligence-layer language stays but is reframed as the activation model. Pressure test of the framing is in the new HTML reports.
- **README rewritten and tightened — 607 → 483 lines.** Adds a side-by-side USP block right after the TL;DR (qualitative `--customize` framing on the left, quantitative token-cost evidence on the right), a new "Token cost" section with hero numbers and links to the HTML reports, and a tightened FAQ that answers the most-missed conceptual question: "if the skill reads my project, doesn't that cost tokens?" Architecture diagram simplified; command reference halved (full reference still in `references/commands.md`).
- **`deploy.py` `FILES_TO_PUSH`** extended with the new `docs/` and `docs/audit/` files so they ship to the public repo.

### Notes
- Token counts use `tiktoken` `cl100k_base` (OpenAI's BPE tokenizer). Anthropic's tokenizer is also BPE with similar vocabulary scale — measured counts are within ~5–10% of what Claude actually sees. External SKILL.md size assumption was validated against 42 real installed `SKILL.md` files: average 11,057 bytes / 2,623 tokens, median 2,280 tokens — within 5% of the audit's 10 KB / 2,560-token reference.
- No engine, CLI, or schema changes. All `pytest tests/` cases continue to pass.

## [4.4.4] — 2026-05-11

README banner removed. The repo now opens with the title + badges (no hero image above the title). Cleaner first impression that matches what most well-designed CLI-tool repos do (HTTPie, DVC, Bun, etc.) — the value-prop tagline carries the opening, with content-rich images (the Claude Code session screenshot, the `--customize` flow) reserved for the Demo and feature sections below.

### Removed
- `docs/images/hero.png` no longer ships in the repo. It was the warm-cream editorial cover; useful as a separate brand asset but unnecessary as a banner. The README opens with the title and badges directly.

### Notes
- `docs/images/` is now six files: `customize-workflow.png` + the five `screenshot-*.png`. Every shipped image is content (a diagram or a real product screenshot), not pure branding.
- The local `.share/images/hero.png` is retained as a social asset (X tweet attachments, LinkedIn share, manual GitHub Settings "Social preview" upload), but it lives only in the local social-launch folder.

## [4.4.3] — 2026-05-11

Image set tightened. README hero reverted to the editorial cover. Every diagram regenerated with real data — no AI-hallucinated platform names, no abstract block diagrams that don't carry information.

### Changed
- **README hero is the editorial cover again** (`docs/images/hero.png`). The Clair Obscur painterly direction lived briefly in v4.4.2 — pulled back in favor of the cleaner brand identity.
- **`docs/images/customize-workflow.png` regenerated as a three-lane diagram.** Source column shows the external skill as authored (6 sections). Plan column scores each section and tags it `keep`, `keep-trim`, `rewrite`, `rewrite-fm`, or `drop` — with `drop` sections visibly struck through and excluded. Final column ("Your Project") contains only the surviving sections; dropped sections are physically absent, with a footer noting their exclusion. Visually proves "infuse, don't invoke" in a single image.

### Removed
- `docs/images/brand-curator-portrait.png` and `docs/images/brand-gallery-hallway.png` — the Clair Obscur brand imagery is no longer in the public repo. README banner uses the editorial cover.

### Notes
- The local `.share/` gallery (not shipped) was also reorganized: engine concept replaced with a live-state dashboard view, cross-agent migration replaced with a real-data platform matrix (55 platforms, organized by tier, every install path shown), decision history replaced with an actual evaluation-record artifact (pros / cons / conflicts / adoption plan). Local gallery at `.share/gallery.html`.

## [4.4.2] — 2026-05-11

Visual identity refresh. No engine or behaviour changes — purely the README, brand imagery, and image manifest.

### Added
- **Clair Obscur brand direction.** Two new oil-painted Belle Époque brand images named after the painterly aesthetic of *Clair Obscur · Expedition 33* — appropriate for a project literally called "Curator." `docs/images/brand-curator-portrait.png` (a bearded curator in a dark coat and burgundy vest examining a small gilded frame, surrounded by floating gilded miniatures) replaces the editorial-cover hero in the README. `docs/images/brand-gallery-hallway.png` (a long museum hallway with salon-style hangings and a single figure at the far end) ships as a secondary banner option.
- **Real product screenshots ship to the repo.** Five styled-HTML terminal/IDE captures (Edge headless): `screenshot-claude-session.png` (the agent activating Skills Curator in a Claude Code chat), `screenshot-customize.png` (real `--customize` per-section plan output), `screenshot-recommend.png`, `screenshot-symptoms.png`, `screenshot-check.png` (split-panel: self-clean scan vs flagged community skill).
- **New modern technical diagrams.** `customize-workflow.png` is now a sleek isometric block diagram on midnight navy (replacing the hand-drawn version). All ship under `docs/images/`.

### Changed
- **README hero is now the Clair Obscur curator portrait** — stronger first impression than the editorial cover, ties the visual identity to the project's naming.
- **`--customize` section in README** now embeds the real terminal screenshot of the per-section decomposition output, replacing the hand-drawn workflow diagram.
- **Demo section in README** opens with the Claude Code session screenshot — proves what the tool does in one image.

### Notes
- Original `hero.png` editorial cover remains in the manifest as an alternate for users who prefer the cleaner brand option.
- `deploy.py` `FILES_TO_PUSH` expanded with the eight new image paths.

## [4.4.1] — 2026-05-11

Quality + dogfooding pass. The biggest fix is that running `--check` on Skills Curator itself no longer returns "DO NOT INSTALL" — the scanner was matching its own pattern definitions. Plus a CSO-compliant frontmatter rewrite, SKILL.md trim, and a small additive `scanner:ignore` mechanism documentation can use to opt out of self-scans.

### Fixed
- **Scanner no longer flags itself.** `cmd_check` against the Python tier returned 6 findings (3 CRITICAL + 2 HIGH + 1 MEDIUM); against Lite, 1 MEDIUM. Both were false positives caused by descriptions like `"eval() — arbitrary code execution risk"` echoing the literal trigger they detect, and by documentation tables that legitimately list patterns. Both tiers now return "✅ No risks detected" on self-scan.
- **`SKILL.md` frontmatter description rewritten** to remove the workflow-summary CSO trap (was: "Maintains a trust-rated catalog… recommends with pros/cons… persists every decision…"). The summary form caused agents to follow the description instead of reading the body. Now strict "Use when…" triggering conditions only. Pressure-tested via subagent: 5/5 true positives, 3/3 true negatives across 8 user prompts.
- **`deploy.py` commit message hardcoded** as "Release v4.0.0 — Skills Curator" since v4.0.0; every push since shipped with a stale title. Now reads the current `VERSION` from `registry.py` and pulls the matching one-paragraph summary from `CHANGELOG.md`. Tag-suggestion next-step also uses the dynamic version.
- **`registry.py` docstring** said "Skills Curator v4.0.0" while `VERSION = "4.4.0"`. Replaced with "see VERSION constant" so it can't drift again.
- **README + CLAUDE.md doc freshness** — test count was 26/35 in different places, engine was "1944 LOC". Now consistent: 37 tests, ~2.3k LOC.

### Added
- **`scanner:ignore` line/block markers.** Lines containing `scanner:ignore` (anywhere in the line) are skipped during `--check`. Blocks bounded by `scanner:ignore-block-start` / `scanner:ignore-block-end` (works as `<!-- … -->` in markdown) are skipped wholesale. Used internally to mark `SECURITY_RISK_PATTERNS` and the pattern-listing tables in `references/commands.md` and `skills-curator-lite/SKILL.md`. Available to skill authors who legitimately need to reference patterns in docs.
- 2 new pytest cases (`test_scanner_ignore_block_suppresses_findings`, `test_scanner_ignore_single_line`) → total 37 (was 35).

### Changed
- **`SKILL.md` trimmed** from 2073 → 1800 words. Removed command-list duplication that already lived in `references/commands.md`, removed "Why no install counts" from SKILL.md (lives in CLAUDE.md as maintainer-facing rationale), tightened `--customize` and Platform Management sections, replaced the duplicated "When to activate" block with a one-line non-redundant note. Added "Common Mistakes" table.
- **Pattern descriptions in `SECURITY_RISK_PATTERNS`** rewritten to use CWE references rather than echoing the literal trigger (`"Dynamic code execution call (CWE-95)"` instead of `"eval() — arbitrary code execution risk"`). Detection behavior unchanged.

### Notes
- Local-install copies in `~/.claude/skills/skills-curator/` were synced with the source during this work; future installs from npm/skills.sh will pick up the changes automatically.

## [4.4.0] — 2026-05-08

The Lite-promotion release. `skills-curator-lite` is now feature-parity with the v4.3 Python engine and ships as the default tier. The Python full version remains available as the performance/regression-tested tier.

### Added (skills-curator-lite v2.0.0)
- **Feature parity with the Python v4.3 engine.** Lite gains everything that previously needed Python: `--auto`-equivalent project fingerprint via byte-count + prefix comparison (state file at `auto_state.json`), `--customize`-equivalent section-by-section fork generation, GitHub topic-search catalog enrichment via `curl`, multi-target migration, and the 55-platform catalog.
- **Five verbs** (was three): RECOMMEND, EVALUATE, AUDIT, **PLATFORMS**, **MIGRATE** — plus the bonus CUSTOMIZE flow for forking external skills.
- **Embedded catalog expanded to 19 entries** (was ~10), with hand-written pros/cons matching the Python `KNOWN_SKILLS`.
- **Tag-rivals table + customization hints** — agent surfaces a `--customize` hint when a recommended skill's tags imply a stack mismatch with the project (Vue skill in a React project, etc.).
- **First-activation orientation** — same two-line intro as the Python version, adapted for Lite.
- **Live catalog enrichment** via `curl` to GitHub Search API. Honors `SKILLS_NO_TELEMETRY=1`. Cached at `~/.claude/skills/skills-curator-lite/catalog.json`.
- **Platforms catalog (all 55 supported agents)** embedded as YAML — same shape as the Python `PLATFORMS` dict so behavior matches.
- **Symptom→skill mapping** expanded from 11 → 17 patterns to mirror the Python version.

### Changed
- **Lite is now the default install tier.** `install.sh` and `install.ps1` install Lite unconditionally, and add the Python full version on top only when Python 3.10+ is available (or `--with-python` is passed). Order in `plugin.json` `skills` array flipped — Lite is now first.
- **Plugin description rewritten** to lead with "two tiers" (Lite + Python full).
- **Lite SKILL.md grew from ~360 lines to ~750 lines** because Python logic became agent instructions + embedded data.

### Notes
- Lite intentionally drops one capability the Python version has: **cross-device Gist sync via private GitHub Gist**. The plumbing requires a longer flow than belongs in a markdown skill; users who need sync should add the full Python tier.
- The two skills don't conflict — they use different registry paths (`skills-curator-lite/registry.json` vs `skills-curator/registry.json`). Install both if you want both.

## [4.3.0] — 2026-05-08

The platforms + live-catalog release. Skills Curator now knows about every agent platform `skills.sh` supports, the catalog enriches itself from GitHub topic search, and recommendations include hand-written pros/cons plus customization hints when a stack mismatch is detected.

### Added
- **`--platforms`** — lists every supported agent platform with detection status. `--verbose` expands the table from primary + detected to all 55. Shows install directory per platform, with `~` substitution.
- **Multi-target `--migrate`** — accepts comma-separated target list (`--migrate cursor,codex,roo`), the literal `detected` keyword, or `--all-detected` to mean every platform present on the machine. With no argument and a TTY, prints the platforms table and prompts. Falls back to `claude-code` in non-TTY contexts.
- **`PLATFORMS` catalog** (55 entries) replaces the prior 10-entry `AGENT_PATHS`. Sourced from `vercel-labs/skills` `dist/cli.mjs`. `AGENT_PATHS` is preserved as a `{id: Path}` view for backwards compatibility.
- **GitHub topic-search catalog enrichment** — `_fetch_github_topics()` queries `topic:claude-skill`, `claude-code-skill`, `agent-skill` from the GitHub Search API, classifies trust by author membership in `_TRUSTED_AUTHORS` (Anthropic, Vercel, Microsoft, Google, ComposioHQ + 5 others), merges with curated `KNOWN_SKILLS`. Curated entries always win on id collision. Cached in `catalog.json` per existing TTL. Honors `SKILLS_NO_TELEMETRY=1`.
- **Pros/cons** populated on every curated `KNOWN_SKILLS` entry. Honest assessments — what each skill is good at and what its costs are. Surfaces in `--recommend` output.
- **Customization hints in `--recommend`** — when a recommended skill's tags imply a stack mismatch with the project (Vue skill in a React project, Django skill in a FastAPI project, etc.), the output includes a one-line hint suggesting `--customize <id>` to fork it with rewritten examples.
- **First-activation orientation** in `SKILL.md` — when the skill activates the first time in a session and the user hasn't named a verb, the agent leads with a two-line intro describing the intelligence layer before answering.
- **Platform management section** in `SKILL.md` — instructs the agent on when and how to use `--platforms` and the new multi-target `--migrate`.
- 9 new pytest cases covering platforms catalog size, primary defaults, AGENT_PATHS back-compat, detection behavior, unknown-target rejection, multi-target migrate, pros/cons coverage, telemetry-off catalog behavior, and curated-wins merge semantics.

### Changed
- **`_load_catalog()`** now returns the merged curated+discovered catalog instead of just `KNOWN_SKILLS`. Behavior is unchanged when offline or with telemetry disabled.
- **`cmd_recommend()`** prints up to 2 pros and 2 cons per recommendation (when populated), plus the optional customization hint.
- **`plugin.json` description** rewritten to lead with "intelligence layer" and reference the catalog + 55-platform support, replacing the prior auto-activation-first framing.

### Notes
- `skills.sh` HTML scraping is **still deliberately not added back** — it was removed in v4.0 as brittle and dishonest. GitHub topic search gives us breadth via a stable JSON API instead.

## [4.2.0] — 2026-05-08

Two big additions: skill customization, and a no-Python companion.

### Added
- `--customize <source>` — takes an external skill (registered id, local path, or `owner/repo@skill`), scores each section by project fit, and emits a customization plan + a forked `SKILL.md` the agent can rewrite for this specific project's stack. Per-section actions: `keep`, `keep-trim`, `rewrite-stack`, `drop-or-rewrite`, `rewrite-frontmatter`. The engine produces structured artifacts; the agent does the prose rewrite.
- `--no-fork` flag for `--customize` (preview the plan without writing the fork file).
- New companion skill: **Skills Curator Lite** at `skills/skills-curator-lite/SKILL.md`. Pure markdown, no Python — the agent reads project files, applies the embedded catalog + symptom map + security patterns, and writes the registry directly via Bash. Use when Python isn't available or you want a transparent flow. Same model, same registry shape.
- Plugin manifest now registers both skills (`skills-curator` and `skills-curator-lite`) — install one or both.

### Changed
- SKILL.md gained a "Customizing an external skill" section explaining the customize→rewrite handoff.

## [4.1.0] — 2026-05-08

The intelligence layer. Skills Curator's USP shifts from *"evaluate when asked"* to *"activate proactively when the project context warrants it."*

### Added
- `--auto` — proactive scan that fingerprints the project (key dep/config/doc files + mtimes) and only re-recommends when the fingerprint changes. Cheap to call on every session start; designed for the agent to run silently without prompting.
- `--symptoms "<phrase>"` — maps user complaints (*"slow tests"*, *"ugly UI"*, *"manual deploy"*, etc.) to skill categories using a built-in symptom→tag table. 17 symptom patterns covering testing, CI/CD, UI, deploy, docs, commits, performance, auth, scraping, refactor, accessibility.
- `--find <term>` — explicit alias for `--discover`, matching the verb users learn from `npx skills find`.
- `auto_state.json` — persists last project fingerprint + top 3 picks per project so drift detection works across sessions.
- New SKILL.md "Proactive activation" section instructing the agent to run `--auto` at session start in any real project, and `--symptoms` whenever the user describes a pain point instead of naming a skill.
- New `references/discovery.md` sections: Skill Categories table (10 domains with example queries), single-skill response template, search tips.

### Changed
- SKILL.md: explicit "When to activate this skill" trigger-phrase list; full 6-step discover→evaluate→install workflow; explicit "no match" fallback (offer task help OR `--author`).
- Status output (`registry.py` no-args) now lists the Intel verbs alongside Discovery.

## [4.0.0] — 2026-05-08

First public release.

### Added
- `--export-eval <skill-id>` — emits the latest evaluation as a shareable markdown artifact (PR-ready)
- `--check <path>` — pre-install security scanner, 14 risk patterns
- `--audit` — duplicate detection, preference-conflict detection, gap analysis
- `--health` — A–D health score per registered skill, shows what's missing
- `--stale` — checks GitHub releases for outdated installed skills
- `--migrate <agent>` — copies installed skills across 9 agents (claude-code → cursor, codex, gemini-cli, cline, windsurf, github-copilot, opencode, amp, plus the cross-tool `agents` convention)
- `--author` — interactive scaffold producing `SKILL.md` + `MANIFEST.yaml` + `CHANGELOG.md`
- `--pros` / `--cons` / `--conflicts` flags on `--eval` so the CLI captures the full evaluation, not just the summary
- Slash commands: `/skill-evaluate`, `/skill-recommend`, `/skill-audit`
- Cross-device sync via private GitHub Gist (`SKILLS_CURATOR_GIST_ID` + `SKILLS_CURATOR_GITHUB_TOKEN`)
- `SKILLS_NO_TELEMETRY=1` disables all outbound network calls
- 26 pytest cases covering core registry, migration, security scan, project scan, validation, and export-eval
- CI matrix: Linux + macOS + Windows × Python 3.10 / 3.11 / 3.12 / 3.13

### Changed
- Pinned to Python 3.10+ (was inconsistent — code used 3.10 syntax but README claimed 3.8)
- Schema bumped to v3 (added `installed_version`, `pairs_with`, `security_scan` per skill)
- Schema migration now persists on first read instead of running silently on every load
- `--check` now records findings to `security_scan` field with severity, description, and file
- `_mark_security_reviewed` now matches by registry id with fuzzy fallback to source URL; warns if no match found instead of silently no-op'ing
- Recommendation scoring: removed install-count weighting, now ranks purely by tag overlap × trust tier
- `cmd_history` now displays conflicts and adoption_plan, not just summary
- Slash command surface collapsed from 9 to 3 verbs aligned with the product pitch (the CLI keeps everything)
- README restructured around the "persistent decisions" pitch instead of a feature comparison table
- AGENT_PATHS corrected: 4 of the original 10 paths were wrong; verified against each agent's docs

### Removed
- Fabricated `weekly_installs` numbers in the catalog (no public skills.sh API exposes them; removed the brittle HTML-scrape fallback)
- Unsourced "Snyk audit 13.4%" claim from the README
- 6 surplus slash commands collapsed into the audit verb
- `aider` from `--migrate` (no native skill system)

### Fixed
- `install.sh` was completely broken — rewrote to mirror `install_local.ps1` and added a Python 3.10+ guard
- `install.ps1` referenced files that don't exist (`registry.py` at root, four scripts merged into `registry.py`) — rewrote
- Version mismatches across `plugin.json` (3.1.0), `install.sh`/`install.ps1` (3.0.0), and other files — all unified to 4.0.0
- `references/schema.md` documented v2 fields; updated to v3
- `CONTRIBUTING.md` referenced a `validate.py` that doesn't exist; pointed to `registry.py --validate`
- `references/discovery.md` referenced four scripts that don't exist; corrected to unified registry.py paths
- `references/commands.md` advertised 4 slash commands that had no corresponding command files; corrected
- Missing `LICENSE` file added (MIT)
