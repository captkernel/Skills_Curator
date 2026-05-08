---
description: Evaluate a Claude skill against the current project — security scan + pros/cons/conflicts/verdict, persisted to your decision registry
allowed-tools: Bash, Read, Glob
argument-hint: <skill-id-or-path>
---

# Evaluate a skill

You are evaluating a skill against this project. The user wants a real verdict, not a feature recap. Follow this exact flow.

## 1. Identify what's being evaluated

`$ARGUMENTS` is either:
- A registered skill id (`agent-browser`)
- A path to an unregistered local skill folder
- A `owner/repo` or full GitHub URL

Resolve which one. If it's a local path, run a security scan first:

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --check "$ARGUMENTS"
```

If CRITICAL or HIGH findings appear, **stop**. Tell the user not to install until each finding is reviewed.

## 2. Scan the project

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --scan
```

Use the project signals (languages, frameworks, goals) as your evaluation lens — does *this* project genuinely benefit?

## 3. Read CLAUDE.md and README

Use Read or Glob to find them. Evaluate against what the project says it's building, not against imagined goals.

## 4. Produce the evaluation in this exact format

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

## 5. Persist the decision

After the user agrees with the verdict:

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" \
  --eval <id> <project> <verdict> "<summary>" \
  --pros "<a>,<b>" \
  --cons "<c>,<d>" \
  --conflicts "<e>"
```

Then offer to export the evaluation as a shareable markdown artifact:

```bash
python "$HOME/.claude/skills/skills-curator/scripts/registry.py" --export-eval <id>
```

## Why this matters

Other tools install skills. This one **persists your judgment** so you don't re-decide every time. Treat the registry as the artifact.
