# Skills Curator — Token Cost Analysis

> 📊 **Looking for the visual report?** See **[token-cost-report.html](./token-cost-report.html)** — a single-file, no-CDN HTML report with charts, per-verb tables, and session profiles. Generated from real measurements; regenerable on any machine in 60 seconds.

---

## TL;DR

Token costs were measured with `tiktoken` against **5 real projects** ranging from 1 file to **17,680 files**, plus every CLI verb in both tiers. Findings:

| Metric | Number |
|---|---:|
| Always-on cost per session (both tiers combined) | **249 tokens** (~0.025% of a 1M context window) |
| Max single-verb stdout, on a 17,680-file Next.js project | **965 tokens** |
| Max single-verb stdout, on a 48-file repo | **1,140 tokens** |
| **Project size's effect on token cost** | **None measurable** (engine output is bounded by design) |
| Savings vs ad-hoc evaluation across 7 skill interactions | **20,038 tokens (71%)** |
| Re-asking about a previously evaluated skill (`--history`) | **~13 tokens** vs ~4,060 without persistence |

---

## Why project size doesn't matter

The engine deliberately caps inputs:

- `_scan_project` reads CLAUDE.md, README.md, package.json, requirements.txt, pyproject.toml, Pipfile — and **truncates doc reads to 4,000 chars**.
- `rglob` is used only to count file extensions for language detection; file contents are not emitted.
- Catalog matches are deduplicated and capped at `--max 8` by default.

Result: a 17,680-file React Native codebase with a 20 KB CLAUDE.md generates the same-size stdout as a 30-file folder. The HTML report includes a grouped bar chart that makes this visually obvious — bars are flat across project sizes.

---

## What was measured

**Static (loaded into context):**
- Frontmatter description (both tiers, always loaded at session start): **249 tokens**
- SKILL.md body (Python tier, loaded on skill activation): **3,359 tokens**
- SKILL.md body (Lite tier, loaded on skill activation): **10,988 tokens**
- All `references/*.md` combined (rarely all loaded in one session): **5,358 tokens**

**Engine, NOT in context:**
- `registry.py` (subprocess — Claude only sees stdout): **27,900 tokens of source code, 0 tokens of context cost**

**Per-verb stdout** (24 verbs × 5 projects = 120 measurements):
- 10 verbs are **constant** across all projects (`--symptoms`, `--platforms`, `--search`, `--find`, `--discover`, `--stale`, `--version`, etc.)
- 14 verbs vary by ±200 tokens or less across the project range — driven by catalog match count, not project size

Full per-verb table lives in the HTML report.

---

## Session profiles (Large project: Next.js + 20 KB CLAUDE.md)

| Session type | Tokens | Notes |
|---|---:|---|
| Silent — just project work, skill never activates | **249** | Frontmatter description only |
| Light WITH Skills Curator (1× auto + 1× recommend + 1× evaluate) | **5,629** | SKILL.md + 3 subprocess outputs |
| Heavy WITH Skills Curator (7 skill interactions, mixed verbs) | **8,382** | SKILL.md + 7 subprocess outputs |
| Heavy WITHOUT (7 ad-hoc evaluations, no persistence) | **28,420** | Each WebFetches + reasons from scratch |
| **Heavy session savings** | **20,038 tokens (71%)** | Plus persistence means future sessions cost ~150 tokens per repeat ask |

---

## The customization payoff

`--customize` is the headline capability and also the case where context savings compound. The engine produces a structured per-section action plan (≈970 tokens) instead of forcing the agent to reason about every section from scratch (≈3,000 tokens).

| Step | Without skill | With `--customize` |
|---|---:|---:|
| Fetch source SKILL.md (~10 KB) | ~2,560 | 0 *(engine reads it)* |
| Decide what to keep/drop/rewrite | ~3,000 | **~970** *(structured plan)* |
| Agent rewrites mismatched sections | ~2,000 | ~2,000 *(same, but directed)* |
| **Total per customization** | **~7,560** | **~3,000** |

---

## Methodology

- Tokenizer: `tiktoken` `cl100k_base` (GPT-4's BPE encoding). Anthropic's tokenizer is also BPE with similar vocabulary scale → counts within ~5–10% of what Claude actually sees.
- External SKILL.md size assumption (10 KB / 2,560 tokens) for the "without-skill" baseline was validated against **42 real installed SKILL.md files**: average 11,057 bytes / 2,623 tokens, median 2,280 tokens.
- Engine subprocess stdout is captured via `subprocess.run(capture_output=True)` and counted as one block — this is exactly what Claude Code shows the agent.
- Reproducibility: scripts at `docs/audit/deep_token_audit.py` + `docs/audit/generate_html.py`. Raw measurements at `docs/audit/audit_results.json`.

## Reproduce on your machine

```bash
git clone https://github.com/captkernel/Skills_Curator
cd Skills_Curator
pip install tiktoken
python docs/audit/deep_token_audit.py    # writes docs/audit/audit_results.json
python docs/audit/generate_html.py       # writes docs/token-cost-report.html
```

Override the test projects with `--projects path1,path2,...` to point at your own codebases.
