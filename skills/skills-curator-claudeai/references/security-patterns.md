# Security scan patterns

When evaluating an attached or fetched skill, the agent runs these patterns. Any HIGH or CRITICAL match should halt the evaluation pending user review.

The SKILL.md references this file during EVALUATE and SCAN.

---

## Severity-tagged pattern table

<!-- scanner:ignore-block-start -->
| Severity | Pattern (regex) | Why |
|---|---|---|
| CRITICAL | `curl\s+\S+\|\s*(sh\|bash)` | Remote code execution: pipe-to-shell |
| CRITICAL | `wget\s+\S+\|\s*(sh\|bash)` | Remote code execution: pipe-to-shell |
| CRITICAL | `rm\s+-rf\s+/\s*$` | Destructive root deletion |
| HIGH | `sk-[A-Za-z0-9]{32,}` | Hardcoded OpenAI key |
| HIGH | `sk-ant-[A-Za-z0-9-]{32,}` | Hardcoded Anthropic key |
| HIGH | `gh[pousr]_[A-Za-z0-9]{36,}` | Hardcoded GitHub PAT |
| HIGH | `ghs_[A-Za-z0-9]{36,}` | Hardcoded GitHub server token |
| HIGH | `password\s*=\s*['"][^'"]+['"]` | Hardcoded password literal |
| MEDIUM | `\beval\s*\(` | Dynamic code execution |
| MEDIUM | `\bexec\s*\(` | Dynamic code execution |
| MEDIUM | `import\s*\(.+\$\{` | Dynamic import with interpolation |
| MEDIUM | `base64\.(?:b64)?decode` | Possible obfuscation |
| MEDIUM | `\bkeychain\b\|\bcredmanager\b\|\bsecretservice\b` | OS credential store access |
| LOW | `http://[^"\s]+` (non-localhost) | Unencrypted endpoint |
<!-- scanner:ignore-block-end -->

---

## How the agent runs the scan

In the claude.ai sandbox, the simplest path is `grep -rE` over the skill folder. The agent should:

1. Stage the source files in `/tmp/scan-target/` (write attached content or fetched curl output there).
2. Run grep per pattern and tag the severity:
   ```bash
   SKILL_PATH=/tmp/scan-target
   grep -rE 'curl\s+\S+\|\s*(sh|bash)' "$SKILL_PATH"  # CRITICAL
   grep -rE 'sk-[A-Za-z0-9]{32,}'      "$SKILL_PATH"  # HIGH
   # ... etc for each row
   ```
3. Collate findings into the report table shown in SKILL.md § SCAN.

The Grep tool (when available) is preferred over `grep` via Bash — better permissions, faster.

---

## Halt rules

- **Any CRITICAL hit:** Stop. Report findings. Refuse to produce an ADOPT verdict until the user explicitly acknowledges.
- **Any HIGH hit:** Halt and surface to the user. They can override after review (e.g., the regex matched a documentation example, not real code).
- **MEDIUM / LOW:** Surface but proceed. Note them in the evaluation's Cons section.

---

## False-positive avoidance

Documentation files that legitimately list patterns (like this very document) can trip self-scans. Use the scanner-ignore markers:

- **Line-level:** any line containing the substring `scanner:ignore` is skipped.
- **Block-level:** content between `scanner:ignore-block-start` and `scanner:ignore-block-end` (works as HTML comments in markdown) is skipped entirely.

The pattern table above is wrapped in a block-ignore so this file doesn't flag itself.

When the agent scans an external skill, it should respect these markers if present — assume the author knows their documentation references patterns and isn't actually shipping them.

---

## When patterns fire wrongly

Sometimes the agent will hit a HIGH pattern that's clearly safe — e.g., a `password = "REDACTED"` placeholder in a comment, or an OpenAI-key shape that's actually an example from a tutorial. When this happens:

1. Surface the match honestly: *"Pattern X flagged this line, but it looks like an example placeholder — review and confirm before adopting."*
2. Let the user decide. Don't auto-suppress.
3. If the user confirms it's a false positive for this specific source, persist that decision in the registry's `security_scan` field so future SCAN/EVALUATE doesn't re-flag the same line.
