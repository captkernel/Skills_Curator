# install.ps1 — Skills Curator v4 (Windows)
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$Version   = "4.0.0"
$SkillDir  = "$env:USERPROFILE\.claude\skills\skills-curator"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Src       = Join-Path $ScriptDir "skills\skills-curator"

Write-Host ""
Write-Host "Skills Curator v$Version" -ForegroundColor Cyan
Write-Host "  Source : $Src" -ForegroundColor Gray
Write-Host "  Target : $SkillDir" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $Src)) {
  Write-Host "Source skill folder not found at $Src" -ForegroundColor Red
  Write-Host "Run install.ps1 from inside the cloned Skills_Curator repo." -ForegroundColor Red
  exit 1
}

# Python 3.10+ check
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  Write-Host "python not found in PATH. Install Python 3.10 or newer." -ForegroundColor Red
  exit 1
}
$pyOk = python -c "import sys; print('yes' if sys.version_info >= (3,10) else 'no')"
if ($pyOk.Trim() -ne "yes") {
  $pyVer = python -c "import sys; print('%d.%d' % sys.version_info[:2])"
  Write-Host "Python $($pyVer.Trim()) detected. Skills Curator requires 3.10+." -ForegroundColor Red
  exit 1
}

$CmdDir = "$env:USERPROFILE\.claude\commands"

New-Item -ItemType Directory -Force -Path "$SkillDir\references" | Out-Null
New-Item -ItemType Directory -Force -Path "$SkillDir\scripts"    | Out-Null
New-Item -ItemType Directory -Force -Path $CmdDir                | Out-Null

Copy-Item "$Src\SKILL.md"                    "$SkillDir\SKILL.md"                  -Force
Copy-Item "$Src\scripts\registry.py"         "$SkillDir\scripts\registry.py"       -Force
Copy-Item "$Src\references\commands.md"      "$SkillDir\references\commands.md"    -Force
Copy-Item "$Src\references\evaluation.md"    "$SkillDir\references\evaluation.md"  -Force
Copy-Item "$Src\references\discovery.md"     "$SkillDir\references\discovery.md"   -Force
Copy-Item "$Src\references\schema.md"        "$SkillDir\references\schema.md"      -Force

# Slash commands
$CmdSrc = Join-Path $ScriptDir ".claude\commands"
if (Test-Path $CmdSrc) {
  Copy-Item "$CmdSrc\skill-evaluate.md"  "$CmdDir\skill-evaluate.md"  -Force
  Copy-Item "$CmdSrc\skill-recommend.md" "$CmdDir\skill-recommend.md" -Force
  Copy-Item "$CmdSrc\skill-audit.md"     "$CmdDir\skill-audit.md"     -Force
}

Write-Host "Files installed" -ForegroundColor Green
Write-Host ""
Write-Host "Initialising registry..." -ForegroundColor Cyan
python "$SkillDir\scripts\registry.py"

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host ""
Write-Host "  Claude Code : restart any Claude Code session - skill auto-loads"
Write-Host "  claude.ai   : Settings -> Skills -> upload $SkillDir\SKILL.md"
Write-Host "  Gist sync   : see docs\gist-sync.md"
Write-Host ""
Write-Host "  Quick commands:"
Write-Host "    python $SkillDir\scripts\registry.py --list"
Write-Host "    python $SkillDir\scripts\registry.py --recommend"
Write-Host "    python $SkillDir\scripts\registry.py --discover react"
Write-Host "    python $SkillDir\scripts\registry.py --validate"
Write-Host ""
