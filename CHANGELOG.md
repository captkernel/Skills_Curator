# Changelog

All notable changes to Skills Curator. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
