# Render templates

## RECOMMEND / CURATE result row

```
01. <trust-icon> <Name>   [curated|skills.sh|github]
     why: fit .8 (react, nextjs) · trust high · 185K installs
     What    : <one-line description>
     ✓ Pro   : <pro 1>        (curated entries only; up to 2)
     ✗ Con   : <con 1>        (curated entries only; up to 2)
     💡 Tip   : <customize hint, only if stack mismatch>
     Install : npx skills add <source> --skill <skillId>
     Link    : https://skills.sh/<source>/<skillId>
```

Full RECOMMEND frame: header `═══ Recommendations for: <project> ═══`, then `⚡ CAPABILITY — new abilities` and `🎨 PREFERENCE — better defaults` groups, numbered 01...
Trust icons: `🏛️` official · `✅` high · `🟡` medium · `⬜` community · `❓` unknown.
Rows the registry marks SKIP show `(previously rejected)` after the name.

## EVALUATE output (exact format, paste-able into a PR)

```
## Skill Evaluation: <Name>
Project: <project>
Type: Capability Uplift | Encoded Preference

### ✅ Pros
- <specific, tied to project goals>

### ⚠️ Cons
- <specific cost or limitation>

### 🔴 Conflicts
- <existing skill or pattern that overlaps; "None" if clean>

### 🎯 Verdict: ADOPT | PARTIAL | SKIP
<one or two sentences with the core reason>

### 📦 Adoption Plan
- Adopt: <which features>
- Skip: <which features>
- Pairs with: <skill-id or "nothing">
```

## Third-party audit line (advisory)

`Audits (skills.sh): Gen <risk> · Socket <n> alerts · Snyk <risk>   details: https://skills.sh/<source>/<skillId>`
Use `--` for a missing provider. Never block on it.
