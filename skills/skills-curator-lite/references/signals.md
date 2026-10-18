# Signals, rivals, symptoms

When the agent scans a project, it uses these tables to convert raw files into tags.

### Framework Signals (keywords found in package.json / requirements.txt / pyproject.toml / CLAUDE.md / README.md)

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

### Goal Signals (keywords found in CLAUDE.md / README.md, case-insensitive)

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

## Tag rivals (for customization hints)

When a recommended skill's tags imply a stack mismatch with the project, surface a `--customize` hint. Detection rule: if any of the skill's tags appear in column 1 AND any project tag appears in column 2 of the same row, flag a mismatch.

| Skill tags (left) | Project tags (right) — mismatch |
|---|---|
| vue, nuxt | react, nextjs |
| react, nextjs | vue, nuxt |
| angular | react, vue |
| django, flask | fastapi |
| fastapi | django, flask |

Hint format: *"Stack mismatch (`<skill-tag>` in skill vs `<project-tag>` in project) — fork it via CUSTOMIZE to rewrite examples."*

---

## Symptom → skill mapping

When the user describes a problem instead of naming a skill, match against this table and search the catalog by tag:

| User says (substring) | Look for skills tagged |
|---|---|
| `slow test`, `tests are slow` | testing, performance |
| `failing ci`, `ci is broken` | ci-cd, github-actions |
| `ugly ui`, `design is bad`, `ai-slop` | frontend-design, design-system, ui |
| `manual deploy`, `deploys are manual` | ci-cd, deploy |
| `no docs`, `missing docs` | docs, docgen |
| `messy commits`, `bad commit messages` | commit-writer, conventional-commits |
| `slow build`, `build takes forever` | build-tools, performance |
| `auth broken`, `login issue` | auth, session-management |
| `scraping broken`, `browser auth` | scraping, browser-automation |
| `accessibility`, `a11y` | accessibility, ui |
| `pr review takes`, `slow code review` | pr-review, code-review |
| `forget context`, `no memory` | memory, personalization |
| `mcp server` | mcp, integration |
| `mobile app`, `ios bug`, `android bug` | mobile, react-native |
| `video render`, `animation` | video, animation, remotion |
| `data extraction`, `parse pdf` | documents, data-extraction |
| `hardcoded keys`, `security audit` | security, audit |
