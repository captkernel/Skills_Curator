# Installing Skills Curator on claude.ai

This is the **claude.ai edition** of Skills Curator (`web + desktop`). It runs inside a claude.ai conversation via the Skills (Capabilities) feature — it is *not* a Claude Code CLI skill.

If you have Claude Code, install the CLI editions instead (`npx skills add captkernel/Skills_Curator`) for `--auto`, cross-agent migration, and Gist sync.

---

## Prerequisites

- **claude.ai plan** that exposes the Skills feature (Pro, Max, Team, or Enterprise as of May 2026).
- **Code Execution / Analysis tool enabled** — Settings → Capabilities. Skills Curator uses this to read attached files, run security scans, and write the updated registry to a downloadable file.
- **A claude.ai Project** (strongly recommended) — gives you persistent storage for the registry via Project Knowledge. The skill works without a Project too, but you'll need to upload/download the registry each session.

---

## Easiest: download the pre-built zip

A pre-built bundle ships with each release. Skip the build step entirely:

- **[`skills-curator-claudeai.zip`](https://github.com/captkernel/Skills_Curator/raw/main/dist/skills-curator-claudeai.zip)** — 19 KB, SKILL.md at the archive root, ready for upload.

Or build it yourself from a clone (instructions below).

## Build the bundle (only if you don't want the pre-built zip)

Zip the contents of this folder so `SKILL.md` sits at the **root** of the archive (not inside a subdirectory):

```
skills-curator-claudeai.zip
├── SKILL.md
├── INSTALL.md
└── references/
    ├── catalog.yaml
    ├── signals.md
    ├── security-patterns.md
    └── persistence.md
```

**Windows PowerShell:**

```powershell
cd skills/skills-curator-claudeai
Compress-Archive -Path SKILL.md, INSTALL.md, references -DestinationPath ../../skills-curator-claudeai.zip -Force
```

**macOS / Linux:**

```bash
cd skills/skills-curator-claudeai
zip -r ../../skills-curator-claudeai.zip SKILL.md INSTALL.md references
```

---

## Upload to claude.ai

1. Open claude.ai → **Settings** → **Capabilities** → **Skills**.
2. Click **Upload skill** and select `skills-curator-claudeai.zip`.
3. Toggle the skill on for the contexts where you want it active (globally, or per-Project).

---

## One-time persistence setup (recommended — Mode A)

The cleanest persistence mode is via Project Knowledge. The skill auto-reads the registry from there and writes updates as downloadable files.

1. Create or open a **Project** in claude.ai.
2. Open **Project Knowledge** for that Project.
3. Add a file named `skills_registry.json` with this initial content:

   ```json
   {"version": "3.0", "last_updated": "", "skills": []}
   ```

4. Make sure Skills Curator is enabled for the Project (Settings → Capabilities).

After a decision is made, the skill emits an updated `skills_registry.json` you can download from the conversation and re-upload to Project Knowledge to persist.

For other persistence modes (per-conversation upload, Gist sync), see [`references/persistence.md`](references/persistence.md).

---

## Alternative: Project Instructions (no Skills feature needed)

If your claude.ai plan doesn't expose the Skills feature (Free plan) or you'd rather avoid managing uploaded skills, you can run Skills Curator entirely via a **Project** instead. This trades auto-discovery for always-on behavior within one Project.

### Setup

1. Open claude.ai → sidebar → **Projects** → **New Project** (or open an existing one).
2. Open **Project Knowledge** and upload these files from the bundle:
   - `SKILL.md`
   - `references/catalog.yaml`
   - `references/signals.md`
   - `references/security-patterns.md`
   - `references/persistence.md`
   - `skills_registry.json` (start with `{"version": "3.0", "last_updated": "", "skills": []}`)
3. Open **Project Instructions** and paste this directive:

   ```
   You have access to the Skills Curator skill via Project Knowledge.
   Read SKILL.md and follow its instructions exactly. When a verb
   (RECOMMEND, EVALUATE, SCAN, AUDIT, CUSTOMIZE) requires a reference
   file (catalog.yaml, signals.md, security-patterns.md,
   persistence.md), read it on demand from Project Knowledge. The
   user's persistent registry lives at skills_registry.json in
   Project Knowledge — read from it, and emit updated versions to
   /mnt/user-data/outputs/skills_registry.json when decisions change.
   ```

4. Save the Project. Open a new conversation inside it.

### Trade-offs vs the Skills feature install

| | Skills feature (upload zip) | Project Instructions (this workaround) |
|---|---|---|
| Activation | Auto-discovered when relevant — Claude decides based on the skill's `description` | Always-on for every conversation in this Project |
| Reach | Active everywhere you enable the skill | Limited to one Project |
| Plan requirement | Pro / Max / Team / Enterprise | Works on Free plan |
| Setup steps | 1 zip upload + 1 registry file | 6 file uploads + 1 instructions paste |
| Updates | Re-upload one zip when a new version ships | Re-upload changed files individually |
| Behavior fidelity | Full | Full (same `SKILL.md`, same references, same registry) |

If you can use the Skills feature, do — it's auto-activating and scales to every conversation. The Project Instructions path exists so users on the Free plan can still get the same judgment model.

---

## Verifying the install

In a new conversation with the skill enabled, ask:

> *"Should I install the frontend-design skill?"*

You should see the orientation line *"Skills Curator loaded — your intelligence layer for Claude skills (claude.ai edition)."* before the evaluation begins. If you don't see the orientation and Claude answers from general knowledge instead, the skill isn't loaded — re-check Settings → Capabilities → Skills.

---

## Differences vs the Claude Code editions

| | This (claude.ai) | Claude Code Lite | Claude Code Python |
|---|---|---|---|
| Runtime | claude.ai web + desktop | Claude Code CLI | Claude Code CLI |
| Persistence | Project Knowledge / upload / Gist | `~/.claude/skills/.../registry.json` | `~/.claude/skills/.../registry.json` (+ Gist) |
| Project signals | Attached / Project Knowledge files | Files in cwd | Files in cwd |
| Cross-agent migration | Removed | 55 platforms | 55 platforms |
| Engine | Agent + references/ | Agent + embedded YAML | Python single-pass (~2.3k LOC) |
| Tests | None (no engine) | None | 37 pytest cases |
| Headline verb (`CUSTOMIZE`) | ✅ outputs to `/mnt/user-data/outputs/<fork>.zip` | ✅ writes to `~/.claude/skills/<fork>/` | ✅ writes to `~/.claude/skills/<fork>/` |

For migrating skills to other CLI agents (Cursor, Codex, Gemini CLI, etc.), use the Claude Code editions. claude.ai has no equivalent target.
