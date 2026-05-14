# Project signal extraction

When the agent scans the user's project context, it uses these tables to turn raw files (manifests, CLAUDE.md, README) into tags. Tags drive the RECOMMEND scoring step in SKILL.md.

---

## Framework signals

Keywords found in `package.json` / `requirements.txt` / `pyproject.toml` / `Pipfile` / `go.mod` / `Cargo.toml` / `CLAUDE.md` / `README.md`. Case-insensitive substring match.

| Keyword in file | Tags emitted |
|---|---|
| `react`, `next`, `nextjs` | `react, frontend, nextjs` |
| `vue`, `nuxt` | `vue, frontend` |
| `svelte`, `sveltekit` | `svelte, frontend` |
| `tailwind`, `tailwindcss` | `tailwind, css, design-system` |
| `playwright` | `playwright, browser-automation, testing` |
| `puppeteer` | `puppeteer, browser-automation` |
| `pytest`, `jest`, `vitest`, `cypress` | `testing` |
| `fastapi`, `flask`, `django`, `express` | `backend, api` |
| `prisma`, `drizzle`, `sqlalchemy` | `database, orm` |
| `terraform`, `pulumi`, `kubernetes` | `infra, devops` |
| `docker`, `dockerfile` | `devops, containers` |
| `langchain`, `openai`, `anthropic` | `ai, llm` |
| `pandas`, `numpy`, `torch`, `pytorch` | `data-science, ml` |
| `stripe` | `stripe, payments` |
| `postgres`, `mongodb`, `redis`, `supabase` | `database` |
| `expo` | `expo, react-native, mobile` |
| `remotion` | `remotion, video, animation` |

---

## Goal signals

Phrase patterns in `CLAUDE.md` / `README.md`, case-insensitive.

| Phrase pattern | Tags emitted |
|---|---|
| `scrape`, `crawl`, `extract data` | `scraping, data-extraction` |
| `auth`, `login`, `session` | `auth, session-management` |
| `dashboard`, `admin panel`, `cms` | `frontend, dashboard` |
| `migrate`, `migration` | `database, migration` |
| `agent`, `LLM`, `AI` | `ai, agents` |
| `test`, `testing`, `coverage` | `testing` |
| `deploy`, `CI/CD`, `release` | `ci-cd, deploy` |
| `documentation`, `docs` | `docs` |
| `accessibility`, `a11y` | `accessibility, ui` |
| `commit`, `pull request` | `git, code-review` |
| `video`, `animation` | `video, animation` |
| `mobile`, `iOS`, `android` | `mobile` |
| `memory`, `personalization`, `recall` | `memory, personalization` |

---

## Tag rivals (for CUSTOMIZE hints)

When a recommended skill's tags imply a stack mismatch with the project, surface a CUSTOMIZE hint. **Detection rule:** if any of the skill's tags appear in column 1 AND any project tag appears in column 2 of the same row, flag a mismatch.

| Skill tags (left) | Project tags (right) — mismatch |
|---|---|
| vue, nuxt | react, nextjs |
| react, nextjs | vue, nuxt |
| angular | react, vue |
| django, flask | fastapi |
| fastapi | django, flask |

Hint format: *"Stack mismatch (`<skill-tag>` in skill vs `<project-tag>` in project) — fork it via CUSTOMIZE to rewrite examples."*

---

## How to use this file

The SKILL.md tells the agent to read this file during RECOMMEND and CUSTOMIZE. It's a reference, not a runtime — there's no script that processes the tables. The agent reads the tables, applies them to whatever the user has attached, and emits the tag set.

If a relevant keyword for the user's stack is missing from these tables, the agent should:
1. Mention the gap to the user.
2. Add the keyword inline for this session.
3. Optionally offer to PR the addition back to `captkernel/Skills_Curator`.
