# Persistence deep dive

The claude.ai sandbox is fresh every conversation. There's no persistent `~/.claude/` filesystem. Skills Curator preserves judgment across sessions by storing the registry in a place the user controls. **Three modes**, in order of recommendation.

---

## Mode A — Project Knowledge (recommended for repeat use)

Best for: users who do skill-management work inside a long-running claude.ai Project.

### Initial setup (one-time per Project)

1. Open claude.ai → sidebar → **Projects** → either open an existing Project or create a new one for your skills-management work.
2. Open **Project Knowledge** (the panel that lists pinned files Claude sees in every conversation in this Project).
3. Add a new file named `skills_registry.json` with this initial content:

   ```json
   {
     "version": "3.0",
     "last_updated": "",
     "skills": []
   }
   ```

4. Make sure the Skills Curator skill is enabled for this Project (Settings → Capabilities for that Project, or globally).

### Read path

When a new conversation starts in this Project, the registry is injected as part of the system context (Project Knowledge files are auto-loaded). Skills Curator can read it inline.

### Write path

claude.ai does not let Claude directly mutate Project Knowledge files. The flow is:

1. Skills Curator builds the updated registry JSON in memory.
2. Writes it to `/mnt/user-data/outputs/skills_registry.json` via the code-execution tool:
   ```python
   import json, pathlib
   pathlib.Path("/mnt/user-data/outputs/skills_registry.json").write_text(
       json.dumps(registry, indent=2)
   )
   ```
3. Tells the user: *"Updated registry written to `skills_registry.json` (download link above). To persist this decision, replace the file in your Project Knowledge."*

The user clicks the download, opens Project Knowledge, removes the old file, uploads the new one. Done.

### Pros / cons

- ✅ Cleanest read path — registry available with zero attachment effort
- ✅ Survives every conversation in the Project automatically
- ✗ Two manual steps to write back (download + re-upload in Project Knowledge)

---

## Mode B — Upload / download per conversation

Best for: ad-hoc use without a Project.

### Setup

None. The user uploads `skills_registry.json` (or a starter `{"version":"3.0","last_updated":"","skills":[]}` JSON) to the conversation when they start.

### Read path

Skills Curator reads from the attached file via the standard file-read tool.

### Write path

Same as Mode A — write to `/mnt/user-data/outputs/skills_registry.json` and let the user download it. They save it locally and attach it to the next conversation.

### Pros / cons

- ✅ No Project setup
- ✗ Have to remember to attach + save every session
- ✗ Easy to lose decisions if you forget to download

---

## Mode C — Gist sync (power users)

Best for: users with a GitHub PAT who want cross-device sync without manual file shuffling.

### Setup

1. Create a private Gist on GitHub with a file named `skills_registry.json` and the initial JSON content.
2. Note the Gist ID (the random hex in the URL).
3. Create a fine-grained PAT with `gist` scope.
4. Pin both the Gist ID and the PAT to Project Knowledge as text (e.g., `SKILLS_REGISTRY_GIST_ID=abc123` / `SKILLS_REGISTRY_GIST_TOKEN=ghp_…`), or paste them at the start of each conversation. **Treat the PAT as ephemeral — don't let Skills Curator ever write it back to Project Knowledge.**

### Read path

```bash
curl -sL \
  -H "Authorization: token $SKILLS_REGISTRY_GIST_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/gists/$SKILLS_REGISTRY_GIST_ID" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['files']['skills_registry.json']['content'])" \
  > /tmp/registry.json
```

### Write path

```bash
BODY=$(python3 -c "import json; print(json.dumps({'files':{'skills_registry.json':{'content': open('/tmp/registry.json').read()}}}))")
curl -sL -X PATCH \
  -H "Authorization: token $SKILLS_REGISTRY_GIST_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/gists/$SKILLS_REGISTRY_GIST_ID" \
  -d "$BODY"
```

### Pros / cons

- ✅ True sync — same registry across devices, claude.ai conversations, and Claude Code installations
- ✅ Version history (Gists keep revision history automatically)
- ✗ Setup requires a GitHub PAT
- ✗ Token handling — be careful never to let Skills Curator persist the PAT to a file

### Security caveat

The Skills Curator agent should treat the GitHub PAT as ephemeral. Never:
- Write it to `/mnt/user-data/outputs/`
- Include it in any artifact or persisted file
- Echo it back in chat

Read it from the user's pasted text, use it for the API call, never write it anywhere.

---

## Schema

The registry schema is `v3.0` and identical across all three editions of Skills Curator (Claude Code Lite, Claude Code Python, claude.ai). The same file can be moved between editions without conversion.

```json
{
  "version": "3.0",
  "last_updated": "2026-05-14",
  "skills": [
    {
      "id": "frontend-design",
      "name": "Frontend Design",
      "source": "anthropics/skills",
      "install": "npx skills add anthropics/skills --skill frontend-design",
      "type": "preference",
      "tags": ["frontend", "design", "react", "css", "html", "ui"],
      "trust": "official",
      "installed_version": null,
      "security_scan": {
        "scanned_at": "2026-05-14",
        "findings": []
      },
      "pairs_with": [],
      "evaluations": [
        {
          "date": "2026-05-14",
          "project": "my-saas-app",
          "verdict": "adopt",
          "summary": "Bold aesthetic guidelines match brand goals",
          "pros": ["Anthropic-curated", "stack-agnostic"],
          "cons": ["Heavier on non-UI tasks"],
          "conflicts": []
        }
      ]
    }
  ]
}
```

### Field semantics

| Field | Purpose |
|---|---|
| `version` | Schema version. Used by migration logic if schema bumps in future. |
| `last_updated` | ISO date of the most recent change. Set by the agent when writing. |
| `skills[].id` | Stable kebab-case identifier. Often matches the source skill's name. |
| `skills[].source` | Where the skill comes from — `owner/repo`, or `local-path`, or `npx <pkg>`. |
| `skills[].type` | `capability` (new abilities) or `preference` (encoded style/discipline). |
| `skills[].tags` | Tag set used for project-fit scoring. Lowercase, hyphenated. |
| `skills[].trust` | `official` / `high` / `medium` / `community` / `unknown`. Drives the score bonus. |
| `skills[].evaluations[]` | Append-only — history matters; never overwrite a prior verdict. |
| `evaluations[].verdict` | `adopt` / `partial` / `skip` (lowercase in JSON; uppercase in user-facing output). |

---

## Migrating from an older schema

If the registry has `version` other than `3.0`, the agent should:

1. Identify the source schema (v1 had no `tags` field; v2 had no `evaluations[]` array).
2. Apply migration rules:
   - v1 → v2: add empty `evaluations[]`, copy old `decision` field into the first evaluation.
   - v2 → v3: add `tags: []`, `trust: "unknown"`, `security_scan: null`, `pairs_with: []` for any skill missing them.
3. Bump `version` to `3.0`, write the migrated file, notify the user.

The Claude Code Python edition has automated migration in `_migrate()` of `registry.py`. The claude.ai edition does it manually with the agent reading + rewriting.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| "Registry is empty even after I evaluated 3 skills" | Mode A: forgot to re-upload to Project Knowledge after download. | Re-download from the last conversation's `/mnt/user-data/outputs/` (claude.ai keeps recent files), replace in Project Knowledge. |
| "Skills Curator can't see the registry" | Project Knowledge file is named wrong, or the Project doesn't have the skill enabled. | Filename must be `skills_registry.json`. Check Project → Settings → Capabilities → Skills. |
| "Two registries drifted between Claude Code and claude.ai" | Both editions wrote independently. | Pick a winner manually (the more recent `last_updated`), or merge `evaluations[]` arrays by skill id. Future: use Mode C Gist sync. |
| "Gist PAT leaked into a Project Knowledge file" | The agent persisted it by mistake. | Rotate the PAT immediately on GitHub. Re-create the Gist if any of its revisions contain the leaked token. |
