# install.ps1 — Skills Curator v4.4 (Windows)
# Installs the Lite skill (no Python) by default, plus the full Python
# version if Python 3.10+ is available on the system.
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1 [-Tier lite-only|with-python|auto]
param([string]$Tier = "auto")

$ErrorActionPreference = "Stop"

$Version       = "4.4.0"
$SkillLiteDir  = "$env:USERPROFILE\.claude\skills\skills-curator-lite"
$SkillFullDir  = "$env:USERPROFILE\.claude\skills\skills-curator"
$CmdDir        = "$env:USERPROFILE\.claude\commands"
$ScriptDir     = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SrcLite       = Join-Path $ScriptDir "skills\skills-curator-lite"
$SrcFull       = Join-Path $ScriptDir "skills\skills-curator"

if ($Tier -notin @("lite-only", "with-python", "auto")) {
  Write-Host "Unknown -Tier '$Tier' (allowed: lite-only, with-python, auto)" -ForegroundColor Red
  exit 2
}

Write-Host ""
Write-Host "Skills Curator v$Version" -ForegroundColor Cyan
Write-Host "  Mode   : $Tier" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $SrcLite)) {
  Write-Host "Source skill folder not found at $SrcLite" -ForegroundColor Red
  Write-Host "Run install.ps1 from inside the cloned Skills_Curator repo." -ForegroundColor Red
  exit 1
}

# ─── Always install Lite ─────────────────────────────────────────────────────
Write-Host "Installing skills-curator-lite (Python-free, default tier)..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $SkillLiteDir | Out-Null
Copy-Item "$SrcLite\SKILL.md" "$SkillLiteDir\SKILL.md" -Force
Write-Host "   -> $SkillLiteDir\SKILL.md"

if (-not (Test-Path "$SkillLiteDir\registry.json")) {
  '{"version":"3.0","last_updated":"","skills":[]}' | Out-File -Encoding utf8 "$SkillLiteDir\registry.json"
}
if (-not (Test-Path "$SkillLiteDir\auto_state.json")) {
  '{}' | Out-File -Encoding utf8 "$SkillLiteDir\auto_state.json"
}

# Slash commands
New-Item -ItemType Directory -Force -Path $CmdDir | Out-Null
$CmdSrc = Join-Path $ScriptDir ".claude\commands"
if (Test-Path $CmdSrc) {
  Copy-Item "$CmdSrc\skill-evaluate.md"  "$CmdDir\skill-evaluate.md"  -Force
  Copy-Item "$CmdSrc\skill-recommend.md" "$CmdDir\skill-recommend.md" -Force
  Copy-Item "$CmdSrc\skill-audit.md"     "$CmdDir\skill-audit.md"     -Force
  Write-Host "   -> slash commands installed to $CmdDir"
}

# ─── Optionally install Python full version ──────────────────────────────────
$InstallPython = "no"
switch ($Tier) {
  "with-python" { $InstallPython = "forced" }
  "lite-only"   { $InstallPython = "no" }
  "auto" {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
      $pyOk = python -c "import sys; print('yes' if sys.version_info >= (3,10) else 'no')"
      if ($pyOk.Trim() -eq "yes") { $InstallPython = "auto" }
    }
  }
}

if ($InstallPython -ne "no") {
  if ($InstallPython -eq "forced") {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
      Write-Host "-Tier with-python requested but python not found in PATH." -ForegroundColor Red
      exit 1
    }
    $pyOk = python -c "import sys; print('yes' if sys.version_info >= (3,10) else 'no')"
    if ($pyOk.Trim() -ne "yes") {
      $pyVer = python -c "import sys; print('%d.%d' % sys.version_info[:2])"
      Write-Host "Python $($pyVer.Trim()) detected (3.10+ required)." -ForegroundColor Red
      exit 1
    }
  }

  Write-Host ""
  Write-Host "Installing skills-curator (full Python, performance tier)..." -ForegroundColor Cyan
  New-Item -ItemType Directory -Force -Path "$SkillFullDir\references" | Out-Null
  New-Item -ItemType Directory -Force -Path "$SkillFullDir\scripts"    | Out-Null
  Copy-Item "$SrcFull\SKILL.md"                    "$SkillFullDir\SKILL.md"                  -Force
  Copy-Item "$SrcFull\scripts\registry.py"         "$SkillFullDir\scripts\registry.py"       -Force
  Copy-Item "$SrcFull\references\commands.md"      "$SkillFullDir\references\commands.md"    -Force
  Copy-Item "$SrcFull\references\evaluation.md"    "$SkillFullDir\references\evaluation.md"  -Force
  Copy-Item "$SrcFull\references\discovery.md"     "$SkillFullDir\references\discovery.md"   -Force
  Copy-Item "$SrcFull\references\schema.md"        "$SkillFullDir\references\schema.md"      -Force
  Write-Host "   -> $SkillFullDir"

  Write-Host ""
  Write-Host "Initialising Python registry..." -ForegroundColor Cyan
  python "$SkillFullDir\scripts\registry.py"
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
if ($InstallPython -eq "no") {
  Write-Host "  Tier installed : Lite (no Python)"
  Write-Host "  Note: Python 3.10+ is not on PATH - install it and re-run with"
  Write-Host "        '-Tier with-python' to add the performance-tier engine."
} else {
  Write-Host "  Tiers installed: Lite + Python full"
  Write-Host "  Lite is the default - agent uses it unless you invoke the Python verbs."
}
Write-Host ""
Write-Host "  Restart Claude Code to load both skills + slash commands."
Write-Host ""
