# Security Policy

## Reporting a vulnerability

If you find a security issue in `Skills_Curator` itself (the tool, not a skill it lists), **do not open a public GitHub issue.**

Instead, email **karanparmar7993@gmail.com** with:

- A description of the issue
- Steps to reproduce
- The version of the tool you're using (`python registry.py --version`)
- Whether you've disclosed the issue elsewhere

You will get an acknowledgement within 5 working days. Once a fix is available, the disclosure timeline is coordinated with you.

---

## Reporting a malicious skill

If you encounter a Claude skill on `skills.sh` or GitHub that contains malicious code, hardcoded credentials, or data-exfiltration endpoints, please:

1. Run `python registry.py --check <path>` and save the output.
2. Open an **issue** (not a security advisory) on this repo using the `report-bad-skill` template, with the scan output and a link to the skill repo.
3. Also report it to `skills@vercel.com` so they can review for catalog removal.

We do not maintain a blocklist in this tool, but high-severity findings drive new patterns added to `SECURITY_RISK_PATTERNS` in `scripts/registry.py`.

---

## Trust model

- `registry.py` is **stdlib-only Python**. Reviewing it line-by-line is feasible.
- The tool reads local files and makes optional network calls to:
  - `api.github.com` (Gist sync, release-version checks)
  - `skills.sh` (catalog enrichment, install-count fetch)
- It never sends your code, project content, or registry contents to any external service.
- All outbound calls are gated on `SKILLS_NO_TELEMETRY=1`. Set that env var to make the tool fully offline.

---

## Scope

This policy covers:

- The Python script `scripts/registry.py`
- The shell installers `install.sh` and `install.ps1`
- The deploy script `deploy.py`

It does **not** cover:

- Skills the tool catalogs or installs (those are third-party — use `--check` to scan them yourself)
- The skills.sh service or the `npx skills` CLI (report those upstream)
- Cosmetic bugs or feature requests
