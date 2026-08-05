# POCKET v1.0 Product Runtime — double-click and leave running
# Starts Python watchdog + ensures NEXUS is on PYTHONPATH

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Src = Join-Path $Root "src"
$Nexus = "C:\Users\Medin\OneDrive\nexus"
$py = "C:\Users\Medin\AppData\Local\Programs\Python\Python311-arm64\python.exe"
if (-not (Test-Path $py)) {
  $c = Get-Command python -ErrorAction SilentlyContinue
  if ($c) { $py = $c.Source } else { throw "Python not found" }
}

$env:PYTHONPATH = ($Src + [IO.Path]::PathSeparator + $Nexus + [IO.Path]::PathSeparator + ($env:PYTHONPATH))
$env:NEXUS_ROOT = $Nexus
$env:POCKET_PUBLIC_URL = "https://pocket.medinatechlabs.net"
$env:Path = "C:\Users\Medin\.grok\bin;" + $env:Path

# Load secrets
foreach ($f in @(
  (Join-Path $env:USERPROFILE ".pocket\access.env"),
  (Join-Path $Root ".pocket\access.env")
)) {
  if (Test-Path $f) {
    Get-Content $f | ForEach-Object {
      if ($_ -match '^\s*([A-Z0-9_]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1])" -Value $matches[2].Trim()
      }
    }
  }
}

# Load nexus .env if present
$nxEnv = Join-Path $Nexus ".env"
if (Test-Path $nxEnv) {
  Get-Content $nxEnv | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or $line.IndexOf("=") -lt 1) { return }
    $i = $line.IndexOf("=")
    $k = $line.Substring(0, $i).Trim()
    $v = $line.Substring($i + 1).Trim()
    if (-not [string]::IsNullOrEmpty($k) -and -not (Test-Path "env:$k")) {
      Set-Item -Path "env:$k" -Value $v
    }
  }
}

Set-Location $Root
# Always ensure host is reachable (restart-safe)
$ensure = Join-Path $Root "scripts\Ensure-POCKET-Up.ps1"
if (Test-Path $ensure) {
  try { & $ensure | Out-Host } catch { Write-Host "Ensure-POCKET-Up: $_" }
}
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " POCKET Product Runtime (always-on ready)"
Write-Host " Python:  $py"
Write-Host " Local:   http://127.0.0.1:8787/"
Write-Host " Public:  https://pocket.medinatechlabs.net/"
Write-Host " Desk:    http://127.0.0.1:8787/desk"
Write-Host " Forge:   http://127.0.0.1:8787/forge"
Write-Host " Auro:    http://127.0.0.1:8787/auro/"
Write-Host " GitHub:  https://github.com/FreddyCreates/pocket"
Write-Host " NEXUS:   $Nexus"
Write-Host " Pass:    $env:USERPROFILE\.pocket\ACCESS.txt"
Write-Host " Watchdog: scripts\Start-POCKET-AlwaysOn.ps1"
Write-Host " Leave runtime open or rely on always-on task."
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Doctor first
& $py -u -m pocket doctor
Write-Host ""
& $py -u -m pocket runtime
