# Awesome-list entries for Skills Curator (HELD)

Drafts only. Nothing here has been submitted. A human submits each one, later, after launch traction.
Install line for reference: `/plugin marketplace add captkernel/plugins` then `/plugin install skills-curator@captkernel`.

Baseline signals recorded 2026-10-15: Skills Curator 3 stars, about 20 installs on skills.sh. Claunchpad 0 stars, not on skills.sh.

## 1. hesreallyhim/awesome-claude-code

Rules (verified 2026-10-14 from CONTRIBUTING.md and the issue template):
- Submit through the web UI issue form only, by a human: https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml . Not a PR. The `gh` CLI cannot be used.
- One resource at a time. Submit this one first, after launch 1. Claunchpad waits until this recommendation is resolved.
- Resource must be at least 14 days old with ongoing commits, or have 100+ stars. Skills Curator qualifies on age and activity (first commit 2026-05-08).
- Description: descriptive, not a sales pitch, not addressed to the reader, no emojis. 10 to 500 characters.
- The bot discovers the license.

Form fields (template ids in parentheses):
- Display Name (`display_name`): Skills Curator
- Category (`category`, dropdown): Skills
- Link (`link`): https://github.com/captkernel/Skills_Curator
- Author Name (`author_name`): captKernel
- Author Link (`author_link`): https://github.com/captkernel
- Description (`description`): Trust-rated skill catalog and recommender for Claude Code. It matches skills to a project's stack, checks them for security problems, forks external skills to fit the project, records each decision, and migrates skills across 55 agent platforms.
- Checklist (`checklist`): tick every required box after actually doing each step (distinct from existing entries, links public, Claude Code specific, CONTRIBUTING.md read, attestation). Leave the optional trap box unchecked.

Other category options in the template, if "Skills" is rejected: Configuration, Multi-Purpose.

### On acceptance

Add this badge to the README:

```
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)
```

## 2. VoltAgent/awesome-agent-skills

README line (add at the end of the subcategory):

```
- **[captkernel/skills-curator](https://github.com/captkernel/Skills_Curator)** - Recommend, vet, and customize Claude skills for a project
```

(9 words in the description.)

- Subcategory: Community Skills > Productivity and Collaboration (README checked 2026-10-15; the subcategories are now Vector Databases, Marketing, Productivity and Collaboration, Development and Testing, Context Engineering, Specialized Domains, n8n Automation). Alternative: Development and Testing.
- Order: the Skills Curator PR goes first. Submit the Claunchpad PR only after the Skills Curator PR is merged, or after a gap of at least two weeks.
- PR title: `Add skill: captkernel/skills-curator`
- Hold condition: about 25 stars or visible installs. The maintainers decline brand-new skills and say they focus on community-adopted ones. The decision to submit is the owner's.
- History: PR #548 (Skills Curator) was closed on 2026-05-08 for lack of usage. Do not resubmit before there is visible usage (see hold condition).
