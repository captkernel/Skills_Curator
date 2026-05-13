"""Deep token audit — measures Skills Curator's real context cost across:
  • Real projects of increasing size/complexity (configured via PROJECTS below)
  • Every verb in the engine
  • Both tiers (Python + Lite)
  • Three realistic session profiles

Output: ./audit_results.json (alongside this script). Feeds generate_html.py.

Usage:
  pip install tiktoken
  python docs/audit/deep_token_audit.py [--projects path1,path2,...]

Default test projects are configured at the top of this file. Override with
--projects to test against your own paths. All paths must exist.
"""

from __future__ import annotations
import sys, io, os, subprocess, json, time, re, argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

try:
    import tiktoken
except ImportError:
    sys.stderr.write("ERROR: tiktoken not installed. Run: pip install tiktoken\n")
    sys.exit(2)

enc = tiktoken.get_encoding("cl100k_base")

def tok(text: str) -> int:
    if not text:
        return 0
    return len(enc.encode(text))

def file_tok(p: Path) -> int:
    if not p.exists():
        return 0
    return tok(p.read_text(encoding="utf-8", errors="replace"))

# ----------------------------------------------------------------------
# Locate repo files (this script lives at <repo>/docs/audit/)
# ----------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
REG        = REPO / "skills" / "skills-curator" / "scripts" / "registry.py"
SKILL_FULL = REPO / "skills" / "skills-curator" / "SKILL.md"
SKILL_LITE = REPO / "skills" / "skills-curator-lite" / "SKILL.md"
REFS_DIR   = REPO / "skills" / "skills-curator" / "references"

# ----------------------------------------------------------------------
# Default test projects (override with --projects)
# Format: label|path|category|description
# ----------------------------------------------------------------------
DEFAULT_PROJECTS_SPEC = [
    # label, path-relative-or-absolute, category, description
    ("Empty",  r"D:\Karan\AFP",              "empty",  "Bare directory, 1 file, no signals"),
    ("Small",  r"D:\Karan\Business",         "small",  "Notes folder with CLAUDE.md, ~34 root files"),
    ("Medium", r"D:\VoiceTaskAI",            "medium", "React Native app, no CLAUDE.md, ~30 files"),
    ("Large",  r"D:\Karan\Ancyr",            "large",  "Next.js project, 20 KB CLAUDE.md, ~50 files"),
    ("XL",     str(REPO),                    "xl",     "Skills Curator's own repo: Python + skill files + tests + docs"),
]

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def run(args, cwd=None, timeout=60):
    full = [sys.executable, str(REG)] + args
    t0 = time.time()
    try:
        p = subprocess.run(full, cwd=str(cwd) if cwd else None,
                           capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace",
                           env={**os.environ,
                                "SKILLS_NO_TELEMETRY": "1",
                                "PYTHONIOENCODING": "utf-8"})
        return {"stdout": p.stdout or "", "stderr": p.stderr or "",
                "exit": p.returncode, "elapsed_ms": int((time.time() - t0) * 1000)}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "exit": -1, "elapsed_ms": timeout * 1000}
    except Exception as e:
        return {"stdout": "", "stderr": f"ERROR: {e}", "exit": -2, "elapsed_ms": 0}

def measure(args, cwd=None, timeout=60):
    r = run(args, cwd, timeout)
    r["tokens"] = tok(r["stdout"])
    r["chars"]  = len(r["stdout"])
    r["lines"]  = r["stdout"].count("\n")
    return r

# ----------------------------------------------------------------------
def fingerprint_project(path: Path) -> dict:
    fp = {"file_count": 0, "py_count": 0, "js_count": 0, "ts_count": 0,
          "claude_md_bytes": 0, "readme_bytes": 0, "pkg_json_bytes": 0,
          "total_bytes_top": 0, "has_claude_md": False, "has_pkg_json": False,
          "has_requirements": False, "has_pyproject": False}
    if not path.exists():
        return fp
    for ext in [".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".json", ".yml", ".yaml"]:
        try:
            cnt = sum(1 for _ in path.rglob(f"*{ext}"))
            fp["file_count"] += cnt
            if ext == ".py":  fp["py_count"] = cnt
            elif ext in (".js", ".jsx"): fp["js_count"] += cnt
            elif ext in (".ts", ".tsx"): fp["ts_count"] += cnt
        except Exception:
            pass
    cmd = path / "CLAUDE.md"
    if cmd.exists():
        fp["has_claude_md"] = True
        fp["claude_md_bytes"] = cmd.stat().st_size
    rdm = path / "README.md"
    if rdm.exists():
        fp["readme_bytes"] = rdm.stat().st_size
    pkg = path / "package.json"
    if pkg.exists():
        fp["has_pkg_json"] = True
        fp["pkg_json_bytes"] = pkg.stat().st_size
    if (path / "requirements.txt").exists():
        fp["has_requirements"] = True
    if (path / "pyproject.toml").exists():
        fp["has_pyproject"] = True
    try:
        for c in path.iterdir():
            if c.is_file():
                try: fp["total_bytes_top"] += c.stat().st_size
                except: pass
    except Exception:
        pass
    return fp

def measure_static():
    fm = lambda p: re.match(r"---.*?---", p.read_text(encoding="utf-8"), re.DOTALL).group(0) if p.exists() else ""
    desc_re = lambda txt: re.search(r"description:\s*[>|]?\s*([\s\S]+?)\n[a-z_]+:", txt)
    fm_full = fm(SKILL_FULL); fm_lite = fm(SKILL_LITE)
    desc_full = desc_re(fm_full).group(1).strip() if desc_re(fm_full) else ""
    desc_lite = desc_re(fm_lite).group(1).strip() if desc_re(fm_lite) else ""

    refs = {}
    for r in REFS_DIR.glob("*.md"):
        refs[r.name] = file_tok(r)

    return {
        "engine_py_tokens":  file_tok(REG),
        "skill_full_tokens": file_tok(SKILL_FULL),
        "skill_lite_tokens": file_tok(SKILL_LITE),
        "fm_full_tokens":    tok(fm_full),
        "fm_lite_tokens":    tok(fm_lite),
        "desc_full_tokens":  tok(desc_full),
        "desc_lite_tokens":  tok(desc_lite),
        "references":        refs,
        "references_total":  sum(refs.values()),
    }

def measure_verbs(project_path: Path):
    results = {}
    verbs = [
        ("--auto",                            ["--auto"]),
        ("--auto --refresh",                  ["--auto", "--refresh"]),
        ("--recommend",                       ["--recommend"]),
        ("--scan",                            ["--scan"]),
        ("--symptoms 'slow tests'",           ["--symptoms", "slow tests"]),
        ("--symptoms 'ugly UI'",              ["--symptoms", "ugly UI"]),
        ("--symptoms 'deploys are manual'",   ["--symptoms", "deploys are manual"]),
        ("--detect",                          ["--detect"]),
        ("--status",                          ["--status"]),
        ("--list",                            ["--list"]),
        ("--list --type capability",          ["--list", "--type", "capability"]),
        ("--search testing",                  ["--search", "testing"]),
        ("--platforms",                       ["--platforms"]),
        ("--platforms --verbose",             ["--platforms", "--verbose"]),
        ("--find testing",                    ["--find", "testing"]),
        ("--discover design",                 ["--discover", "design"]),
        ("--audit",                           ["--audit"]),
        ("--health",                          ["--health"]),
        ("--stale",                           ["--stale"]),
        ("--validate",                        ["--validate"]),
        ("--version",                         ["--version"]),
        ("--check (skill folder)",            ["--check", str(SKILL_FULL.parent)]),
        ("--history skills-curator",          ["--history", "skills-curator"]),
        ("--customize skills-curator --no-fork", ["--customize", "skills-curator", "--no-fork"]),
    ]
    for label, args in verbs:
        r = measure(args, cwd=project_path)
        results[label] = {
            "tokens":    r["tokens"],
            "chars":     r["chars"],
            "lines":     r["lines"],
            "exit":      r["exit"],
            "elapsed_ms": r["elapsed_ms"],
            "preview":   r["stdout"][:400].replace("\n", " ⏎ "),
        }
    return results

def compute_sessions(static_data, verb_results):
    desc_total = static_data["desc_full_tokens"] + static_data["desc_lite_tokens"]
    skill_full = static_data["skill_full_tokens"]
    out = {}
    for label, vresults in verb_results.items():
        get = lambda v: vresults.get(v, {}).get("tokens", 0)
        out[label] = {
            "A_silent_tokens":        desc_total,
            "B_light_tokens":         (
                desc_total + skill_full
                + get("--auto") + get("--recommend") + 800
            ),
            "C_heavy_tokens":         (
                desc_total + skill_full
                + get("--auto") + get("--recommend")
                + 800*3
                + get("--audit") + get("--check (skill folder)")
                + get("--customize skills-curator --no-fork")
            ),
            "without_skill_light":    4060,
            "without_skill_heavy":    4060*7,
        }
    return out

def main():
    ap = argparse.ArgumentParser(description="Deep token audit for Skills Curator")
    ap.add_argument("--projects", help="Comma-separated list of project paths to override defaults")
    ap.add_argument("--out", default=str(HERE / "audit_results.json"),
                    help="Output JSON path (default: audit_results.json beside this script)")
    args = ap.parse_args()

    if args.projects:
        projects = []
        for i, p in enumerate(args.projects.split(",")):
            p = p.strip()
            projects.append((f"P{i+1}", p, "custom", f"User-supplied project: {p}"))
    else:
        projects = DEFAULT_PROJECTS_SPEC

    print("=" * 78)
    print("DEEP TOKEN AUDIT — Skills Curator")
    print("=" * 78)

    print("\n[1/4] Static measurements (what loads independent of project)...")
    static_data = measure_static()
    print(f"   SKILL.md (Python): {static_data['skill_full_tokens']:,} tokens")
    print(f"   SKILL.md (Lite):   {static_data['skill_lite_tokens']:,} tokens")
    print(f"   Engine (subprocess, not in context): {static_data['engine_py_tokens']:,} tokens")

    print("\n[2/4] Fingerprinting projects...")
    project_data = {}
    for label, raw_path, cat, desc in projects:
        path = Path(raw_path)
        fp = fingerprint_project(path)
        project_data[label] = {"path": str(path), "category": cat,
                                "description": desc, "fingerprint": fp}
        present = "✓" if path.exists() else "✗ MISSING"
        print(f"   [{present}] {label:<8} {path}: files={fp['file_count']:>5} "
              f"CLAUDE.md={fp['claude_md_bytes']:>5}B  pkg.json={'Y' if fp['has_pkg_json'] else 'N'}")

    print("\n[3/4] Running every verb against every present project...")
    all_verb_results = {}
    for label, raw_path, cat, desc in projects:
        path = Path(raw_path)
        if not path.exists():
            continue
        print(f"   {label}...", end=" ", flush=True)
        results = measure_verbs(path)
        all_verb_results[label] = results
        n_passed = sum(1 for r in results.values() if r["exit"] == 0)
        max_tok  = max((r["tokens"] for r in results.values()), default=0)
        print(f"{n_passed}/{len(results)} ran clean, max stdout = {max_tok:,} tokens")

    print("\n[4/4] Computing session profiles...")
    sessions = compute_sessions(static_data, all_verb_results)

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "methodology": (
            "Token counts via tiktoken cl100k_base. cl100k_base is GPT-4's "
            "BPE tokenizer; Claude's tokenizer is also BPE with similar vocabulary "
            "scale, so counts are within ~5–10% of what Claude actually sees."
        ),
        "static": static_data,
        "projects": project_data,
        "verbs": all_verb_results,
        "sessions": sessions,
    }
    out_path = Path(args.out)
    out_path.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print(f"\n✓ Wrote {out_path}")
    print(f"  Total verb runs: {sum(len(v) for v in all_verb_results.values())}")
    print(f"  Next: python {HERE / 'generate_html.py'}")

if __name__ == "__main__":
    main()
