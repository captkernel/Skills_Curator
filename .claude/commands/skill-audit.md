---
description: Full review of your installed Claude skills — duplicates, conflicts, security gaps, staleness, and health scores in one pass
allowed-tools: Bash
---

# Audit my skill stack

Run the four-part stack review:

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --audit
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --health
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --stale
```

The three together give the complete picture: what's broken, what's risky, what's outdated.

## How to present the result

Don't dump three reports back-to-back. Synthesise:

1. **Triage** — what should the user fix *first*? Lead with critical findings:
   - Preference conflicts (Claude getting contradictory instructions)
   - Security-unreviewed community skills
   - Stale versions of skills with known security history
2. **Group the rest** — duplicates, low health scores, unevaluated skills — as a punch list with the exact command to fix each
3. **End with one ask** — "Want me to evaluate the unreviewed ones now?"

## Why this matters

A skill stack rots. New skills overlap with old ones. Community skills go un-reviewed. Versions drift. Most users never look. This command makes the rot visible in 10 seconds.

Run `/skill-audit` after you install anything new, or weekly if you can remember.
