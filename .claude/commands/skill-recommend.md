---
description: Recommend Claude skills that fit the current project's tech stack and goals — judgment-driven, not popularity-driven
allowed-tools: Bash, Read
---

# Recommend skills for this project

Run the project-aware recommendation engine:

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --recommend
```

If `$ARGUMENTS` contains "refresh", pass `--refresh` to force a fresh catalog fetch.

## How to present the result

Don't just dump the output. Walk the user through it:

1. **Lead with the strongest match** — highest score, highest trust tier
2. **Explain why it matched** — which project tags triggered it, in plain English ("you're doing scraping, this is for scraping")
3. **Group by type** — Capability skills (new abilities) before Preference skills (better defaults)
4. **Flag trust** — 🏛️ Official, ✅ High, 🟡 Medium
5. **Offer the next step** — "Want me to evaluate this against your project goals?" → triggers `/skill-evaluate`

## Why this differs from `npx skills` or skills.sh

The skills.sh leaderboard ranks by install counts. **This ranks by fit.** A skill with 50k installs is a worse match than a skill with 200 installs if those 200 installs were on projects exactly like yours.

Trust tier + tag overlap is the signal we use. If you want raw popularity, `--discover` is the catalog browser.
