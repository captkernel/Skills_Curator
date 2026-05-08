# Skill Evaluation — Format and Principles

---

## Evaluation Output Format

Use this exact format for every skill evaluation:

```
## Skill Evaluation: <Skill Name>
Project: <project name or directory>
Date: <YYYY-MM-DD>
Skill type: <Capability Uplift | Encoded Preference>

### ✅ Pros
- <specific benefit tied to this project's stated goals>
- <another benefit>

### ⚠️ Cons
- <limitation, overhead, or dependency cost>
- <another downside>

### 🔴 Conflicts  (🟡 if advisory only)
- <direct conflict with existing skill or project pattern>
- None  ← if no conflicts

### 🎯 Verdict: <ADOPT | PARTIAL | SKIP>
<1–2 sentences: what to use, what to ignore, and the core reason>

### 📦 Adoption Plan
- Adopt: <specific feature, mode, or module>
- Skip: <specific feature, mode, or module>
- Pairs well with: <skill it complements, or "nothing installed yet">
- Install command: <exact command to run, or "already installed">

### ⚠️ Security Note  (omit if not applicable)
- <any community skill risks, network calls, or data access to be aware of>
```

---

## Skill Types

Classifying the skill type sharpens the evaluation:

**Capability Uplift** — gives Claude a new ability it doesn't have natively.
Examples: agent-browser (browser control), firecrawl (web scraping), openspace (self-evolving skills), document-skills (PDF/DOCX generation)

Evaluation lens: *Does this project need this capability? Is there already another skill providing it?*

**Encoded Preference** — changes how Claude behaves on tasks it can already do.
Examples: frontend-design (forces bold design direction), react-best-practices (enforces conventions), commit-writer (standardises messages)

Evaluation lens: *Does this preference align with the project's existing conventions? Does it conflict with another preference skill?*

---

## Evaluation Principles

Apply all of these when assessing a skill:

**Vision alignment** — does it serve what the project's CLAUDE.md / README explicitly says it's building? Don't evaluate against imagined goals.

**Overlap detection** — does it duplicate a capability or preference already covered by an installed skill? Two skills teaching different browser automation patterns is a conflict.

**Complexity cost** — every skill adds to the token budget at session start (name + description loaded always). Evaluate whether the benefit justifies the constant cost plus any dependency overhead.

**Partial adoption** — always look for which parts are worth using even when the whole isn't. A security audit skill might have one workflow worth keeping while the rest is overkill.

**Conflict severity:**
- 🔴 Blocking — two skills give contradictory instructions on the same task. One must be disabled.
- 🟡 Advisory — skills overlap but don't directly contradict. Monitor for confusion.

**Default behaviour shift** — the best skills change what Claude produces without needing to be invoked. If a skill only adds a slash command the user has to remember, it's lower priority than one that improves every relevant response automatically.

**Security** — community skills can include scripts that make outbound network calls or access credentials. Flag any concern in the Security Note section.

---

## Saving to Registry

After producing the evaluation output, append this to `evaluation_history` for the skill:

```json
{
  "date": "YYYY-MM-DD",
  "project": "<project name>",
  "verdict": "adopt | partial | skip",
  "skill_type": "capability | preference",
  "summary": "<one line>",
  "pros": ["<pro 1>", "<pro 2>"],
  "cons": ["<con 1>"],
  "conflicts": ["<conflict 1>", "none"],
  "adoption_plan": {
    "adopt": ["<feature>"],
    "skip": ["<feature>"],
    "pairs_with": ["<skill-id>"]
  },
  "security_notes": []
}
```
