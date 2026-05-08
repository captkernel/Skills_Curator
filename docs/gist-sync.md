# Cross-device sync via GitHub Gist

Keep your skill registry in sync across all your machines without spinning up a server. The whole sync mechanism is one private GitHub Gist + a PAT.

---

## Setup (one-time)

### 1. Create the gist

Go to [gist.github.com](https://gist.github.com).

- Filename: `registry.json`
- Content: `{}`
- **Make it secret** — *not* public. Anyone with the URL can read a public gist.

Click "Create secret gist". Copy the gist ID from the URL: `https://gist.github.com/<your-handle>/<GIST_ID>`.

### 2. Create a fine-grained PAT

Go to [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).

- **Token name:** `skills-curator-sync`
- **Expiration:** your call. 90 days is reasonable.
- **Repository access:** *None* (we only need gists, not repos)
- **Permissions → Account permissions:**
  - **Gists: Read and write**

Click "Generate token" and copy it. You'll never see it again.

### 3. Set environment variables

```bash
# macOS / Linux — append to ~/.zshrc or ~/.bashrc
export SKILLS_CURATOR_GIST_ID="your-gist-id-here"
export SKILLS_CURATOR_GITHUB_TOKEN="ghp_..."
```

```powershell
# Windows PowerShell — set permanently for current user
[Environment]::SetEnvironmentVariable("SKILLS_CURATOR_GIST_ID", "your-gist-id-here", "User")
[Environment]::SetEnvironmentVariable("SKILLS_CURATOR_GITHUB_TOKEN", "ghp_...", "User")
```

Restart your shell for env vars to take effect.

---

## Using sync

```bash
R=~/.claude/skills/skills-curator/scripts/registry.py

# Upload your local registry to the Gist
python $R --push

# Pull the Gist down to this machine (overwrites local!)
python $R --sync
```

Typical workflow:

- After evaluating skills on machine A: `--push`
- When sitting down at machine B for the first time today: `--sync`
- Back at machine A after a day on B: `--sync`, then keep working

---

## What gets synced

The entire `registry.json` — all your skills, their evaluations, the full decision history. Everything in the file ships up unchanged.

**What does NOT get synced:**

- `catalog.json` (regenerated locally from skills.sh)
- `recommendations.json` (per-machine cache of past recommendations)
- The skills themselves (those live wherever they were installed)

---

## Conflict handling

This is a single-master scheme. `--sync` overwrites the local registry with whatever's in the Gist. `--push` overwrites the Gist with the local registry. There is **no merge**.

If you make decisions on machine A *and* machine B without syncing in between, the second `--push` wins. The losing decisions are gone unless you saved the file first.

For workflows that genuinely need multi-master, manage the gist manually or open an issue describing the use case — it's not impossible to add three-way merge, but most users don't need it.

---

## Privacy

Secret gists are not indexed and are not visible without the URL. They're not encrypted at rest on GitHub's servers. Don't put credentials in your evaluations — the registry is for verdicts and reasoning, not secrets.

If you want stricter privacy, encrypt the file before pushing. The simplest way:

```bash
# Encrypt before push
gpg --symmetric --cipher-algo AES256 ~/.claude/skills/skills-curator/registry.json
# (manually upload registry.json.gpg to gist instead, decrypt on pull)
```

This isn't built in — open an issue if you'd like an `--encrypt` flag.

---

## Disabling sync

Just don't set the env vars. The tool works completely offline; sync is opt-in.

To temporarily disable, unset the env vars in the current shell:

```bash
unset SKILLS_CURATOR_GIST_ID SKILLS_CURATOR_GITHUB_TOKEN
```

To go fully offline (no skills.sh fetch either), also set:

```bash
export SKILLS_NO_TELEMETRY=1
```
