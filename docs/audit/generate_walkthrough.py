"""Generate how-it-works.html — a feature-by-feature walkthrough of Skills Curator
with honest token accounting per feature.

Pure inline CSS + SVG. No CDNs. Single file.

Usage:
  python docs/audit/generate_walkthrough.py
"""
import sys, io, json, html, argparse, re
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="in_path",  default=str(HERE / "audit_results.json"))
    ap.add_argument("--out", dest="out_path", default=str(HERE.parent / "how-it-works.html"))
    args = ap.parse_args()

    DATA = json.load(open(args.in_path, encoding="utf-8"))
    OUT  = Path(args.out_path)

    # Helper: get largest stdout for a verb across all projects
    def verb_max(v):
        return max((DATA["verbs"][p].get(v, {}).get("tokens", 0) for p in DATA["verbs"]), default=0)
    def verb_min(v):
        return min((DATA["verbs"][p].get(v, {}).get("tokens", 0) for p in DATA["verbs"]), default=0)

    # ------------------------------------------------------------------
    # Feature catalog: every command, with honest accounting
    # ------------------------------------------------------------------
    # Each row: (command, headline, what-it-does, what-it-reads, where-reads-happen,
    #            what-enters-context, pain-point, verb-key-in-audit-or-None)
    FEATURES = [
        ("--auto", "Proactive project scan",
         "Fingerprints the project. Re-scans only when something changes (new dep, edited CLAUDE.md). Surfaces top 3 picks if drift detected, otherwise prints a one-line 'no changes' marker.",
         "CLAUDE.md, README.md, package.json, requirements.txt, pyproject.toml, Pipfile, go.mod, Cargo.toml — each capped at 4 KB. Plus rglob counts of .py/.js/.ts/etc. for language tally.",
         "Subprocess (Python). Never in context.",
         "Top 3 picks if drift, or one-line 'no changes since {date}'. " ,
         "User keeps re-evaluating skills every session and forgetting prior picks. --auto is cheap to run on every session; it stays silent when nothing changed.",
         "--auto"),
        ("--symptoms <phrase>", "Pain point → skill mapping",
         "User describes a complaint ('tests are slow', 'ugly UI', 'deploys are manual'). The engine substring-matches against 17 hand-tuned patterns and surfaces catalog entries tagged with the matched categories.",
         "Just the user's phrase. No project read. No network. Pattern table is built into the script.",
         "Subprocess (Python). String matching only.",
         "List of catalog matches with tags (~30-190 tokens depending on match count).",
         "User says 'X is slow' or 'I wish I had Y' instead of naming a skill. Without this, the agent has to guess what category the complaint maps to.",
         "--symptoms 'slow tests'"),
        ("--recommend", "Project-aware ranking",
         "Full project scan, ranks catalog entries by (tag-overlap × 10) + (trust-tier bonus). Splits into Capability Uplift vs Encoded Preference. Surfaces top N with pros/cons and per-section customization hints.",
         "Same as --auto (project signals). Plus the catalog (cached at ~/.claude/skills/skills-curator/catalog.json, 24h TTL).",
         "Subprocess (Python). Catalog read from disk cache, not network unless TTL expired.",
         "Ranked list with name, why-it-fits, trust tier, install command, optional customization hint.",
         "Need a 'what skills fit here?' answer without manually scanning the catalog and reasoning about every entry.",
         "--recommend"),
        ("--scan", "Show project signals only",
         "Runs the same project scanner but prints the extracted tags + languages instead of recommending. Useful when you want to see what the engine 'sees' before trusting its picks.",
         "Same as --auto.",
         "Subprocess.",
         "Tag list, language counts, existing-skills inventory (~90-130 tokens).",
         "Debugging — when --recommend surfaces an unexpected pick, --scan shows whether the tag extraction is correct.",
         "--scan"),
        ("--customize <source>", "Fork an external skill, rewrite for this project",
         "Resolves the source (registered id, local path, or owner/repo@skill). Reads the SKILL.md. Splits it into sections. Scores each section against the project's tag set + languages. Emits a per-section action plan (keep / keep-trim / rewrite-stack / drop-or-rewrite / rewrite-frontmatter). Optionally writes a fork file at ~/.claude/skills/<name>-for-<project>/SKILL.md with the plan baked in.",
         "Source SKILL.md (~10 KB typical), project signals (~4 KB capped per doc).",
         "Subprocess. Source fetch can be local file, registered install path, or https://raw.githubusercontent.com/... — all in Python memory.",
         "Per-section action plan as a table (~900 tokens). Optionally writes a 1.5 KB fork file to disk (not in context).",
         "Most skills ship with examples from someone else's stack. Without --customize, adopting them means tolerating the mismatch or rewriting by hand without a plan.",
         "--customize skills-curator --no-fork"),
        ("--check <path>", "Security scan a skill folder",
         "rglob's every file in the folder, reads .py/.sh/.js/.ts/.md/.yaml/.yml/.json files, regex-matches against 15 patterns covering: remote curl/wget pipes, rm -rf, eval()/exec(), hardcoded API keys, suspected exfiltration endpoints, base64 decode, dynamic imports, keychain access. Categorizes as CRITICAL / HIGH / MEDIUM.",
         "Every text file in the target folder.",
         "Subprocess (Python regex). All file reads in Python memory.",
         "Findings count per severity + relative paths of offending files (~50 tokens for clean, more if findings).",
         "Installing community skills is risky — they can contain malicious eval(), hardcoded keys, or curl|bash patterns. Without this, the agent would need to read every file itself to spot risks (5-50 KB into context per skill).",
         "--check (skill folder)"),
        ("--audit", "Find duplicates, conflicts, security gaps",
         "Cross-references the registry to find: skills with overlapping tags (potential duplicates), preference conflicts between encoded-preference skills, skills missing a security review, skills with no evaluation history, and stale entries (>180 days since last touch).",
         "The registry file (~/.claude/skills/skills-curator/registry.json).",
         "Subprocess.",
         "Categorized list of issues per skill (~100-205 tokens).",
         "Skill installs accrete; nobody cleans them up. --audit surfaces the cruft.",
         "--audit"),
        ("--migrate <agent[,agent...]>", "Copy installed skills to other agent platforms",
         "Looks up the target platform's skill folder location (from a 55-entry platforms catalog mirrored from vercel-labs/skills) and copies each installed skill there. Skips existing destinations to avoid clobbering. Targets accept a single id, a comma list, or 'detected' (every platform on this machine).",
         "~/.claude/skills/ (source) and the target's skill folder (e.g., ~/.cursor/skills/).",
         "Subprocess. File copy via shutil.",
         "Per-skill copy log (one line each).",
         "Skills tied to one agent. Without migrate, copying to Cursor/Codex/Roo means manually figuring out each agent's skill folder convention.",
         None),
        ("--platforms [--verbose]", "List supported agent platforms",
         "Renders the 55-entry platforms catalog with detection status (which are installed on this machine).",
         "Platforms catalog (built into the script) + filesystem checks for each platform's marker directory.",
         "Subprocess.",
         "Table of platforms with name, detection status, install path. ~176 tokens compact, ~774 tokens verbose.",
         "Knowing which agents Skills Curator can target without grepping source code.",
         "--platforms"),
        ("--list / --history / --search", "Registry queries",
         "List all registered skills, show evaluation history for a specific skill, or full-text search the registry.",
         "Registry file only.",
         "Subprocess.",
         "Tabular output (~7-205 tokens depending on registry size).",
         "Re-evaluating a skill you already evaluated is waste. --history surfaces the prior verdict.",
         "--history skills-curator"),
        ("--find / --discover [term]", "Catalog search",
         "Free-text search of the cached catalog (curated entries + GitHub topic results). Filters by tag, name, or description.",
         "Catalog cache.",
         "Subprocess.",
         "Ranked matches (~114-157 tokens typical).",
         "Finding skills you might want when you don't yet have a project context.",
         "--find testing"),
        ("--health / --stale / --validate", "Registry hygiene",
         "Score each installed skill (0-100) based on: has evaluation, security-reviewed, has description, has tags, etc. --stale flags entries >180 days. --validate checks schema integrity.",
         "Registry file.",
         "Subprocess.",
         "Per-skill score list (~7-233 tokens).",
         "Catching skills that drift out of compliance silently.",
         "--health"),
        ("/skill-evaluate <id>", "Pre-install verdict with full evidence",
         "Slash command. Runs --check (security scan), then reads CLAUDE.md, then produces a structured verdict: ADOPT / PARTIAL / SKIP with pros, cons, conflicts, and a partial-adoption plan. Persisted to registry. Markdown artifact emittable via --export-eval.",
         "Target skill folder + project's CLAUDE.md.",
         "Subprocess for the security scan; agent then synthesizes the verdict prose.",
         "Verdict block (~800 tokens typical).",
         "Without this, evaluating a skill is ad-hoc — re-decided every conversation, no persistent record.",
         None),
        ("/skill-recommend", "Slash wrapper for --recommend",
         "Same as --recommend but invokable as a Claude Code slash command.", "—", "Subprocess.", "Same as --recommend.", "Same as --recommend.", None),
        ("/skill-audit", "Slash wrapper for --audit",
         "Same as --audit but invokable as a Claude Code slash command.", "—", "Subprocess.", "Same as --audit.", "Same as --audit.", None),
    ]

    # 17 symptom patterns (from registry.py)
    SYMPTOM_PATTERNS = [
        ('"slow test", "tests are slow", "test suite slow"',  '`testing`, `performance`, `test-performance`'),
        ('"flaky test", "tests fail random"',                  '`testing`, `test-stability`'),
        ('"no test", "untested", "missing tests"',             '`testing`, `test-coverage`, `unit-test`'),
        ('"failing ci", "ci is broken", "broken pipeline"',    '`ci-cd`, `github-actions`'),
        ('"ugly ui", "messy ui", "design is bad", "looks bad"','`frontend-design`, `design-system`, `ui`'),
        ('"manual deploy", "deploying by hand"',               '`ci-cd`, `deploy`, `release-automation`'),
        ('"no docs", "missing docs", "outdated docs"',         '`docs`, `docgen`, `readme-builder`'),
        ('"messy commits", "bad commit messages"',             '`commit-writer`, `conventional-commits`'),
        ('"slow build", "build is slow"',                      '`build-tools`, `performance`, `vite`'),
        ('"auth broken", "session bug", "login issue"',        '`auth`, `session-management`'),
        ('"scraping broken", "can\'t scrape", "browser auth"', '`scraping`, `browser-automation`'),
        ('"memory leak", "out of memory", "oom"',              '`performance`, `profiling`'),
        ('"slow api", "endpoint is slow"',                     '`performance`, `api`, `profiling`'),
        ('"hard to refactor", "spaghetti code"',               '`refactor`, `code-quality`'),
        ('"pr review takes", "review takes forever"',          '`pr-review`, `code-review`'),
        ('"changelog", "release notes"',                       '`changelog`, `release-notes`'),
        ('"accessibility", "a11y"',                            '`accessibility`, `ui`'),
    ]

    # 15 security patterns (from registry.py)
    SECURITY_PATTERNS = [
        ("`curl ... | bash`",                  "CRITICAL", "Remote code execution via curl pipe"),
        ("`wget ... | bash`",                  "CRITICAL", "Remote code execution via wget pipe"),
        ("`rm -rf /` or `rm -rf ~`",           "CRITICAL", "Destructive recursive delete"),
        ("`eval(...)`",                        "CRITICAL", "Dynamic code execution (CWE-95)"),
        ("`exec(...)`",                        "HIGH",     "Code execution function"),
        ("`OPENAI_API_KEY = \"sk-...\"`",      "CRITICAL", "Hardcoded OpenAI key"),
        ("`ANTHROPIC_API_KEY = \"sk-...\"`",   "CRITICAL", "Hardcoded Anthropic key"),
        ("`ghp_...` (36 chars)",               "CRITICAL", "Hardcoded GitHub PAT"),
        ("`password = \"literal\"`",           "HIGH",     "Hardcoded password"),
        ("`https://.../exfil`",                "CRITICAL", "Suspected data exfiltration endpoint"),
        ("`subprocess.call(...)` / `os.system(...)`","MEDIUM","Shell execution — review"),
        ("`requests.post(...secret...)`",      "MEDIUM",   "POST with sensitive token"),
        ("`__import__(...)`",                  "HIGH",     "Dynamic import — obfuscation risk"),
        ("`base64.b64decode`",                 "MEDIUM",   "Base64 decode — check payload"),
        ("`keychain` / `credentials store`",   "MEDIUM",   "OS credential store access"),
    ]

    # 31 framework signals (from FRAMEWORK_SIGNALS dict)
    FRAMEWORK_SIGNALS_SAMPLE = [
        ("`next` (in package.json/CLAUDE.md)", "`nextjs`, `react`, `frontend`"),
        ("`react`",                            "`react`, `frontend`"),
        ("`vue`",                              "`vue`, `frontend`"),
        ("`tailwind`",                         "`tailwind`, `css`, `frontend`"),
        ("`fastapi`",                          "`fastapi`, `python`, `backend`, `api`"),
        ("`django`",                           "`django`, `python`, `backend`, `web`"),
        ("`prisma`",                           "`prisma`, `database`, `orm`"),
        ("`playwright`",                       "`playwright`, `testing`, `browser`"),
        ("`jest` / `vitest`",                  "`jest`, `testing` / `vitest`, `testing`"),
        ("`langchain` / `openai` / `anthropic`",     "`ai`, `llm`"),
        ("`stripe`",                           "`stripe`, `payments`"),
        ("`aws` / `gcp` / `azure`",            "`cloud`"),
        ("`postgres` / `mongodb` / `redis`",   "`database`"),
        ("`remotion`",                         "`remotion`, `video`, `animation`"),
        ("`expo`",                             "`expo`, `react-native`, `mobile`"),
    ]

    # ------------------------------------------------------------------
    # SVG architecture diagram
    # ------------------------------------------------------------------
    arch_svg = '''
    <svg viewBox="0 0 760 360" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;font-family:ui-sans-serif,system-ui,sans-serif">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#7c3aed"/>
        </marker>
        <marker id="arrow-grey" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
          <path d="M0,0 L0,6 L9,3 z" fill="#9ca3af"/>
        </marker>
      </defs>

      <!-- Claude (context window) -->
      <rect x="20" y="40" width="200" height="280" fill="#f5f3ff" stroke="#7c3aed" stroke-width="2" rx="14"/>
      <text x="120" y="62" text-anchor="middle" font-weight="700" font-size="14" fill="#5b21b6">Claude's context</text>
      <text x="120" y="80" text-anchor="middle" font-size="11" fill="#7c3aed">(the only thing that costs tokens)</text>
      <rect x="40" y="100" width="160" height="34" fill="white" stroke="#c4b5fd" rx="6"/>
      <text x="120" y="120" text-anchor="middle" font-size="12" fill="#374151">SKILL.md (on activation)</text>
      <text x="120" y="132" text-anchor="middle" font-size="10" fill="#6b7280">3,359 tokens</text>
      <rect x="40" y="148" width="160" height="34" fill="white" stroke="#c4b5fd" rx="6"/>
      <text x="120" y="168" text-anchor="middle" font-size="12" fill="#374151">Description (always-on)</text>
      <text x="120" y="180" text-anchor="middle" font-size="10" fill="#6b7280">249 tokens combined</text>
      <rect x="40" y="196" width="160" height="34" fill="white" stroke="#c4b5fd" rx="6"/>
      <text x="120" y="216" text-anchor="middle" font-size="12" fill="#374151">Subprocess stdout</text>
      <text x="120" y="228" text-anchor="middle" font-size="10" fill="#6b7280">10-1,200 tokens / call</text>
      <rect x="40" y="244" width="160" height="34" fill="white" stroke="#c4b5fd" rx="6"/>
      <text x="120" y="264" text-anchor="middle" font-size="12" fill="#374151">Agent's own Read/Glob</text>
      <text x="120" y="276" text-anchor="middle" font-size="10" fill="#6b7280">(if SKILL.md asks)</text>

      <!-- Engine (subprocess) -->
      <rect x="280" y="40" width="220" height="200" fill="#ecfdf5" stroke="#16a34a" stroke-width="2" rx="14"/>
      <text x="390" y="62" text-anchor="middle" font-weight="700" font-size="14" fill="#15803d">registry.py subprocess</text>
      <text x="390" y="80" text-anchor="middle" font-size="11" fill="#16a34a">(runs in Python — 0 tokens)</text>
      <text x="390" y="110" text-anchor="middle" font-size="12" fill="#374151">27,900 token source file</text>
      <text x="390" y="128" text-anchor="middle" font-size="12" fill="#374151">never enters context</text>
      <rect x="300" y="148" width="180" height="22" fill="white" stroke="#86efac" rx="4"/>
      <text x="390" y="163" text-anchor="middle" font-size="11" fill="#15803d">_scan_project()</text>
      <rect x="300" y="174" width="180" height="22" fill="white" stroke="#86efac" rx="4"/>
      <text x="390" y="189" text-anchor="middle" font-size="11" fill="#15803d">_fetch_github_topics()</text>
      <rect x="300" y="200" width="180" height="22" fill="white" stroke="#86efac" rx="4"/>
      <text x="390" y="215" text-anchor="middle" font-size="11" fill="#15803d">_read_external_skill()</text>

      <!-- External resources -->
      <rect x="560" y="40" width="180" height="60" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5" rx="10"/>
      <text x="650" y="62" text-anchor="middle" font-weight="600" font-size="12" fill="#92400e">Project files</text>
      <text x="650" y="80" text-anchor="middle" font-size="10" fill="#b45309">CLAUDE.md, package.json,</text>
      <text x="650" y="93" text-anchor="middle" font-size="10" fill="#b45309">requirements.txt, ... (capped 4KB)</text>

      <rect x="560" y="118" width="180" height="60" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5" rx="10"/>
      <text x="650" y="140" text-anchor="middle" font-weight="600" font-size="12" fill="#92400e">GitHub API</text>
      <text x="650" y="158" text-anchor="middle" font-size="10" fill="#b45309">topic:claude-skill, etc.</text>
      <text x="650" y="171" text-anchor="middle" font-size="10" fill="#b45309">cached 24h</text>

      <rect x="560" y="196" width="180" height="60" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5" rx="10"/>
      <text x="650" y="218" text-anchor="middle" font-weight="600" font-size="12" fill="#92400e">Registry + catalog</text>
      <text x="650" y="236" text-anchor="middle" font-size="10" fill="#b45309">~/.claude/skills/...</text>
      <text x="650" y="249" text-anchor="middle" font-size="10" fill="#b45309">JSON on disk</text>

      <!-- Arrows -->
      <!-- Claude → subprocess (Bash) -->
      <line x1="225" y1="213" x2="275" y2="140" stroke="#7c3aed" stroke-width="2" marker-end="url(#arrow)"/>
      <text x="230" y="174" font-size="10" fill="#7c3aed">Bash exec</text>

      <!-- subprocess → external -->
      <line x1="505" y1="70" x2="555" y2="70" stroke="#9ca3af" stroke-width="1.5" marker-end="url(#arrow-grey)"/>
      <line x1="505" y1="148" x2="555" y2="148" stroke="#9ca3af" stroke-width="1.5" marker-end="url(#arrow-grey)"/>
      <line x1="505" y1="225" x2="555" y2="225" stroke="#9ca3af" stroke-width="1.5" marker-end="url(#arrow-grey)"/>
      <text x="510" y="58" font-size="10" fill="#6b7280">read</text>

      <!-- subprocess → Claude (stdout) -->
      <line x1="275" y1="170" x2="225" y2="213" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow)"/>
      <text x="240" y="200" font-size="10" fill="#15803d">stdout only</text>

      <!-- Legend -->
      <text x="20" y="345" font-size="11" font-weight="600" fill="#374151">Token cost happens only inside the purple box. Everything in the green and yellow boxes is free.</text>
    </svg>
    '''

    # ------------------------------------------------------------------
    # Build the feature table
    # ------------------------------------------------------------------
    feat_rows = []
    for cmd, headline, what, reads, where, ctx, pain, key in FEATURES:
        cost_cell = ""
        if key and key in DATA["verbs"]["Empty"]:
            mn, mx = verb_min(key), verb_max(key)
            cost_cell = f"<strong>{mn:,}-{mx:,}</strong> tokens" if mn != mx else f"<strong>{mn:,}</strong> tokens"
        else:
            cost_cell = "varies (see notes)"
        feat_rows.append(f"""
        <details class="feature">
          <summary>
            <code>{html.escape(cmd)}</code>
            <span class="feat-headline">{html.escape(headline)}</span>
            <span class="feat-cost">{cost_cell}</span>
          </summary>
          <div class="feat-body">
            <p><strong>What it does:</strong> {html.escape(what)}</p>
            <p><strong>What it reads:</strong> {html.escape(reads)}</p>
            <p><strong>Where reads happen:</strong> {html.escape(where)}</p>
            <p><strong>What enters Claude's context:</strong> {html.escape(ctx)}</p>
            <p><strong>Pain point it solves:</strong> {html.escape(pain)}</p>
          </div>
        </details>""")

    symp_rows = "\n".join(
        f"<tr><td>{p}</td><td>{t}</td></tr>" for p, t in SYMPTOM_PATTERNS
    )
    sec_rows = "\n".join(
        f"<tr><td>{pat}</td><td><span class='sev sev-{sev.lower()}'>{sev}</span></td><td>{desc}</td></tr>"
        for pat, sev, desc in SECURITY_PATTERNS
    )
    fw_rows = "\n".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in FRAMEWORK_SIGNALS_SAMPLE
    )

    # ------------------------------------------------------------------
    # Compose page
    # ------------------------------------------------------------------
    PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skills Curator — How It Works</title>
<meta name="description" content="Feature-by-feature walkthrough of Skills Curator with honest token accounting for every command.">
<style>
  :root {{
    --bg: #fafaf9; --fg: #18181b; --muted: #71717a; --line: #e4e4e7;
    --card: #ffffff; --accent: #7c3aed; --accent-soft: #f5f3ff;
    --good: #16a34a; --bad: #ef4444;
  }}
  *,*::before,*::after {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--fg);
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6; font-size: 16px; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 24px; }}
  h1, h2, h3 {{ line-height: 1.2; letter-spacing: -0.01em; }}
  h1 {{ font-size: 2.1rem; margin: 0 0 8px; }}
  h2 {{ font-size: 1.45rem; margin: 44px 0 8px; padding-top: 12px;
    border-top: 1px solid var(--line); }}
  h3 {{ font-size: 1.08rem; margin: 22px 0 8px; }}
  p {{ margin: 0 0 12px; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  code {{ font-family: ui-monospace, "SF Mono", Consolas, monospace; font-size: 0.92em;
    background: var(--accent-soft); padding: 2px 5px; border-radius: 4px; color: #5b21b6; }}
  pre {{ background: var(--accent-soft); padding: 14px; border-radius: 8px; overflow-x: auto;
    border: 1px solid var(--line); }}
  pre code {{ background: transparent; padding: 0; }}
  .hero {{ background: linear-gradient(135deg, #06b6d4 0%, #7c3aed 100%);
    color: white; padding: 32px 28px; border-radius: 16px; margin-bottom: 26px;
    box-shadow: 0 8px 32px rgba(124,58,237,0.18); }}
  .hero h1 {{ color: white; margin-top: 6px; }}
  .hero .tagline {{ font-size: 1.04rem; opacity: 0.92; margin: 4px 0 12px; }}
  .pill {{ display: inline-block; padding: 3px 10px; background: rgba(255,255,255,0.18);
    color: white; border-radius: 999px; font-size: 0.78rem; font-weight: 600; letter-spacing: 0.02em; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 0.92rem; }}
  th, td {{ text-align: left; padding: 9px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ background: var(--accent-soft); font-weight: 600; color: #3f3f46; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .glossary {{ display: grid; grid-template-columns: 180px 1fr; gap: 14px 24px; margin: 14px 0; }}
  .glossary dt {{ font-weight: 600; color: #5b21b6; }}
  .glossary dd {{ margin: 0; color: #3f3f46; }}
  .callout {{ background: #ecfdf5; border-left: 4px solid var(--good); padding: 14px 16px;
    border-radius: 8px; margin: 14px 0; }}
  .callout.warn {{ background: #fffbeb; border-left-color: #f59e0b; }}
  .callout.bad {{ background: #fef2f2; border-left-color: var(--bad); }}
  .feature {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    margin: 10px 0; transition: all 0.15s; overflow: hidden; }}
  .feature[open] {{ border-color: var(--accent); box-shadow: 0 4px 16px rgba(124,58,237,0.08); }}
  .feature summary {{ list-style: none; cursor: pointer; padding: 12px 16px; display: grid;
    grid-template-columns: minmax(180px,auto) 1fr auto; gap: 14px; align-items: center; }}
  .feature summary::-webkit-details-marker {{ display: none; }}
  .feature summary::before {{ content: "▸"; color: var(--accent); margin-right: 4px;
    transition: transform 0.15s; display: inline-block; }}
  .feature[open] summary::before {{ transform: rotate(90deg); }}
  .feat-headline {{ color: #3f3f46; font-weight: 500; }}
  .feat-cost {{ font-family: ui-monospace, "SF Mono", monospace; font-size: 0.82rem;
    background: var(--accent-soft); color: #5b21b6; padding: 3px 10px; border-radius: 999px; }}
  .feat-body {{ padding: 0 16px 16px 30px; color: #3f3f46; }}
  .feat-body p {{ margin: 6px 0; }}
  .sev {{ font-weight: 700; font-size: 0.78rem; padding: 2px 8px; border-radius: 4px;
    text-transform: uppercase; letter-spacing: 0.04em; }}
  .sev-critical {{ background: #fee2e2; color: #991b1b; }}
  .sev-high {{ background: #fed7aa; color: #9a3412; }}
  .sev-medium {{ background: #fef3c7; color: #854d0e; }}
  .crosslink {{ display: inline-block; margin: 20px 0; padding: 8px 14px;
    background: var(--accent-soft); border-radius: 8px; color: #5b21b6; font-weight: 600; }}
  footer {{ margin-top: 56px; padding-top: 20px; border-top: 1px solid var(--line);
    color: var(--muted); font-size: 0.86rem; }}
  @media (max-width: 640px) {{
    main {{ padding: 16px; }}
    .glossary {{ grid-template-columns: 1fr; gap: 4px; }}
    .glossary dt {{ margin-top: 8px; }}
    .feature summary {{ grid-template-columns: 1fr; gap: 4px; }}
    .feat-cost {{ justify-self: start; }}
    .hero {{ padding: 22px 18px; }}
    h1 {{ font-size: 1.7rem; }}
    table {{ font-size: 0.82rem; }}
  }}
</style>
</head>
<body>
<main>

<section class="hero">
  <span class="pill">Feature walkthrough</span>
  <h1>How Skills Curator actually works</h1>
  <p class="tagline">Every command, what it reads, where reads happen, and what enters Claude's context. The conceptual model behind the bounded token cost.</p>
  <p style="margin:0;opacity:0.9"><a href="token-cost-report.html" style="color:white;text-decoration:underline">← Back to the token cost report</a></p>
</section>

<h2>The most important concept (and the most-missed)</h2>
<p>
  There are two completely different ways code can "read" a file in a Claude Code session,
  and they have <strong>opposite</strong> token implications:
</p>
<ol>
  <li><strong>Claude reads the file itself</strong> (via the <code>Read</code>, <code>Glob</code>, <code>Grep</code> tools). Every byte enters Claude's context window. A 20 KB CLAUDE.md = ~5,000 tokens consumed.</li>
  <li><strong>A subprocess reads the file</strong>. The bytes go into the <em>subprocess's</em> memory (Python's RAM), get processed, and the subprocess returns only its <code>stdout</code> to Claude. Claude sees nothing but the stdout.</li>
</ol>
<p>
  Skills Curator is built entirely around mechanism #2. When <code>--auto</code> runs, here's
  what physically happens:
</p>
<pre><code>Python process starts
  → reads CLAUDE.md (capped at 4 KB), package.json, requirements.txt, etc. into its own RAM
  → parses, extracts framework tags ("nextjs", "react", "testing")
  → matches tags against the catalog
  → prints ~250 tokens of structured output to stdout
Python process exits, RAM freed
  → Claude sees ONLY those 250 tokens</code></pre>

<div class="callout">
  <strong>This is the whole reason a 17,680-file project costs the same as a 30-file folder.</strong>
  The engine is a magnifying glass: sees a lot, reports a little. Project bytes never enter context.
</div>

<h2>Architecture</h2>
<div class="card" style="background:white;border:1px solid var(--line);border-radius:12px;padding:20px;margin:14px 0">
{arch_svg}
</div>

<h2>Glossary</h2>
<dl class="glossary">
  <dt>Command (a.k.a. "verb")</dt>
  <dd>A CLI flag that tells the engine what action to perform. <code>--auto</code>, <code>--recommend</code>, <code>--customize</code>, <code>--check</code> — these are commands. In the earlier report I called them "verbs" (CLI-design jargon — <code>git commit</code>: <code>commit</code> is a verb). Same thing; "command" is clearer.</dd>

  <dt>Tier</dt>
  <dd>Two implementations of the same skill ship in the plugin:<br>
    <strong>Python tier</strong> — heavy lifting in <code>registry.py</code> (2,272 lines, 27,900 tokens of source). Faster on 100+ skills, regression-tested.<br>
    <strong>Lite tier</strong> — pure-markdown SKILL.md (~11,000 tokens) that instructs the agent to do everything with <code>Bash</code>, <code>Read</code>, <code>Glob</code>, <code>Grep</code>, <code>Write</code>. No Python needed.</dd>

  <dt>Subprocess</dt>
  <dd>A separate process started by Claude via the <code>Bash</code> tool. Runs Python independently, has its own memory, returns only stdout/stderr/exit-code to the parent. Anything inside the subprocess is invisible to Claude's context window.</dd>

  <dt>Engine vs Agent</dt>
  <dd><strong>Engine</strong> = the Python script (<code>registry.py</code>). Deterministic logic — file I/O, regex matching, JSON parsing.<br>
    <strong>Agent</strong> = Claude itself. Reads SKILL.md, decides which engine command to run, interprets results, talks to the user.</dd>

  <dt>Always-on cost</dt>
  <dd>What loads into context at <em>every</em> session start, regardless of whether the skill activates. For Skills Curator, that's just the frontmatter <code>description</code> field of both tiers (249 tokens combined).</dd>

  <dt>Activation cost</dt>
  <dd>What loads when the skill is invoked. The full <code>SKILL.md</code> body. Pays once per session.</dd>

  <dt>Catalog</dt>
  <dd>The list of known skills. Combination of: 19 hand-curated entries (in source) + ~60 community skills discovered via GitHub topic search (cached 24h). Used for recommendations and search.</dd>

  <dt>Trust tier</dt>
  <dd>Skill source classification: 🏛️ official (Anthropic / Vercel / Microsoft / Google), ✅ high (established orgs like ComposioHQ / Firecrawl), 🟡 medium, ⬜ community, ❓ unknown. Used to gate recommendations — unknown-author skills require a security scan before being surfaced.</dd>

  <dt>Verdict</dt>
  <dd>The output of <code>/skill-evaluate</code>: one of <code>ADOPT</code>, <code>PARTIAL</code> (adopt parts, skip parts), or <code>SKIP</code>. Persisted to <code>~/.claude/skills/skills-curator/registry.json</code> so the same skill is never re-evaluated.</dd>

  <dt>Fingerprint</dt>
  <dd>A short hash derived from the project's key files (CLAUDE.md byte count + prefix, dependencies, etc.). <code>--auto</code> uses it to detect "has the project changed since last scan?" — if not, --auto exits in ~30 tokens without doing any work.</dd>
</dl>

<h2>External skills research — how new skills are discovered</h2>
<p>
  Three layers of catalog:
</p>
<h3>Layer 1: Curated catalog (built into the script)</h3>
<p>
  19 hand-picked skills with pre-written pros/cons, tags, install commands, and trust tiers.
  Lives inside <code>registry.py</code> — zero network cost, always available.
</p>

<h3>Layer 2: GitHub topic search (live, cached 24h)</h3>
<p>
  Once per day, the engine hits the GitHub Search API:
</p>
<pre><code>GET api.github.com/search/repositories?q=topic:claude-skill&amp;sort=stars
GET api.github.com/search/repositories?q=topic:claude-code-skill&amp;sort=stars
GET api.github.com/search/repositories?q=topic:agent-skill&amp;sort=stars</code></pre>
<p>
  Each returns ~20 repos. Engine collects <strong>just the metadata</strong> — repo name, owner,
  stars, short description. <strong>SKILL.md bodies are NOT fetched here.</strong> Authors are
  classified into trust tiers via the <code>_TRUSTED_AUTHORS</code> dict:
</p>
<pre><code>anthropics / vercel-labs / microsoft / google     → 🏛️ official
ComposioHQ / supermemoryai / remotion-dev / firecrawl → ✅ high
obra                                              → 🟡 medium
others                                            → ⬜ community / ❓ unknown</code></pre>
<p>
  Cached at <code>~/.claude/skills/skills-curator/catalog.json</code> with a 24-hour TTL. Set
  <code>SKILLS_NO_TELEMETRY=1</code> to disable all outbound calls.
</p>

<h3>Layer 3: On-demand SKILL.md fetch</h3>
<p>
  Only happens when the user runs <code>--check</code>, <code>--customize</code>, or
  <code>/skill-evaluate</code> on a specific candidate. The <code>_read_external_skill()</code>
  function tries (in order):
</p>
<ol>
  <li>Local path on disk</li>
  <li>Registered install path under <code>~/.claude/skills/</code></li>
  <li><code>owner/repo[@skill-name]</code> → fetches <code>raw.githubusercontent.com/.../SKILL.md</code></li>
</ol>
<p>
  All reads happen in subprocess memory. The SKILL.md bytes never enter Claude's context;
  only the analysis result (security findings, customization plan, verdict) does.
</p>

<h2>How project signals get turned into tags</h2>
<p>
  Two pattern tables convert raw project content into the tags the engine uses for matching.
</p>
<h3>Framework signals (sample of 31 keywords)</h3>
<p>
  The engine reads each of <code>package.json</code>, <code>requirements.txt</code>,
  <code>pyproject.toml</code>, <code>Pipfile</code> — and the first 4 KB of <code>CLAUDE.md</code>
  and <code>README.md</code>. Each keyword that appears emits one or more tags:
</p>
<table>
  <thead><tr><th>Keyword in file</th><th>Tags emitted</th></tr></thead>
  <tbody>{fw_rows}</tbody>
</table>

<h3>Goal signals (15 regex patterns)</h3>
<p>
  Run against CLAUDE.md/README.md content. Map general-purpose mentions
  ("dashboard", "scraping", "deploy", "auth", "ml") into broader tag categories
  for catalog matching.
</p>

<h2>Pain point discovery: <code>--symptoms</code></h2>
<p>
  When the user describes a complaint in chat instead of naming a skill,
  <code>--symptoms "&lt;phrase&gt;"</code> substring-matches against this hand-tuned table:
</p>
<table>
  <thead><tr><th>Phrase patterns (case-insensitive substring match)</th><th>Tags emitted</th></tr></thead>
  <tbody>{symp_rows}</tbody>
</table>
<p>
  17 entries — small enough to be hand-curated, large enough to catch what users actually say in
  chat. First-match-wins. The output is a list of catalog skills tagged with the matched
  categories, ranked by trust tier (~30-190 tokens of stdout).
</p>
<div class="callout">
  <strong>Why a hand-curated table and not ML / stemming?</strong> The phrasing of pain points
  is conversational and idiomatic ("deploys are manual", "my UI looks like shit"). Substring
  matching against curated triggers is more precise than embeddings and 10,000× cheaper to run
  (no model loaded, ~1 ms total).
</div>

<h2>Security scanning: what <code>--check</code> looks for</h2>
<p>
  15 regex patterns covering OWASP top-10-style risks. Files with extensions
  <code>.py .sh .js .ts .md .yaml .yml .json</code> are scanned; binary and lockfile contents
  are skipped. Lines marked <code>scanner:ignore</code> (or blocks bounded by
  <code>scanner:ignore-block-start</code>/<code>-end</code>) are stripped before pattern matching
  so the scanner doesn't flag its own pattern definitions.
</p>
<table>
  <thead><tr><th>Pattern</th><th>Severity</th><th>Description</th></tr></thead>
  <tbody>{sec_rows}</tbody>
</table>
<div class="callout warn">
  Without <code>--check</code>, evaluating a community skill means the agent has to read every
  file in the skill folder looking for risks — easily 5-50 KB of context per skill. With
  <code>--check</code>, the engine does the scanning and reports back ~50-200 tokens of
  findings.
</div>

<h2>Customization: the full pipeline with token accounting</h2>
<p>
  This is the headline command. Here's what happens, end-to-end, when you run
  <code>--customize vue-skill</code> on a React project — with honest token accounting at every
  step:
</p>
<table>
  <thead>
    <tr><th>Step</th><th>Where it happens</th><th>Bytes in subprocess RAM</th><th class="num">Tokens in Claude's context</th></tr>
  </thead>
  <tbody>
    <tr><td>Resolve source (local / registered / owner/repo@skill)</td><td>Subprocess</td><td>—</td><td class="num">0</td></tr>
    <tr><td>Fetch source <code>SKILL.md</code> from GitHub raw</td><td>Subprocess (urllib)</td><td>~10 KB</td><td class="num">0</td></tr>
    <tr><td>Scan project for tags (<code>_scan_project</code>)</td><td>Subprocess</td><td>up to ~20 KB capped</td><td class="num">0</td></tr>
    <tr><td>Split <code>SKILL.md</code> into sections by <code>## </code> headings</td><td>Subprocess</td><td>—</td><td class="num">0</td></tr>
    <tr><td>Score each section by tag-overlap and language match</td><td>Subprocess</td><td>—</td><td class="num">0</td></tr>
    <tr><td>Emit per-section action plan as stdout</td><td>Subprocess → stdout</td><td>—</td><td class="num"><strong>~900</strong></td></tr>
    <tr><td>Write fork file to disk (includes first 2 KB of original)</td><td>Subprocess → disk</td><td>~1.5 KB</td><td class="num">0</td></tr>
    <tr><td>Agent reads fork file with the plan baked in</td><td>Claude <code>Read</code></td><td>—</td><td class="num">~500</td></tr>
    <tr><td>Agent rewrites mismatched sections (Vue→React, etc.)</td><td>Claude output</td><td>—</td><td class="num">~2,000</td></tr>
    <tr><th colspan="3">Total context cost</th><th class="num">~3,400</th></tr>
  </tbody>
</table>
<p>
  Compare to doing the same task without the skill:
</p>
<table>
  <thead><tr><th>Step</th><th class="num">Tokens in context</th></tr></thead>
  <tbody>
    <tr><td>WebFetch the source SKILL.md</td><td class="num">~2,560</td></tr>
    <tr><td>Reason about every section from scratch (no structured plan)</td><td class="num">~3,000</td></tr>
    <tr><td>Rewrite mismatched sections</td><td class="num">~2,000</td></tr>
    <tr><th>Total context cost</th><th class="num">~7,560</th></tr>
  </tbody>
</table>
<p>
  <strong>Savings: ~4,160 tokens per customization (55%).</strong> And the agent gets a
  structured action plan instead of free-form reasoning, which dramatically reduces "meandering"
  errors.
</p>

<h2>Feature-by-feature breakdown</h2>
<p>
  Click any command to expand. The cost column shows the actual measured stdout range across
  the five test projects from the <a href="token-cost-report.html">token cost report</a>.
</p>

{''.join(feat_rows)}

<a href="token-cost-report.html" class="crosslink">📊 See full per-project measurements →</a>

<h2>Other questions you might have</h2>

<h3>Does the agent ever read project files itself?</h3>
<p>
  Yes, sometimes. SKILL.md instructs the agent: <em>"if the request is 'how do I do X?' and X
  is plausibly a skill domain, search the registry first"</em>. That's a subprocess call.
  But for <code>/skill-evaluate</code>, SKILL.md may direct the agent to read CLAUDE.md
  directly (using the <code>Read</code> tool) to assess project fit — those bytes DO enter
  context. That's a deliberate trade-off: a 4–5 KB CLAUDE.md is worth reading in full when
  producing a verdict, because the verdict is persistent. The subprocess can't do the
  judgment work; only Claude can.
</p>

<h3>Why is the Lite tier's SKILL.md so much bigger (10,988 vs 3,359 tokens)?</h3>
<p>
  The Python tier delegates work to <code>registry.py</code> (a 27,900-token subprocess). The
  Lite tier has no engine — the agent does the work using <code>Bash</code>, <code>Read</code>,
  <code>Glob</code>, <code>Grep</code>, <code>Write</code>. So the catalog, the 17 symptom
  patterns, the 15 security patterns, the 55-platform table, and the project-scanning
  instructions all have to live inline in the markdown. The trade-off: zero Python dependency,
  but ~3.5× larger activation cost.
</p>

<h3>What if I have 1,000 installed skills?</h3>
<p>
  <code>--audit</code>, <code>--health</code>, and <code>--list</code> output grows linearly
  with installed skill count. Practical guidance: at 100+ skills, prefer the Python tier
  (single-pass speed) over Lite (which would need many agent steps). The Python tier was
  regression-tested up to ~200 skills.
</p>

<h3>What stops a malicious skill from injecting prompts via its SKILL.md?</h3>
<p>
  <code>--check</code> regex-scans for known indicators of malicious code (curl|bash, hardcoded
  keys, eval/exec). It doesn't currently scan for prompt-injection patterns. The trust-tier gate
  is the second defense — unknown-author skills are flagged before surfacing.
</p>

<footer>
  Generated {DATA['generated_at']} · Skills Curator v4.4.4 · <a href="token-cost-report.html">Token Cost Report</a> · <a href="https://github.com/captkernel/Skills_Curator">github.com/captkernel/Skills_Curator</a>
</footer>

</main>
</body>
</html>"""

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(PAGE, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Size: {OUT.stat().st_size:,} bytes")

if __name__ == "__main__":
    main()
