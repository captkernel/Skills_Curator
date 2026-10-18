# Security scan patterns

When evaluating a local skill folder, the agent runs Grep with these patterns. Any HIGH or CRITICAL match should halt the install pending review.

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

Example Grep run:
```bash
SKILL_PATH="$1"
echo "Scanning $SKILL_PATH..."
grep -rE 'curl\s+\S+\|\s*(sh|bash)' "$SKILL_PATH" && echo "CRITICAL: pipe-to-shell"
grep -rE 'sk-[A-Za-z0-9]{32,}'      "$SKILL_PATH" && echo "HIGH: hardcoded API key"
# ...etc
```
<!-- scanner:ignore-block-end -->

The agent should run each pattern via the Grep tool (preferred over Bash for performance and permissions). Documentation that lists pattern definitions verbatim should be wrapped in `<!-- scanner:ignore-block-start -->` / `<!-- scanner:ignore-block-end -->` (or `# scanner:ignore` for single-line Python) so the engine and agent skip them during self-scans.
