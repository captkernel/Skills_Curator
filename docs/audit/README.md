# Token cost audit + walkthrough

Empirical token-cost measurement and feature documentation for Skills Curator.

## Outputs

Two HTML pages live at `docs/`:

| File | What it covers |
|---|---|
| [`docs/token-cost-report.html`](../token-cost-report.html) | Empirical measurement — every command, every project, real numbers. Bar charts, per-command tables, session profiles. |
| [`docs/how-it-works.html`](../how-it-works.html) | Conceptual walkthrough — glossary, architecture diagram, feature-by-feature breakdown with honest token accounting, the 17 symptom patterns, the 15 security patterns. |

## Scripts in this folder

| File | Purpose |
|---|---|
| `deep_token_audit.py` | Runs every CLI command against multiple test projects, counts stdout tokens with `tiktoken`. Writes `audit_results.json`. |
| `generate_html.py` | Reads `audit_results.json`, emits `docs/token-cost-report.html`. |
| `generate_walkthrough.py` | Reads `audit_results.json`, emits `docs/how-it-works.html`. |
| `audit_results.json` | Latest measurement (committed for transparency — regenerate to update). |

## Run it

```bash
pip install tiktoken
python docs/audit/deep_token_audit.py     # writes docs/audit/audit_results.json
python docs/audit/generate_html.py        # writes docs/token-cost-report.html
python docs/audit/generate_walkthrough.py # writes docs/how-it-works.html
```

## Custom projects

Override the default test projects:

```bash
python docs/audit/deep_token_audit.py --projects /path/to/projA,/path/to/projB
```

The default set spans empty → 17,680-file projects to demonstrate that engine output is bounded regardless of project size. Swap in your own paths to verify on your codebases.

## What's measured

- **Static**: SKILL.md token counts (both tiers), references/, the Python engine
- **Always-on cost**: just the frontmatter description (what Claude loads per session)
- **Per-command stdout**: actual subprocess output token counts — what enters Claude's context
- **Session profiles**: realistic mix of commands for silent / light / heavy session types

## Why tiktoken, not Anthropic's tokenizer?

Anthropic doesn't publish a local tokenizer. `tiktoken` is OpenAI's BPE tokenizer; Anthropic's is also BPE with a similar vocabulary scale. Counts are within ~5–10% of what Claude actually sees — close enough to draw correct relative conclusions about scale.
