# Permanent-ish POCKET without Administrator rights
# 1) Starts keep-alive now  2) Adds Startup-folder shortcut (no scheduled task)

$ErrorActionPreference = "Continue"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Alive = Join-Path $PSScriptRoot "Start-POCKET-Alive.ps1"
$Startup = [Environment]::GetFolderPath("Startup")
$cmdPath = Join-Path $Startup "POCKET-MultiAgent.cmd"

# Firewall best-effort (may need admin — ignore fail)
try {
  if (-not (Get-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName "ITSNOTAI-POCKET-8787" -Direction Inbound -Protocol TCP -LocalPort 8787 -Action Allow -Profile Private -ErrorAction SilentlyContinue | Out-Null
  }
} catch {}

# Startup entry — runs at user logon without admin
$cmd = @"
@echo off
cd /d "$Root"
set PYTHONPATH=$Root\src
start "POCKET" /min powershell -NoProfile -ExecutionPolicy Bypass -File "$Alive"
"@
Set-Content -Path $cmdPath -Value $cmd -Encoding ASCII
Write-Host "Startup entry written: $cmdPath"
Write-Host "POCKET will start minimized when you log in (no admin needed)."
Write-Host ""
Write-Host "Starting keep-alive NOW..."
Write-Host "Desktop: http://127.0.0.1:8787/"
Write-Host "Leave the POCKET window running (or minimized)."
Write-Host ""

# Free port then start
Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep 1
& $Alive
