# Build POCKET Electron Windows packages and publish to /download
# Usage (from pocket-os root):
#   .\scripts\Build-POCKET-Desktop-Exe.ps1
#   .\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch arm64
#   .\scripts\Build-POCKET-Desktop-Exe.ps1 -Arch x64

param(
  [ValidateSet("arm64", "x64", "both")]
  [string]$Arch = "arm64",
  [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ElectronDir = Join-Path $Root "desktop-electron"
$npm = Join-Path $env:ProgramFiles "nodejs\npm.cmd"
if (-not (Test-Path $npm)) { $npm = "npm.cmd" }

Write-Host "POCKET Desktop package build" -ForegroundColor Cyan
Write-Host "  Root: $Root"
Write-Host "  Arch: $Arch"

Set-Location $ElectronDir

if (-not $SkipInstall) {
  if (-not (Test-Path ".\node_modules\electron-builder\package.json")) {
    Write-Host "npm.cmd install (electron + electron-builder)..." -ForegroundColor Yellow
    & cmd.exe /c "`"$npm`" install --no-fund --no-audit"
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
  }
}

function Invoke-Dist([string]$a) {
  Write-Host "electron-builder --win --$a ..." -ForegroundColor Green
  # Use npx via cmd to avoid npm.ps1 Notepad issues
  & cmd.exe /c "`"$npm`" exec -- electron-builder --win portable nsis --$a"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "full target failed; trying portable only..." -ForegroundColor Yellow
    & cmd.exe /c "`"$npm`" exec -- electron-builder --win portable --$a"
    if ($LASTEXITCODE -ne 0) { throw "electron-builder failed for $a" }
  }
}

if ($Arch -eq "both") {
  Invoke-Dist "arm64"
  Invoke-Dist "x64"
} else {
  Invoke-Dist $Arch
}

$env:PYTHONPATH = Join-Path $Root "src"
$py = "$env:LOCALAPPDATA\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) {
  $py = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
}
if (-not (Test-Path $py)) { $py = "python.exe" }

Write-Host "Publishing to releases/desktop (web /download)..." -ForegroundColor Cyan
& $py -m pocket desktop-pack
if ($LASTEXITCODE -ne 0) { throw "desktop-pack failed" }

Write-Host ""
Write-Host "Done. Download from:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:8787/download"
Write-Host "  http://127.0.0.1:8787/download/desktop"
Write-Host "  https://pocket.medinatechlabs.net/download  (when tunnel is up)"
