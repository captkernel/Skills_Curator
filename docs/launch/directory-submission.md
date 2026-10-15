# Anthropic directory submission sheet: Skills Curator

Prepared 2026-10-15 for a manual submission by the maintainer. Nothing has been submitted.
Portal facts were checked on 2026-10-14 against claude.com/docs/plugins/submit.

## Prerequisites

- [ ] Paid Claude plan
- [ ] GitHub account connected on claude.ai, with push access to `captkernel/Skills_Curator`
- [ ] Repo is public (it is)
- [ ] Limits: 10 submissions per 24 h; one submission per repo and folder

## Portal steps

1. Open https://claude.ai/directory/manage
2. Submit new
3. Choose "Plugin bundle"
4. Repository: `captkernel/Skills_Curator`
5. Plugin path: leave empty (the plugin is at the repo root, no subpath)
6. Branch or tag: `main`
7. Validate (expect a pass; see Checklist results)
8. Listing details (pre-filled from plugin.json and README, see below)
9. Data handling questions
10. Compliance acknowledgements
11. Submit for review

One listing reaches claude.ai, Cowork and Claude Code.

## Listing

| Field | Value |
|---|---|
| Name | `skills-curator` |
| Version | 4.6.2 |
| Author | captKernel (https://github.com/captkernel) |
| License | MIT |
| Keywords | skills-curator, skill-evaluator, skill-registry, claude-code, claude-ai, claude-skills, skill-security, agent-skills, skill-judgment |

**Short description** (plugin.json `description`, verbatim):

> Intelligence layer for Claude skills. Maintains a trust-rated catalog (curated + GitHub topic search), recommends what fits your project, returns ranked lists with pros, cons and customization advice, persists every decision, and migrates skills across 55 supported agent platforms. The plugin ships two tiers: Lite (Python-free, the default) and Python full (performance tier). A claude.ai edition for the claude.ai Skills feature is a separate download.

If the portal limits the description length, use this shorter form:

> Recommends the skills that fit your project, security-scans them, customizes them to your stack, remembers every decision, and migrates skills across 55 agent platforms.

**Long description** (ready to paste, from README facts):

> Skills Curator is the intelligence layer for Claude skills. It reads your project (stack, dependencies, CLAUDE.md) and recommends the skills that fit, with pros, cons and install commands. Before you install a skill it evaluates it (pros, cons, conflicts, verdict) and runs a pre-install security scan for 15 risk patterns, then saves the decision to a local registry, so asking again costs about 13 tokens instead of about 4,060. `--customize` splits an external SKILL.md into sections, scores each against your project and rewrites mismatched examples in your stack. Token cost is measured: 249 tokens always-on per session and at most 1,140 per command. It also audits installed skills and migrates them across 55 agent platforms.

**Category:** the portal's category list was not available when this sheet was written. Pick the closest of: Developer tools / Productivity / Skills management.

## Links

| Field | Value |
|---|---|
| Homepage | https://github.com/captkernel/Skills_Curator |
| Repository | https://github.com/captkernel/Skills_Curator |
| Support (repo issues) | https://github.com/captkernel/Skills_Curator/issues |

### Optional listing fields (optional, recommended)

The directory reads these from plugin.json (Claude Code ignores them; the validator accepts them on v2.1.281+). They are NOT yet in plugin.json; add them in a later task or enter them in the portal.

| plugin.json field | Suggested value |
|---|---|
| `icon` | `assets/logo-avatar.png` exists (raster, suits the directory). Vector alternatives: `assets/icon.svg`, `assets/logo.svg`. Also `assets/logo-social.png` (social card, probably wrong aspect) |
| `documentationUrl` | https://github.com/captkernel/Skills_Curator#readme (deeper reference: https://github.com/captkernel/Skills_Curator/blob/main/docs/reference.md) |
| `supportUrl` | https://github.com/captkernel/Skills_Curator/issues |
| `privacyPolicyUrl` | https://github.com/captkernel/Skills_Curator#what-it-runs-reads-and-sends |
| `termsOfServiceUrl` | https://github.com/captkernel/Skills_Curator/blob/main/LICENSE (MIT; no separate terms exist) |

## Data handling answers

The exact questions were not known when this sheet was written. These are best pre-filled answers derived from the README section "What it runs, reads and sends". They are answers to adapt, not quotes of the portal. Read each question in the portal first.

- **Does the plugin send data off the user's machine?** Not by default. Without Gist sync it only makes GET requests to GitHub: topic search on `api.github.com`, SKILL.md fetches from `raw.githubusercontent.com` when the user customizes a remote skill, and release lookups when the user runs `--stale`. The user's code, project content and registry stay on their machine.
- **Is there any opt-in data transmission?** Yes, Gist sync. The Python tier pushes the registry to the user's own private GitHub Gist only after the user sets `SKILLS_CURATOR_GIST_ID` and `SKILLS_CURATOR_GITHUB_TOKEN` and runs `--push` or `--sync`. Setup is documented in `docs/gist-sync.md`.
- **What does it read?** The user's project files (stack, dependencies, CLAUDE.md) and the skills installed under `~/.claude/skills`.
- **What does it write?** Its own state files (`registry.json` plus caches such as `catalog.json`) under `~/.claude/skills/skills-curator*/`; a temp file (`/tmp/source-skill.md`) briefly during Lite customization; a fork folder there when the user runs `--customize`; copies into other agents' skill folders when the user runs `--migrate`.
- **What code does it run?** Lite uses only the agent's Bash, Read, Glob, Grep and Write tools, plus `curl` to the GitHub search API and `raw.githubusercontent.com`. The Python tier runs one stdlib-only script, `skills/skills-curator/scripts/registry.py`, as a subprocess. No hooks, no MCP servers, no settings or permission changes.
- **Credentials or secrets?** Only the optional `SKILLS_CURATOR_GITHUB_TOKEN`, read from the environment (`registry.py` line 92) for opt-in Gist sync. When it is set, the Python tier also sends it as an `Authorization` header on GitHub topic search (`registry.py` line 956) and on `--stale` release lookups (`registry.py` line 2147), to `api.github.com` only. It is never stored by the plugin.
- **Does it install other software?** Not on its own. The catalog lists `npx skills add ...` install commands for third-party skills; these are shown to the user as recommendations. See the npx note below.

## Compliance acknowledgements

The portal shows 4 acknowledgements. Their wording is unknown here. Read each in the portal and tick it yourself.

- [ ] Acknowledgement 1 (read in the portal)
- [ ] Acknowledgement 2 (read in the portal)
- [ ] Acknowledgement 3 (read in the portal)
- [ ] Acknowledgement 4 (read in the portal)

## npx usage note

The pinned-version rule applies to npx/uvx that the plugin itself executes. Findings:

- No plugin component (manifest, hooks, MCP config, commands) executes npx or uvx. There are no hooks or MCP servers in the plugin.
- `npx skills add ...` appears in the README install docs, in `SECURITY.md` and `docs/reference.md`, in the catalog text inside both SKILL.md files and `references/*.md`, and as `install` strings in `skills/skills-curator/scripts/registry.py` (lines around 647 to 747). `registry.py` has no subprocess call that runs them; they are catalog data and recommendations shown to the user. README line 47 (`npx skills add captkernel/Skills_Curator`) is the user-facing install doc.
- All of these are unpinned (`npx skills add <owner/repo>`). If a reviewer objects, the cheapest fix is to pin the `skills` CLI version in the README install line.

## Held-for-review items

These do not cause rejection but a human reviewer will look at them.

| Item | Size | Justification |
|---|---|---|
| `docs/video/skills-curator-reel.mp4` | 2.6 MB | Launch reel (9:16) referenced from the README as a demo. Not loaded or executed by the plugin |
| `docs/video/skills-curator-reel-4x5.mp4` | 2.5 MB | Same reel in 4:5 feed format |
| `dist/skills-curator-claudeai.zip` | n/a | Upload-ready build of the claude.ai edition (`editions/skills-curator-claudeai/`) for the claude.ai Skills upload flow. Not loaded by the plugin |

Also: the keywords include `claude-code`, `claude-ai` and `claude-skills`. These are descriptive tags, not part of the plugin name.

## Checklist results

Run on 2026-10-15 at HEAD of `main` before adding this file.

| Check | Result |
|---|---|
| `claude plugin validate --strict .` | `✔ Validation passed` |
| `.claude-plugin/plugin.json` present, distinctive name | Yes, `skills-curator` |
| README at least 40 words outside code blocks | Yes (about 1800 words in total) |
| LICENSE or plugin.json license | Both (MIT) |
| `.DS_Store` / `Thumbs.db` / `desktop.ini` | None |
| Symlinks (mode 120000) | None |
| Submodules / LFS | None |
| `git archive HEAD` size | 6,809,600 bytes (limit 52,428,800) |
| Non-image files over 256 KiB | 2 (the two mp4 files above) |
| `.zip` / `.pdf` / `.ico` / `.exe` | 1 (`dist/skills-curator-claudeai.zip`) |
| Tracked file count | 66 (limit 512) |
| Secrets in tracked files | None found (filename scan; token appears only as an env var name in docs) |
| Pinned npx/uvx executed by the plugin | The plugin executes none; see the npx usage note |
| Security scan disclosure | README section "What it runs, reads and sends" covers runs, reads, writes, sends and the opt-in Gist sync |

## Registries

Checked 2026-10-15. Topics `agent-skills`, `claude-code-plugin`, `claude-skills`, `claude-code` are set on this repo.

- skills.sh publisher page `https://skills.sh/captkernel`: loads; lists `skills_curator` (2 skills, 20 installs).
- `https://skills.sh/captkernel/Skills_Curator`: loads. Status: listed, with `skills-curator` (13 installs) and `skills-curator-lite` (7 installs).
- skills.sh shows the command as `npx skills add captkernel/skills_curator`. Not run here, to avoid installing into real agent directories.
- `https://skills.sh/?q=skills-curator`: client-rendered shell, no results visible to a fetch, so inconclusive; the repo page above is the evidence.
