# Local copy: delegates to repo scripts/Start-POCKET-Electron.ps1
# Usage (from desktop-electron): .\scripts\Start-POCKET-Electron.ps1
#
# Never opens .ps1 via notepad / shell association.

$ErrorActionPreference = "Stop"
$RepoScript = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")) "scripts\Start-POCKET-Electron.ps1"

if (-not (Test-Path -LiteralPath $RepoScript)) {
  Write-Host "ERROR: repo launcher not found: $RepoScript" -ForegroundColor Red
  exit 1
}

# Invoke in-process with call operator — NOT Start-Process on the .ps1 path
# (Start-Process file.ps1 can open Notepad with the script source).
& $RepoScript @args
exit $LASTEXITCODE
