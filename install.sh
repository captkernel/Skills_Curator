#!/usr/bin/env bash
# install.sh — Skills Curator v4.4 (macOS / Linux)
# Installs the Lite skill (no Python) by default, plus the full Python
# version if Python 3.10+ is available on the system.
# Usage: bash install.sh [--lite-only|--with-python]
set -euo pipefail

VERSION="4.4.0"
SKILL_LITE_DIR="$HOME/.claude/skills/skills-curator-lite"
SKILL_FULL_DIR="$HOME/.claude/skills/skills-curator"
CMD_DIR="$HOME/.claude/commands"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_LITE="$SCRIPT_DIR/skills/skills-curator-lite"
SRC_FULL="$SCRIPT_DIR/skills/skills-curator"

# Decide which tier the user wants. Default: install Lite, plus Python if available.
TIER="auto"
case "${1:-}" in
  --lite-only)   TIER="lite-only" ;;
  --with-python) TIER="with-python" ;;
  "")            TIER="auto" ;;
  *)             echo "Unknown flag: $1 (allowed: --lite-only, --with-python)"; exit 2 ;;
esac

echo ""
echo "🔧 Skills Curator v$VERSION"
echo "   Mode   : $TIER"
echo ""

if [ ! -d "$SRC_LITE" ]; then
  echo "❌ Source skill folder not found at $SRC_LITE"
  echo "   Run install.sh from inside the cloned Skills_Curator repo."
  exit 1
fi

# ─── Always install Lite ─────────────────────────────────────────────────────
echo "📦 Installing skills-curator-lite (Python-free, default tier)..."
mkdir -p "$SKILL_LITE_DIR"
cp "$SRC_LITE/SKILL.md" "$SKILL_LITE_DIR/SKILL.md"
echo "   → $SKILL_LITE_DIR/SKILL.md"

# Initialize Lite registry (markdown skill writes JSON via the agent)
[ -f "$SKILL_LITE_DIR/registry.json" ] || \
  echo '{"version":"3.0","last_updated":"","skills":[]}' > "$SKILL_LITE_DIR/registry.json"
[ -f "$SKILL_LITE_DIR/auto_state.json" ] || \
  echo '{}' > "$SKILL_LITE_DIR/auto_state.json"

# Slash commands (work for both versions)
mkdir -p "$CMD_DIR"
if [ -d "$SCRIPT_DIR/.claude/commands" ]; then
  cp "$SCRIPT_DIR/.claude/commands/skill-evaluate.md"  "$CMD_DIR/skill-evaluate.md"
  cp "$SCRIPT_DIR/.claude/commands/skill-recommend.md" "$CMD_DIR/skill-recommend.md"
  cp "$SCRIPT_DIR/.claude/commands/skill-audit.md"     "$CMD_DIR/skill-audit.md"
  echo "   → slash commands installed to $CMD_DIR"
fi

# ─── Optionally install Python full version ──────────────────────────────────
INSTALL_PYTHON="no"
case "$TIER" in
  with-python) INSTALL_PYTHON="forced" ;;
  lite-only)   INSTALL_PYTHON="no" ;;
  auto)
    if command -v python3 >/dev/null 2>&1; then
      PY_OK=$(python3 -c 'import sys; print("yes" if sys.version_info >= (3,10) else "no")')
      [ "$PY_OK" = "yes" ] && INSTALL_PYTHON="auto"
    fi
    ;;
esac

if [ "$INSTALL_PYTHON" != "no" ]; then
  if [ "$INSTALL_PYTHON" = "forced" ]; then
    if ! command -v python3 >/dev/null 2>&1; then
      echo "❌ --with-python requested but python3 not found in PATH."
      exit 1
    fi
    PY_OK=$(python3 -c 'import sys; print("yes" if sys.version_info >= (3,10) else "no")')
    if [ "$PY_OK" != "yes" ]; then
      PY_VER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
      echo "❌ --with-python requested but Python $PY_VER detected (3.10+ required)."
      exit 1
    fi
  fi
  echo ""
  echo "📦 Installing skills-curator (full Python, performance tier)..."
  mkdir -p "$SKILL_FULL_DIR/references" "$SKILL_FULL_DIR/scripts"
  cp "$SRC_FULL/SKILL.md"                  "$SKILL_FULL_DIR/SKILL.md"
  cp "$SRC_FULL/scripts/registry.py"       "$SKILL_FULL_DIR/scripts/registry.py"
  cp "$SRC_FULL/references/commands.md"    "$SKILL_FULL_DIR/references/commands.md"
  cp "$SRC_FULL/references/evaluation.md"  "$SKILL_FULL_DIR/references/evaluation.md"
  cp "$SRC_FULL/references/discovery.md"   "$SKILL_FULL_DIR/references/discovery.md"
  cp "$SRC_FULL/references/schema.md"      "$SKILL_FULL_DIR/references/schema.md"
  chmod +x "$SKILL_FULL_DIR/scripts/registry.py"
  echo "   → $SKILL_FULL_DIR"
  echo ""
  echo "📋 Initialising Python registry..."
  python3 "$SKILL_FULL_DIR/scripts/registry.py"
fi

echo ""
echo "✅ Installed."
echo ""
case "$TIER:$INSTALL_PYTHON" in
  *:no)
    echo "  Tier installed : Lite (no Python)"
    echo "  Note: Python 3.10+ is not on PATH — install it and re-run with"
    echo "        '--with-python' to add the performance-tier engine."
    ;;
  with-python:*|*:auto|*:forced)
    echo "  Tiers installed: Lite + Python full"
    echo "  Lite is the default — agent uses it unless you explicitly invoke the Python verbs."
    ;;
esac
echo ""
echo "  Restart Claude Code to load both skills + slash commands."
echo ""
