## What this changes

<!-- One paragraph. What's different and why. -->

## Type

- [ ] Bug fix
- [ ] New feature / capability
- [ ] Catalog entry (new skill in `KNOWN_SKILLS`)
- [ ] Security pattern (new entry in `SECURITY_RISK_PATTERNS`)
- [ ] Doc / refactor (no behaviour change)

## Pre-merge checklist

- [ ] `python -m pytest tests/` passes
- [ ] `python skills/skills-curator/scripts/registry.py --validate --strict` exits 0
- [ ] `metadata.version` in `SKILL.md` bumped (if behaviour changed)
- [ ] `version` in `.claude-plugin/plugin.json` bumped to match
- [ ] `VERSION` in `scripts/registry.py` bumped to match
- [ ] `CHANGELOG.md` updated
- [ ] If adding a `SECURITY_RISK_PATTERNS` entry: a corresponding test in `tests/test_security_scan.py`
- [ ] If adding an `AGENT_PATHS` entry: a doc URL cited in the PR description
