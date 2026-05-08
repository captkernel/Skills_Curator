#!/usr/bin/env bash
# install.sh — Skills Curator v4 (macOS / Linux)
# Usage: bash install.sh
set -euo pipefail

VERSION="4.0.0"
SKILL_DIR="$HOME/.claude/skills/skills-curator"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/skills/skills-curator"

echo ""
echo "🔧 Skills Curator v$VERSION"
echo "   Source : $SRC"
echo "   Target : $SKILL_DIR"
echo ""

if [ ! -d "$SRC" ]; then
  echo "❌ Source skill folder not found at $SRC"
  echo "   Run install.sh from inside the cloned Skills_Curator repo."
  exit 1
fi

# Python 3.10+ check
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 not found in PATH. Install Python 3.10 or newer."
  exit 1
fi
PY_OK=$(python3 -c 'import sys; print("yes" if sys.version_info >= (3,10) else "no")')
if [ "$PY_OK" != "yes" ]; then
  PY_VER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  echo "❌ Python $PY_VER detected. Skills Curator requires 3.10+."
  exit 1
fi

CMD_DIR="$HOME/.claude/commands"

mkdir -p "$SKILL_DIR/references" "$SKILL_DIR/scripts" "$CMD_DIR"

cp "$SRC/SKILL.md"                       "$SKILL_DIR/SKILL.md"
cp "$SRC/scripts/registry.py"            "$SKILL_DIR/scripts/registry.py"
cp "$SRC/references/commands.md"         "$SKILL_DIR/references/commands.md"
cp "$SRC/references/evaluation.md"       "$SKILL_DIR/references/evaluation.md"
cp "$SRC/references/discovery.md"        "$SKILL_DIR/references/discovery.md"
cp "$SRC/references/schema.md"           "$SKILL_DIR/references/schema.md"

# Slash commands — copy from the repo's .claude/commands/ if present
if [ -d "$SCRIPT_DIR/.claude/commands" ]; then
  cp "$SCRIPT_DIR/.claude/commands/skill-evaluate.md"  "$CMD_DIR/skill-evaluate.md"
  cp "$SCRIPT_DIR/.claude/commands/skill-recommend.md" "$CMD_DIR/skill-recommend.md"
  cp "$SCRIPT_DIR/.claude/commands/skill-audit.md"     "$CMD_DIR/skill-audit.md"
fi

chmod +x "$SKILL_DIR/scripts/registry.py"

echo "📦 Initialising registry..."
python3 "$SKILL_DIR/scripts/registry.py"

echo ""
echo "✅ Installed."
echo ""
echo "  Claude Code  : restart any Claude Code session — skill auto-loads"
echo "  claude.ai    : Settings → Skills → upload $SKILL_DIR/SKILL.md"
echo "  Gist sync    : see docs/gist-sync.md"
echo ""
echo "  Quick commands:"
echo "    python3 $SKILL_DIR/scripts/registry.py --list"
echo "    python3 $SKILL_DIR/scripts/registry.py --recommend"
echo "    python3 $SKILL_DIR/scripts/registry.py --discover react"
echo "    python3 $SKILL_DIR/scripts/registry.py --validate"
echo ""
