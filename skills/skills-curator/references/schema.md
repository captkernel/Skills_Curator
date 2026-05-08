# Registry Schema Reference

File: `~/.claude/skills/skills-curator/registry.json`
Schema version: **3.0**

---

## Top-level

```json
{
  "version": "3.0",
  "last_updated": "YYYY-MM-DD",
  "skills": []
}
```

The registry auto-migrates older versions on first load. v1 → v2 → v3 transitions are handled in `_migrate()`.

---

## Skill Object (v3)

```json
{
  "id": "agent-browser",
  "name": "Agent Browser",
  "type": "capability",
  "source": "https://github.com/vercel-labs/agent-browser",
  "install_command": "npx skills add vercel-labs/agent-browser --skill agent-browser",
  "description": "Browser automation via Chrome DevTools Protocol. Element refs (@e1, @e2), 6 auth methods, network inspection, screenshots.",
  "tags": ["browser", "automation", "CDP", "testing", "scraping"],
  "compatibility": ["claude-code", "codex", "cursor", "gemini-cli"],
  "security_reviewed": true,
  "security_scan": {
    "date": "2026-05-08",
    "result": "clean",
    "files_scanned": 24,
    "findings": []
  },
  "installed_version": "1.2.0",
  "pairs_with": ["openspace"],
  "date_added": "2026-05-08",
  "active_in_projects": ["my-scraper"],
  "evaluation_history": []
}
```

### Field Reference

| Field | Required | Type | Description |
|---|---|---|---|
| `id` | ✅ | string | Kebab-case slug. Must match folder name if locally installed. |
| `name` | ✅ | string | Display name |
| `type` | ✅ | enum | `capability` (new ability) or `preference` (changed behaviour) |
| `source` | ✅ | string | GitHub URL, `owner/repo` shortform, or other origin |
| `install_command` | ✅ | string | Exact command to install |
| `description` | | string | One-line summary |
| `tags` | | string[] | Searchable tags |
| `compatibility` | | string[] | Agents this skill works with |
| `security_reviewed` | | bool | Whether you've read the scripts and verified safety |
| `security_scan` | | object\|null | Last `--check` scan result. `null` until scanned. |
| `installed_version` | | string\|null | Version currently installed (used by `--stale`) |
| `pairs_with` | | string[] | IDs of skills that complement this one |
| `date_added` | ✅ | string | ISO date first registered |
| `active_in_projects` | | string[] | Project directory names where skill is active |
| `evaluation_history` | | array | List of evaluation records (see below) |

---

## Evaluation Record

```json
{
  "date": "2026-05-08",
  "project": "my-scraper",
  "verdict": "partial",
  "skill_type": "capability",
  "summary": "Useful for auth flows, overkill for static data extraction",
  "pros": [
    "Handles JS-heavy pages plain HTTP can't reach",
    "Session import auth covers cookie-based login"
  ],
  "cons": [
    "Requires Chrome — adds CI dependency",
    "Token-heavy for simple GET requests"
  ],
  "conflicts": [],
  "adoption_plan": {
    "adopt": ["session-import auth", "element reference system"],
    "skip": ["network inspection (covered by existing tooling)"],
    "pairs_with": ["openspace"]
  },
  "security_notes": []
}
```

### Verdict Values

| Verdict | Meaning |
|---|---|
| `adopt` | Install and use fully — strong fit for this project |
| `partial` | Install but use only specific features (see `adoption_plan`) |
| `skip` | Not suitable for this project — document why for future reference |

### Skill Type Values

| Type | Meaning |
|---|---|
| `capability` | Gives Claude a new ability it doesn't have natively |
| `preference` | Changes how Claude behaves on tasks it can already do |

---

## Migration Notes

| From | To | Changes |
|---|---|---|
| 1.0 | 2.0 | Added `type`, `compatibility`, `security_reviewed`, evaluation `skill_type`/`adoption_plan`/`security_notes` |
| 2.0 | 3.0 | Added `installed_version`, `pairs_with`, `security_scan` |

The migration runs once on first load. The migrated registry is persisted on the next write — you can force a save with any write operation (`--add`, `--eval`, etc.) or `python registry.py --validate`.
