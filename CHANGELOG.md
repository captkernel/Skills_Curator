# Changelog

All notable changes to Skills Curator. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
