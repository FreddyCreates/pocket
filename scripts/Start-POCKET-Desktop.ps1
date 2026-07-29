# POCKET Desktop — tray + desk window + local runtime
# Prefer installed launcher; else run module.

$ErrorActionPreference = "Continue"
$Root = "C:\Users\Medin\OneDrive\pocket-os"
if (-not (Test-Path "$Root\src\pocket")) { $Root = Split-Path $PSScriptRoot -Parent }

$Launcher = Join-Path $Root "scripts\POCKET-Desktop-Launch.cmd"
if (Test-Path $Launcher) {
  Start-Process -FilePath $Launcher
  exit 0
}

$env:PYTHONPATH = "$Root\src"
if (Test-Path "C:\Users\Medin\OneDrive\nexus") {
  $env:PYTHONPATH = "C:\Users\Medin\OneDrive\nexus;$env:PYTHONPATH"
  $env:NEXUS_ROOT = "C:\Users\Medin\OneDrive\nexus"
}
$py = "$env:LOCALAPPDATA\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
Write-Host "POCKET Desktop (tray + host runtime)" -ForegroundColor Cyan
Set-Location $Root
Start-Process -FilePath $py -ArgumentList "-m","pocket","desktop" -WorkingDirectory $Root
exit 0
