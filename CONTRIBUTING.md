# Contributing to Skills Curator

Thanks for your interest. Here's what's useful and how to do it well.

---

## What to contribute

### Skill submissions
If you've evaluated a skill against a real project and have a useful verdict, open an issue using the **skill-submission** template (`.github/ISSUE_TEMPLATE/skill-submission.yml`). Include the install command, your evaluation, and which parts you actually adopted.

### Registry / schema improvements
New fields, schema changes, or validation rules — open an issue first to discuss before a PR. Schema bumps need a corresponding `_migrate()` step in `scripts/registry.py`.

### Validator improvements
New checks that catch real bugs are welcome. Keep exit codes consistent: `0` = pass, `3` = schema errors.

### Security patterns
New entries in `SECURITY_RISK_PATTERNS` (in `scripts/registry.py`) should come with:
- A justification (real-world example or CVE if available)
- A test case in `tests/test_security_scan.py`
- A severity tier (CRITICAL / HIGH / MEDIUM)

### Agent paths
New entries in `AGENT_PATHS` should reference the agent's documented skill directory location, not a guess.

### Documentation
Corrections, clarifications, and new docs for common patterns are always welcome.

---

## PR guidelines

1. **Keep `SKILL.md` under 200 lines** — move detailed content to `references/`.
2. **Run the full test + validate cycle before submitting** (see "Testing" below).
3. **Bump `metadata.version` in `SKILL.md` frontmatter** on any behaviour change.
4. **Bump `version` in `.claude-plugin/plugin.json`** to match.
5. **Bump `VERSION` in `scripts/registry.py`**.
6. **Update `CHANGELOG.md`** with a one-line description.
7. **Don't personalise** — the skill should work for any user, not just you.

---

## Skill type definitions

Use these consistently in any contributions:

| Type | Definition | Examples |
|---|---|---|
| `capability` | Gives Claude an ability it doesn't have natively | agent-browser, openspace, firecrawl |
| `preference` | Changes how Claude behaves on tasks it can already do | frontend-design, commit-writer |

---

## Testing

```bash
# Unit tests
python -m pytest tests/

# End-to-end smoke test
R=skills/skills-curator/scripts/registry.py
python $R                                                                         # init cleanly
python $R --list                                                                  # display
python $R --add test-skill "Test" "https://github.com/test/test" "echo install"
python $R --eval test-skill test-project adopt "Good fit" \
  --pros "fast,easy" --cons "small ecosystem"
python $R --history test-skill                                                    # shows pros/cons
python $R --validate --strict
python $R --health
python $R --audit
python $R --remove test-skill
```

All commands should exit `0` (validate exits `3` only on schema errors).

CI runs all of the above on every PR via `.github/workflows/validate.yml`.

---

## Code style

- Single-file `registry.py` — keep it that way. New features stay in one file unless they truly need their own module.
- Standard library only. No new dependencies.
- Python 3.10+ syntax is fine (`X | None`, `dict[str, list]`).
- Functions prefixed `cmd_` are CLI entry points; keep their signatures aligned with `argparse` definitions in `main()`.

---

## Releasing

Maintainer-only. After merging:

1. Tag: `git tag -a v4.x.y -m "..."`
2. Push tag: `git push origin v4.x.y`
3. Create release on GitHub with notes from `CHANGELOG.md`
4. Skills.sh re-indexes from GitHub releases automatically (no action needed).
