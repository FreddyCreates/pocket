# POCKET Desktop — production. Does NOT call npm/npm.ps1/codex.ps1.
$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ElectronDir = Join-Path $Root "desktop-electron"
$Port = 8787

function Port-Up([int]$P) {
  try { return [bool](Get-NetTCPConnection -LocalPort $P -State Listen -EA SilentlyContinue) } catch { return $false }
}

Write-Host "POCKET Desktop" -ForegroundColor Cyan

if (-not (Port-Up $Port)) {
  $env:PYTHONPATH = Join-Path $Root "src"
  $py = "$env:LOCALAPPDATA\Programs\Python\Python311-arm64\python.exe"
  if (-not (Test-Path $py)) { $py = "python.exe" }
  Start-Process -FilePath $py -ArgumentList "-u","-m","pocket","serve","--host","127.0.0.1","--port","$Port" -WorkingDirectory $Root -WindowStyle Minimized
  1..40 | ForEach-Object { if (Port-Up $Port) { break }; Start-Sleep -Milliseconds 300 }
}

$env:POCKET_URL = "http://127.0.0.1:$Port/"
$env:POCKET_ROOT = $Root
Set-Location $ElectronDir

if (-not (Test-Path ".\node_modules\electron\package.json")) {
  Write-Host "Installing electron via cmd npm.cmd ..." -ForegroundColor Yellow
  cmd.exe /c "`"$env:ProgramFiles\nodejs\npm.cmd`" install --no-fund --no-audit"
}

# ONLY node.exe — never & npm
$node = (Get-Command node.exe -EA SilentlyContinue).Source
if (-not $node) { $node = "node.exe" }
Write-Host "node run-electron.js" -ForegroundColor Green
& $node ".\run-electron.js"
exit $LASTEXITCODE
